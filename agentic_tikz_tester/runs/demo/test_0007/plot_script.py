import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def create_figure():
    np.random.seed(7)
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Generate scatter data
    n_points = 80
    x = np.random.uniform(0, 10, n_points)
    y = np.random.uniform(0, 10, n_points)
    colors = x + y
    sizes = 100 * np.abs(np.sin(x)) + 50
    
    # Create scatter plot with colorbar
    scatter = ax.scatter(x, y, c=colors, s=sizes, alpha=0.6, 
                         cmap='viridis', edgecolors='black', linewidth=0.5)
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label('Color Value', fontsize=11)
    
    # Configure axes
    ax.set_xlabel('X Coordinate', fontsize=12)
    ax.set_ylabel('Y Coordinate', fontsize=12)
    ax.set_title('Scatter Plot with Transparency and Colorbar', fontsize=13)
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-0.5, 10.5)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    return fig

if __name__ == "__main__":
    fig = create_figure()
    fig.savefig("reference.png", dpi=120)
