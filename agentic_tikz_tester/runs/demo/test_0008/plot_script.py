import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def create_figure():
    np.random.seed(8)
    fig, ax = plt.subplots(figsize=(10, 6))
    
    categories = ['$\\alpha$', '$\\beta$', '$\\gamma$', '$\\delta$', '$\\epsilon$']
    values = np.array([23, 45, 56, 78, 32])
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    
    bars = ax.bar(categories, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(value)}',
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax.set_ylabel('Magnitude', fontsize=12, fontweight='bold')
    ax.set_xlabel('Parameters', fontsize=12, fontweight='bold')
    ax.set_title('Parameter Comparison: $x^2 + y^2$', fontsize=14, fontweight='bold')
    
    # Rotate x-axis labels
    ax.tick_params(axis='x', rotation=45)
    
    # Add grid
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Set y-axis limits with some padding
    ax.set_ylim(0, max(values) * 1.15)
    
    fig.tight_layout()
    return fig

if __name__ == "__main__":
    fig = create_figure()
    fig.savefig("reference.png", dpi=120)
