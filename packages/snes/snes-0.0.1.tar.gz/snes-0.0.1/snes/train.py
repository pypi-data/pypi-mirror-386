from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import torch
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from torch.nn.functional import binary_cross_entropy_with_logits
from tqdm import tqdm

from .models.segmenter import ModernBERTSegmenter, get_tokenizer
from .models.metrics import boundary_f1
from .data.loaders import load_jsonl_dataset, paragraphs_to_examples
from .utils.logging import get_logger
from .utils.seed import set_seed


class TextDataset(Dataset):
    def __init__(self, texts: List[str], labels: List[int], tokenizer, max_length: int = 8192):
        self.texts = texts
        self.labels = labels
        self.tok = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> Dict:
        t = self.texts[idx]
        y = self.labels[idx]
        enc = self.tok(
            t,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )
        item = {k: v.squeeze(0) for k, v in enc.items()}
        item["labels"] = torch.tensor(y, dtype=torch.float)
        return item


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train SNES segmenter")
    p.add_argument("--train_file", required=True)
    p.add_argument("--val_file", required=True)
    p.add_argument("--model_name", default="answerdotai/ModernBERT-base")
    p.add_argument("--output_dir", default="./snes_model")
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--lr", type=float, default=2e-5)
    p.add_argument("--batch_size", type=int, default=1)
    p.add_argument("--max_length", type=int, default=8192)
    p.add_argument("--grad_accum", type=int, default=8)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def train_one_epoch(model, loader, optimizer, device):
    model.train()
    total_loss = 0.0
    for batch in loader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)
        logits = model(input_ids=input_ids, attention_mask=attention_mask)
        loss = binary_cross_entropy_with_logits(logits, labels)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / max(1, len(loader))


@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    preds = []
    labels = []
    for batch in loader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        y = batch["labels"].cpu().numpy().tolist()
        proba = model.predict_proba(input_ids=input_ids, attention_mask=attention_mask).cpu().numpy().tolist()
        preds.extend(proba)
        labels.extend(y)
    return boundary_f1(preds, labels, threshold=0.5)


def main():
    args = parse_args()
    logger = get_logger()
    set_seed(args.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # Load data
    train_records = load_jsonl_dataset(args.train_file)
    val_records = load_jsonl_dataset(args.val_file)
    train_texts, train_labels = paragraphs_to_examples(train_records)
    val_texts, val_labels = paragraphs_to_examples(val_records)

    tokenizer = get_tokenizer(args.model_name)
    train_ds = TextDataset(train_texts, train_labels, tokenizer, args.max_length)
    val_ds = TextDataset(val_texts, val_labels, tokenizer, args.max_length)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)

    model = ModernBERTSegmenter(args.model_name).to(device)
    optimizer = AdamW(model.parameters(), lr=args.lr)

    best_f1 = -1.0
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        loss = train_one_epoch(model, train_loader, optimizer, device)
        metrics = evaluate(model, val_loader, device)
        logger.info(f"Epoch {epoch}: loss={loss:.4f} f1={metrics['f1']:.4f} p={metrics['precision']:.4f} r={metrics['recall']:.4f}")
        if metrics["f1"] > best_f1:
            best_f1 = metrics["f1"]
            logger.info("New best model; saving...")
            model.save(output_dir)
            with (output_dir / "training_metrics.json").open("w") as f:
                json.dump({"best_f1": best_f1, "epoch": epoch}, f)

    logger.info(f"Training complete. Best F1: {best_f1:.4f}. Model saved to {output_dir}.")


if __name__ == "__main__":
    main()

