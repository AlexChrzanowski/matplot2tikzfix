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
