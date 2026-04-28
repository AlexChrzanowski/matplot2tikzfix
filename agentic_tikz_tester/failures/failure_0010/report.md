# Failure failure_0010

## Summary

| Field | Value |
|-------|-------|
| Status | `visual_mismatch` |
| RMS | 74.8550 |
| SSIM | 0.607947 |
| Test ID | `test_0005` |
| Timestamp | 2026-04-28T14:24:05.976575+00:00 |
| Model | claude-3-5-haiku-20241022 |
| Seed | None |
| Transpiler | makintikz |
| Features | imshow, colorbar, axis_labels |

## Reproduction

```bash
cd failure_0010
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
    np.random.seed(99)
    x = np.linspace(-3, 3, 50)
    y = np.linspace(-3, 3, 50)
    X, Y = np.meshgrid(x, y)
    Z = np.sin(X) * np.cos(Y) + 0.1 * np.random.randn(50, 50)

    fig, ax = plt.subplots()
    im = ax.imshow(Z, origin="lower", extent=[-3, 3, -3, 3],
                   cmap="RdBu_r", aspect="auto")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Amplitude")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(r"$\sin(x)\cos(y)$ with noise")
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
