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
