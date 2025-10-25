from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import torch
from torch import nn

try:
    from transformers import AutoModel, AutoTokenizer
except Exception as e:  # pragma: no cover
    AutoModel = None  # type: ignore
    AutoTokenizer = None  # type: ignore


class ModernBERTSegmenter(nn.Module):
    def __init__(self, model_name: str = "answerdotai/ModernBERT-base"):
        super().__init__()
        if AutoModel is None:
            raise ImportError("transformers is required to use ModernBERTSegmenter")
        self.encoder = AutoModel.from_pretrained(model_name)
        self.classifier = nn.Linear(self.encoder.config.hidden_size, 1)
        self.model_name = model_name

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        # CLS token representation
        cls = outputs.last_hidden_state[:, 0, :]
        logits = self.classifier(cls)
        return logits.squeeze(-1)

    @torch.no_grad()
    def predict_proba(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        self.eval()
        logits = self.forward(input_ids, attention_mask)
        return torch.sigmoid(logits)

    def save(self, output_dir: str | Path) -> None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        torch.save(self.state_dict(), output_dir / "model.pt")
        with (output_dir / "config.json").open("w") as f:
            json.dump({"model_name": self.model_name}, f)

    @classmethod
    def load(cls, model_dir: str | Path) -> "ModernBERTSegmenter":
        model_dir = Path(model_dir)
        with (model_dir / "config.json").open("r") as f:
            cfg = json.load(f)
        model = cls(model_name=cfg["model_name"])
        state = torch.load(model_dir / "model.pt", map_location="cpu")
        model.load_state_dict(state)
        return model


def get_tokenizer(model_name: str):
    if AutoTokenizer is None:  # pragma: no cover
        raise ImportError("transformers is required to get tokenizer")
    return AutoTokenizer.from_pretrained(model_name, use_fast=True)

