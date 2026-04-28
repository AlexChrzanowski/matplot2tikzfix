import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def create_figure():
    fig, ax = plt.subplots(figsize=(8, 5))
    
    categories = ['Group A', 'Group B', 'Group C', 'Group D', 'Group E']
    values = [23, 45, 56, 78, 32]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    
    bars = ax.bar(categories, values, color=colors, edgecolor='black', linewidth=1.5)
    
    # Add value labels on top of bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Rotate x-axis labels
    ax.set_xticklabels(categories, rotation=45, ha='right')
    
    # Add grid on y-axis
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Labels and title
    ax.set_xlabel('Categories', fontsize=11, fontweight='bold')
    ax.set_ylabel('Values', fontsize=11, fontweight='bold')
    ax.set_title('Bar Chart with Rotated Labels', fontsize=12, fontweight='bold')
    
    # Set y-axis limit
    ax.set_ylim(0, 90)
    
    fig.tight_layout()
    return fig

if __name__ == "__main__":
    fig = create_figure()
    fig.savefig("reference.png", dpi=120)
