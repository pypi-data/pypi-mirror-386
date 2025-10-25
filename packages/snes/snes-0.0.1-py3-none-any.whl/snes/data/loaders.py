from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from ..utils.io import read_jsonl


def load_jsonl_dataset(path: str | Path) -> List[Dict[str, Any]]:
    return read_jsonl(path)


def paragraphs_to_examples(records: List[Dict[str, Any]]) -> Tuple[List[str], List[int]]:
    texts: List[str] = []
    labels: List[int] = []
    for rec in records:
        ps = rec.get("paragraphs", [])
        ls = rec.get("labels", [0] * len(ps))
        for p, l in zip(ps, ls):
            texts.append(p)
            labels.append(int(l))
    return texts, labels

