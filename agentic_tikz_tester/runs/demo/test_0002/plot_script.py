import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def create_figure():
    np.random.seed(2)
    categories = ['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon']
    values = np.array([23, 45, 56, 38, 62])
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(categories, values, color=colors, edgecolor='black', linewidth=1.5)
    
    # Add value labels on top of bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(value)}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Rotate x-axis tick labels
    ax.set_xticklabels(categories, rotation=45, ha='right')
    
    ax.set_ylabel('Values', fontsize=12, fontweight='bold')
    ax.set_title('Bar Chart with Rotated Labels and Value Annotations', fontsize=13, fontweight='bold')
    ax.set_ylim(0, max(values) * 1.15)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    fig.tight_layout()
    return fig

if __name__ == "__main__":
    fig = create_figure()
    fig.savefig("reference.png", dpi=120)
