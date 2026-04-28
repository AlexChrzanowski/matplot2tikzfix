import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def create_figure():
    np.random.seed(4)
    categories = ['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon']
    values = np.array([23.5, 45.2, 38.9, 52.1, 31.7])
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    
    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.bar(categories, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    # Add value labels on top of bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value:.1f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Rotate x-axis labels
    ax.set_xticklabels(categories, rotation=45, ha='right')
    
    # Grid on y-axis
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Labels and title
    ax.set_ylabel('Values ($\\mu$m)', fontsize=12)
    ax.set_xlabel('Categories', fontsize=12)
    ax.set_title('Bar Chart with Rotated Labels and Value Annotations', fontsize=13, fontweight='bold')
    
    # Set y-axis limits
    ax.set_ylim(0, 60)
    
    fig.tight_layout()
    return fig

if __name__ == "__main__":
    fig = create_figure()
    fig.savefig("reference.png", dpi=120)
