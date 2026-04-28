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
