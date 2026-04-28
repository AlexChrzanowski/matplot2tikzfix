import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def create_figure():
    np.random.seed(10)
    fig, ax = plt.subplots(figsize=(8, 5))
    
    categories = ['$\\alpha$', '$\\beta$', '$\\gamma$', '$\\delta$', '$\\epsilon$']
    values = np.array([23, 45, 36, 52, 41])
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    
    bars = ax.bar(categories, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    # Add value labels on top of bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(value)}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('Bar Chart with Greek Letters: $y = f(x)$', fontsize=13, fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(0, 60)
    
    # Rotate x-axis labels
    ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    return fig

if __name__ == '__main__':
    fig = create_figure()
    fig.savefig('reference.png', dpi=120)
