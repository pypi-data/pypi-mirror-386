# SNES — Simple Narrative Edge Segmenter

ModernBERT-based scene/chapter boundary detector for narrative text.

SNES predicts paragraph-level transitions (edges) in long-form documents using an encoder with 8k token context.

## Install

```
pip install -e .
```

Requires Python 3.10+ and the dependencies listed in `pyproject.toml`.

## Quick Start

Train:

```
snes-train --train_file data/train.jsonl --val_file data/val.jsonl \
           --model_name answerdotai/ModernBERT-base \
           --output_dir ./snes_model \
           --epochs 3 --lr 2e-5 --batch_size 1 \
           --max_length 8192
```

Evaluate:

```
snes-eval --model ./snes_model --data data/test.jsonl
```

Infer:

```
snes-infer story.txt --threshold 0.35 --output scene_breaks.json
```

## Data Format (.jsonl)

Each record is one story pre-split into paragraphs:

```
{"story_id": "uuid-1234", "paragraphs": ["Para 1", "Para 2"], "labels": [0, 1]}
```

Optional keys: `soft_labels`, `meta`.

## License

MIT

