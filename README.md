# 1st_half

First-half tactical play templates for football (soccer) coaching and evaluation.

Each YAML file defines a named attacking pattern with player/ball trajectories over time (field depth vs seconds), plus evaluation checkpoints used for scoring. Use `plot.py` to visualize any play as an x–t diagram.

## Plays

| File | Play | Summary |
|------|------|---------|
| `001.yaml` | 邊路經典爆破 | Fullback overlap → cross → finish |
| `002.yaml` | 肋部切割器 | Winger through-ball to cutting AM → shot |
| `003.yaml` | 大範圍撕裂與倒三角 | Switch of play → cutback → finish |
| `004.yaml` | 中路三人過度 | DM → ST layoff → AM → second ST shot |
| `005.yaml` | 華麗的空間魔術 | Cutback → intentional miss → midfielder finish |
| `006.yaml` | 高空作業與做牆 | Long ball → wall pass → finish |
| `008.yaml` | 極限壓迫破解 | Press break via decoy run + overlap + cross |
| `009.yaml` | 誘敵深入與大逃亡 | Drop, layoff, diagonal switch over the top |

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Plot a play

```bash
python plot.py 001.yaml
```

Replace `001.yaml` with any play file. The chart shows each entity’s field depth (m) against time (s), including the ball and offside line when defined.

## YAML schema

```yaml
play_id: "T001"
title: "..."
description: "..."
evaluation_points:
  key: "checkpoint description"
y_label: "Field Depth (m)"
x_label: "Time (seconds)"
x_limits: [0.0, 4.2]
y_limits: [50, 100]
entities:
  - id: "ST"
    label: "Striker (ST)"
    color: "#4A85F6"
    linestyle: "-"
    trajectory:
      - [0.0, 80]   # [time_s, field_depth_m]
      - [4.0, 95]
```

## Requirements

- Python 3.10+
- `PyYAML`, `matplotlib`
