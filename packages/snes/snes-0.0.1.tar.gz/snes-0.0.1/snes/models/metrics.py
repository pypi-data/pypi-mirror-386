from __future__ import annotations

from typing import Iterable, List, Tuple

import numpy as np


def _to_arrays(preds: Iterable, labels: Iterable, threshold: float) -> Tuple[np.ndarray, np.ndarray]:
    p = np.array(list(preds), dtype=float)
    l = np.array(list(labels), dtype=int)
    if p.ndim > 1:
        p = p.squeeze()
    b = (p >= threshold).astype(int)
    return b, l.astype(int)


def boundary_f1(preds: Iterable, labels: Iterable, threshold: float = 0.5) -> dict:
    b, l = _to_arrays(preds, labels, threshold)
    tp = int(((b == 1) & (l == 1)).sum())
    fp = int(((b == 1) & (l == 0)).sum())
    fn = int(((b == 0) & (l == 1)).sum())
    precision = tp / (tp + fp + 1e-8)
    recall = tp / (tp + fn + 1e-8)
    f1 = 2 * precision * recall / (precision + recall + 1e-8)
    return {"precision": precision, "recall": recall, "f1": f1}


def _boundaries_to_segments(boundaries: np.ndarray) -> List[Tuple[int, int]]:
    # boundaries is 0/1 per position; segment breaks after positions with 1.
    n = len(boundaries)
    segs = []
    start = 0
    for i in range(n):
        if boundaries[i] == 1:
            segs.append((start, i + 1))
            start = i + 1
    segs.append((start, n))
    return segs


def pk_metric(preds: Iterable, labels: Iterable, window: int = 3, threshold: float = 0.5) -> float:
    # Simple Pk as proportion of disagreements whether two items are in same segment using window
    b_pred, b_true = _to_arrays(preds, labels, threshold)
    n = len(b_true)
    if n < 2:
        return 0.0
    k = window
    errors = 0
    total = 0
    # convert boundaries to cumulative segment ids
    seg_true = np.cumsum(b_true)
    seg_pred = np.cumsum(b_pred)
    for i in range(0, n - k):
        same_true = seg_true[i] == seg_true[i + k]
        same_pred = seg_pred[i] == seg_pred[i + k]
        errors += int(same_true != same_pred)
        total += 1
    return errors / (total + 1e-8)


def windowdiff_metric(preds: Iterable, labels: Iterable, window: int = 3, threshold: float = 0.5) -> float:
    # WindowDiff: difference in number of boundaries within window
    b_pred, b_true = _to_arrays(preds, labels, threshold)
    n = len(b_true)
    if n < 2:
        return 0.0
    k = window
    errors = 0
    total = 0
    c_true = np.cumsum(b_true)
    c_pred = np.cumsum(b_pred)
    for i in range(0, n - k):
        true_count = c_true[i + k] - c_true[i]
        pred_count = c_pred[i + k] - c_pred[i]
        errors += int(true_count != pred_count)
        total += 1
    return errors / (total + 1e-8)

