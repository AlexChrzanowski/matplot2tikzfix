import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def create_figure():
    np.random.seed(9)
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Generate scatter data
    n_points = 80
    x = np.random.uniform(0, 10, n_points)
    y = np.random.uniform(0, 8, n_points)
    colors = x**2 + y**2
    
    # Create scatter plot with alpha and colorbar
    scatter = ax.scatter(x, y, c=colors, s=60, alpha=0.6, cmap='viridis', edgecolors='black', linewidth=0.5)
    
    # Add colorbar
    cbar = fig.colorbar(scatter, ax=ax, label=r'$x^2 + y^2$')
    
    # Set labels with mathtext
    ax.set_xlabel(r'Position $x$ (units)', fontsize=11)
    ax.set_ylabel(r'Position $y$ (units)', fontsize=11)
    ax.set_title(r'Scatter Plot: $z = x^2 + y^2$ with $\alpha=0.6$', fontsize=12)
    
    # Set custom axis limits
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-0.5, 8.5)
    
    # Enable grid
    ax.grid(True, alpha=0.3, linestyle='--')
    
    fig.tight_layout()
    return fig

if __name__ == "__main__":
    fig = create_figure()
    fig.savefig("reference.png", dpi=120)
