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
