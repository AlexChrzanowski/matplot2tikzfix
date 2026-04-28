# Failure failure_0007

## Summary

| Field | Value |
|-------|-------|
| Status | `visual_mismatch` |
| RMS | 67.3319 |
| SSIM | 0.653910 |
| Test ID | `test_0002` |
| Timestamp | 2026-04-28T14:23:59.138650+00:00 |
| Model | claude-3-5-haiku-20241022 |
| Seed | None |
| Transpiler | makintikz |
| Features | bar, categorical_ticks, rotated_labels, grid |

## Reproduction

```bash
cd failure_0007
python plot_script.py
# Then compile wrapper.tex with pdflatex and compare reference.png vs tikz_rendered.png
```

## Generated Matplotlib Script

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def create_figure():
    np.random.seed(7)
    categories = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"]
    values = np.array([14, 8, 20, 5, 17, 11])

    fig, ax = plt.subplots()
    bars = ax.bar(categories, values, color="steelblue", edgecolor="black")
    ax.set_xlabel("Category")
    ax.set_ylabel("Value")
    ax.set_title("Bar chart with rotated labels")
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories, rotation=45, ha="right")
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    ax.set_ylim(0, 25)
    return fig


if __name__ == "__main__":
    fig = create_figure()
    fig.savefig("reference.png", dpi=120)

```

## Artifacts

- `reference.png` — Matplotlib reference render
- `tikz_rendered.png` — TikZ/PGFPlots render
- `diff.png` — Amplified pixel difference (×4)
- `figure.tikz` — Generated TikZ/PGFPlots code
- `wrapper.tex` — Standalone LaTeX wrapper
- `latex.log` — pdflatex output log
- `metadata.json` — Full machine-readable metadata
