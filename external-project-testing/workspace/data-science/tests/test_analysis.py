
import pytest
import pandas as pd
from datascience_external_test.analysis import generate_sample_data, basic_statistics, create_plot

def test_generate_sample_data():
    df = generate_sample_data(50)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 50
    assert set(df.columns) == {'x', 'y', 'category'}
    assert set(df['category'].unique()).issubset({'A', 'B', 'C'})

def test_basic_statistics():
    df = generate_sample_data(100)
    stats = basic_statistics(df)
    
    required_keys = ['mean_x', 'mean_y', 'std_x', 'std_y', 'correlation']
    assert all(key in stats for key in required_keys)
    assert all(isinstance(value, float) for value in stats.values())
    assert -1 <= stats['correlation'] <= 1

def test_create_plot():
    df = generate_sample_data(30)
    fig = create_plot(df)
    assert fig is not None
    # Test that plot was created without errors
