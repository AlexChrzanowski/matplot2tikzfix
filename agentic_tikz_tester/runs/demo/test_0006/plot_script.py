import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def create_figure():
    np.random.seed(6)
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Generate scatter data with color gradient
    n = 50
    x = np.random.uniform(0, 10, n)
    y = np.random.uniform(0, 10, n)
    colors = x + y  # Color based on sum
    sizes = np.abs(np.sin(x)) * 100 + 30
    
    # Create scatter plot with alpha and colorbar
    scatter = ax.scatter(x, y, c=colors, s=sizes, alpha=0.6, 
                         cmap='viridis', edgecolors='black', linewidth=0.5)
    
    # Add colorbar
    cbar = fig.colorbar(scatter, ax=ax, label='Color Value')
    
    # Customize axes
    ax.set_xlim(-0.5, 11)
    ax.set_ylim(-0.5, 11)
    ax.set_xlabel('X Coordinate ($x$)')
    ax.set_ylabel('Y Coordinate ($y$)')
    ax.set_title('Scatter Plot with Transparency and Colorbar')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    return fig

if __name__ == "__main__":
    fig = create_figure()
    fig.savefig("reference.png", dpi=120)
