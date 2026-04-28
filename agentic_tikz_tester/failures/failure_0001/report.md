# Failure failure_0001

## Summary

| Field | Value |
|-------|-------|
| Status | `visual_mismatch` |
| RMS | 39.2415 |
| SSIM | 0.477226 |
| Test ID | `test_0001` |
| Timestamp | 2026-04-28T14:18:38.470467+00:00 |
| Model | claude-opus-4-5 |
| Seed | None |
| Transpiler | makintikz |
| Features | line, log_y, markers, legend, grid |

## Reproduction

```bash
cd failure_0001
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
    np.random.seed(42)
    x = np.linspace(0.1, 10, 40)
    y1 = np.exp(0.4 * x) + np.random.uniform(0, 0.5, 40)
    y2 = np.exp(0.6 * x) + np.random.uniform(0, 0.5, 40)

    fig, ax = plt.subplots()
    ax.semilogy(x, y1, "o-", label=r"$e^{0.4x}$", markersize=4)
    ax.semilogy(x, y2, "s--", label=r"$e^{0.6x}$", markersize=4)
    ax.set_xlabel("x")
    ax.set_ylabel("y (log scale)")
    ax.set_title("Exponential growth (log y)")
    ax.legend()
    ax.grid(True, which="both", linestyle=":")
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
