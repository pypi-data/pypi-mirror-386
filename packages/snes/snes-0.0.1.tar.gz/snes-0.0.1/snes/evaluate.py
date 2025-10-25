from __future__ import annotations

import argparse
from pathlib import Path

import torch
from torch.utils.data import Dataset, DataLoader

from .models.segmenter import ModernBERTSegmenter, get_tokenizer
from .models.metrics import boundary_f1, pk_metric, windowdiff_metric
from .data.loaders import load_jsonl_dataset, paragraphs_to_examples
from .utils.logging import get_logger


class TextDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=8192):
        self.texts = texts
        self.labels = labels
        self.tok = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
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
    p = argparse.ArgumentParser(description="Evaluate a trained SNES model")
    p.add_argument("--model", required=True, help="Path to saved model dir")
    p.add_argument("--data", required=True, help="Path to jsonl dataset")
    p.add_argument("--max_length", type=int, default=8192)
    return p.parse_args()


@torch.no_grad()
def main():
    args = parse_args()
    logger = get_logger()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = ModernBERTSegmenter.load(args.model).to(device)
    tokenizer = get_tokenizer(model.model_name)

    records = load_jsonl_dataset(args.data)
    texts, labels = paragraphs_to_examples(records)
    ds = TextDataset(texts, labels, tokenizer, max_length=args.max_length)
    loader = DataLoader(ds, batch_size=8)

    all_preds = []
    all_labels = []
    for batch in loader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        probs = model.predict_proba(input_ids=input_ids, attention_mask=attention_mask).cpu().numpy().tolist()
        all_preds.extend(probs)
        all_labels.extend(batch["labels"].cpu().numpy().tolist())

    f1s = boundary_f1(all_preds, all_labels, threshold=0.5)
    pk = pk_metric(all_preds, all_labels, window=3, threshold=0.5)
    wd = windowdiff_metric(all_preds, all_labels, window=3, threshold=0.5)

    logger.info({"boundary": f1s, "pk": pk, "windowdiff": wd})


if __name__ == "__main__":
    main()

