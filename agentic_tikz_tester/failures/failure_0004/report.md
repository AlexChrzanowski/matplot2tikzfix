# Failure failure_0004

## Summary

| Field | Value |
|-------|-------|
| Status | `visual_mismatch` |
| RMS | 38.2493 |
| SSIM | 0.593221 |
| Test ID | `test_0004` |
| Timestamp | 2026-04-28T14:18:45.556967+00:00 |
| Model | claude-opus-4-5 |
| Seed | None |
| Transpiler | makintikz |
| Features | errorbar, capsize, custom_ticks, log_y |

## Reproduction

```bash
cd failure_0004
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
    np.random.seed(3)
    x = np.array([1, 2, 4, 8, 16, 32])
    y = 2.5 * x + np.random.randn(6) * 0.5
    yerr = 0.2 * y

    fig, ax = plt.subplots()
    ax.errorbar(x, y, yerr=yerr, fmt="o-", capsize=5, capthick=1.5,
                color="darkred", ecolor="red", label="measurements")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels([str(v) for v in x])
    ax.set_xlabel("n (log$_2$ scale)")
    ax.set_ylabel("Time (log scale)")
    ax.set_title("Scaling experiment")
    ax.legend()
    ax.grid(True, which="both", alpha=0.4)
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
