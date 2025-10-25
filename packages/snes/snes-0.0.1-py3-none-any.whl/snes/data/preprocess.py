from __future__ import annotations

from typing import Dict, List, Optional


def split_paragraphs(text: str) -> List[str]:
    # Split on blank lines; strip whitespace
    parts = [p.strip() for p in text.replace("\r\n", "\n").split("\n\n")]
    return [p for p in parts if p]


def build_record_from_text(story_id: str, text: str, labels: Optional[List[int]] = None,
                           soft_labels: Optional[List[float]] = None,
                           meta: Optional[Dict] = None) -> Dict:
    paragraphs = split_paragraphs(text)
    rec = {
        "story_id": story_id,
        "paragraphs": paragraphs,
    }
    if labels is not None:
        rec["labels"] = labels
    if soft_labels is not None:
        rec["soft_labels"] = soft_labels
    if meta is not None:
        rec["meta"] = meta
    return rec

