import numpy as np

from snes.models.metrics import boundary_f1, pk_metric, windowdiff_metric


def test_boundary_f1_simple():
    preds = [0.1, 0.9, 0.2, 0.8]
    labels = [0, 1, 0, 1]
    m = boundary_f1(preds, labels, threshold=0.5)
    assert 0.9 < m["precision"] <= 1.0
    assert 0.9 < m["recall"] <= 1.0
    assert 0.9 < m["f1"] <= 1.0


def test_pk_windowdiff_consistency():
    preds = [0, 0, 1, 0, 0, 1, 0]
    labels = [0, 0, 1, 0, 0, 1, 0]
    pk = pk_metric(preds, labels, window=2, threshold=0.5)
    wd = windowdiff_metric(preds, labels, window=2, threshold=0.5)
    assert pk < 1e-6
    assert wd < 1e-6

