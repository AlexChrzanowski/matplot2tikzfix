# Failure failure_0003

## Summary

| Field | Value |
|-------|-------|
| Status | `visual_mismatch` |
| RMS | 41.2779 |
| SSIM | 0.768015 |
| Test ID | `test_0003` |
| Timestamp | 2026-04-28T14:18:43.231291+00:00 |
| Model | claude-opus-4-5 |
| Seed | None |
| Transpiler | makintikz |
| Features | fill_between, alpha, legend, line |

## Reproduction

```bash
cd failure_0003
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
    np.random.seed(0)
    x = np.linspace(0, 2 * np.pi, 80)
    y_mean = np.sin(x)
    y_upper = y_mean + 0.3 + 0.1 * np.random.randn(80)
    y_lower = y_mean - 0.3 - 0.1 * np.random.randn(80)

    fig, ax = plt.subplots()
    ax.plot(x, y_mean, "b-", linewidth=2, label="mean")
    ax.fill_between(x, y_lower, y_upper, alpha=0.3, color="blue", label="uncertainty")
    ax.set_xlabel(r"$\theta$ (radians)")
    ax.set_ylabel(r"$\sin(\theta)$")
    ax.set_title("Sine with uncertainty band")
    ax.legend()
    ax.set_xlim(0, 2 * np.pi)
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
