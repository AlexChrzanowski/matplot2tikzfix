"""
Five hand-written built-in test cases used by --no-llm mode.

Each entry is a GeneratedScript with features and code.
The code defines create_figure() and a __main__ block.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GeneratedScript:
    features: list[str]
    code: str
    name: str = ""


# ---------------------------------------------------------------------------
# 1. Line plot: log y, markers, legend, grid
# ---------------------------------------------------------------------------
_EXAMPLE_1 = GeneratedScript(
    name="line_logy_markers_legend_grid",
    features=["line", "log_y", "markers", "legend", "grid"],
    code='''\
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
''',
)

# ---------------------------------------------------------------------------
# 2. Bar chart: rotated categorical labels
# ---------------------------------------------------------------------------
_EXAMPLE_2 = GeneratedScript(
    name="bar_categorical_rotated",
    features=["bar", "categorical_ticks", "rotated_labels", "grid"],
    code='''\
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
''',
)

# ---------------------------------------------------------------------------
# 3. fill_between with alpha and legend
# ---------------------------------------------------------------------------
_EXAMPLE_3 = GeneratedScript(
    name="fill_between_alpha_legend",
    features=["fill_between", "alpha", "legend", "line"],
    code='''\
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
    ax.set_xlabel(r"$\\theta$ (radians)")
    ax.set_ylabel(r"$\\sin(\\theta)$")
    ax.set_title("Sine with uncertainty band")
    ax.legend()
    ax.set_xlim(0, 2 * np.pi)
    return fig


if __name__ == "__main__":
    fig = create_figure()
    fig.savefig("reference.png", dpi=120)
''',
)

# ---------------------------------------------------------------------------
# 4. Errorbar with capsize and custom ticks
# ---------------------------------------------------------------------------
_EXAMPLE_4 = GeneratedScript(
    name="errorbar_capsize_custom_ticks",
    features=["errorbar", "capsize", "custom_ticks", "log_y"],
    code='''\
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
''',
)

# ---------------------------------------------------------------------------
# 5. imshow with colorbar and axis labels
# ---------------------------------------------------------------------------
_EXAMPLE_5 = GeneratedScript(
    name="imshow_colorbar",
    features=["imshow", "colorbar", "axis_labels"],
    code='''\
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
    ax.set_title(r"$\\sin(x)\\cos(y)$ with noise")
    return fig


if __name__ == "__main__":
    fig = create_figure()
    fig.savefig("reference.png", dpi=120)
''',
)

EXAMPLES: list[GeneratedScript] = [
    _EXAMPLE_1,
    _EXAMPLE_2,
    _EXAMPLE_3,
    _EXAMPLE_4,
    _EXAMPLE_5,
]


def get_examples() -> list[GeneratedScript]:
    return EXAMPLES
