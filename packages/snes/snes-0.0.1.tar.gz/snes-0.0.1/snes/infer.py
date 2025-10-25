from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from .data.preprocess import split_paragraphs
from .models.segmenter import ModernBERTSegmenter, get_tokenizer
from .utils.logging import get_logger


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Infer scene/segment boundaries from text")
    p.add_argument("text_file", help="Path to input text file")
    p.add_argument("--model", default="./snes_model", help="Path to saved model dir")
    p.add_argument("--threshold", type=float, default=0.5)
    p.add_argument("--max_length", type=int, default=8192)
    p.add_argument("--output", default="scene_breaks.json")
    return p.parse_args()


@torch.no_grad()
def main():
    args = parse_args()
    logger = get_logger()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load text and split into paragraphs
    text = Path(args.text_file).read_text(encoding="utf-8")
    paragraphs = split_paragraphs(text)

    # Load model + tokenizer
    model = ModernBERTSegmenter.load(args.model).to(device)
    tokenizer = get_tokenizer(model.model_name)

    # Predict per paragraph
    preds = []
    for p in paragraphs:
        enc = tokenizer(
            p,
            truncation=True,
            max_length=args.max_length,
            padding="max_length",
            return_tensors="pt",
        )
        input_ids = enc["input_ids"].to(device)
        attention_mask = enc["attention_mask"].to(device)
        prob = model.predict_proba(input_ids=input_ids, attention_mask=attention_mask).item()
        preds.append(prob)

    boundaries = [i for i, prob in enumerate(preds) if prob >= args.threshold]
    out = {
        "num_paragraphs": len(paragraphs),
        "threshold": args.threshold,
        "boundary_indices": boundaries,
    }
    Path(args.output).write_text(json.dumps(out, indent=2), encoding="utf-8")
    logger.info(f"Wrote boundaries to {args.output}")


if __name__ == "__main__":
    main()

