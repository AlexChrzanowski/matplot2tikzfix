import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def create_figure():
    np.random.seed(5)
    categories = ['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon']
    values = np.array([23, 45, 56, 78, 32])
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(categories, values, color=colors, edgecolor='black', linewidth=1.5)
    
    # Add value labels on top of bars
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(val)}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax.set_ylabel('Value', fontsize=12, fontweight='bold')
    ax.set_xlabel('Category', fontsize=12, fontweight='bold')
    ax.set_title('Bar Chart with Rotated Labels', fontsize=13, fontweight='bold')
    ax.set_ylim(0, max(values) * 1.15)
    
    # Rotate categorical tick labels
    plt.xticks(rotation=45, ha='right')
    
    # Add grid for reference
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    fig.tight_layout()
    return fig

if __name__ == "__main__":
    fig = create_figure()
    fig.savefig("reference.png", dpi=120)
