
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def generate_sample_data(n=100):
    """Generate sample dataset."""
    np.random.seed(42)
    data = {
        'x': np.random.randn(n),
        'y': np.random.randn(n),
        'category': np.random.choice(['A', 'B', 'C'], n)
    }
    return pd.DataFrame(data)

def basic_statistics(df):
    """Calculate basic statistics."""
    return {
        'mean_x': df['x'].mean(),
        'mean_y': df['y'].mean(),
        'std_x': df['x'].std(),
        'std_y': df['y'].std(),
        'correlation': df['x'].corr(df['y'])
    }

def create_plot(df, save_path=None):
    """Create a simple scatter plot."""
    plt.figure(figsize=(8, 6))
    for category in df['category'].unique():
        subset = df[df['category'] == category]
        plt.scatter(subset['x'], subset['y'], label=category)
    
    plt.xlabel('X values')
    plt.ylabel('Y values')
    plt.title('Sample Data Scatter Plot')
    plt.legend()
    
    if save_path:
        plt.savefig(save_path)
    
    return plt.gcf()

if __name__ == "__main__":
    df = generate_sample_data()
    stats = basic_statistics(df)
    print("Basic Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value:.3f}")
