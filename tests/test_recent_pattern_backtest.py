"""
Test script for running backtests against recent market patterns using real market data.
"""

import os
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any

from uvmgr.backtest.recent_pattern_backtest import (
    run_recent_pattern_backtest,
    BacktestResult
)

# Test strategy configuration for NVDA earnings pattern
NVDA_EARNINGS_STRATEGY = {
    'name': 'NVDA Earnings Volatility Strategy',
    'asset_class': 'options',
    'min_timeframe': 1,  # 1-minute bars
    'max_position_size': Decimal('0.15'),
    'leverage': Decimal('3.0'),
    'min_trades': 100,
    'required_venues': ['CBOE', 'ISE', 'NYSE'],
    'risk_management': {
        'max_drawdown': Decimal('0.25'),
        'position_limits': True,
        'greeks_limits': True,
        'volatility_scaling': True,
        'liquidity_checks': True
    },
    'data_requirements': {
        'feeds': ['OPRA', 'CBOE.VOL'],
        'min_depth': 100,
        'max_latency_ms': 1
    },
    'venue_requirements': {
        'primary': ['CBOE'],
        'backup': ['ISE', 'NYSE'],
        'min_liquidity': 1000
    }
}

@pytest.fixture
def api_key() -> str:
    """Get Databento API key from environment."""
    key = os.getenv('DATABENTO_API_KEY')
    if not key:
        pytest.skip("Databento API key not found in environment")
    return key

def test_nvda_earnings_backtest(api_key: str) -> None:
    """Test backtesting the NVDA earnings strategy against real market data."""
    # Run the backtest
    result = run_recent_pattern_backtest(
        strategy_config=NVDA_EARNINGS_STRATEGY,
        pattern_name='NVDA Earnings Volatility Trading',
        api_key=api_key
    )
    
    # Validate the results
    assert isinstance(result, BacktestResult)
    assert result.pattern_name == 'NVDA Earnings Volatility Trading'
    assert result.start_time <= result.end_time
    assert result.start_time >= datetime(2024, 2, 21)  # NVDA earnings date
    assert result.end_time <= datetime(2024, 2, 22)  # Day after earnings
    
    # Check market conditions
    assert len(result.market_conditions_met) > 0
    assert 'skew' in result.market_conditions_met
    assert 'volatility' in result.market_conditions_met
    
    # Check risk management
    assert result.risk_limits_respected
    assert result.max_drawdown <= Decimal('0.25')
    
    # Check data quality
    assert result.data_quality_score > 0.8
    assert result.venue_access_score > 0.8
    assert result.confidence_score > 0.8
    
    # Check performance metrics
    assert result.trade_count >= 100
    assert result.win_rate > 0
    assert result.sharpe_ratio > 0
    assert result.avg_trade_duration > timedelta(0)

def test_invalid_strategy_backtest(api_key: str) -> None:
    """Test backtesting an invalid strategy configuration."""
    invalid_strategy = NVDA_EARNINGS_STRATEGY.copy()
    invalid_strategy['leverage'] = Decimal('10.0')  # Too high leverage
    
    with pytest.raises(ValueError) as exc_info:
        run_recent_pattern_backtest(
            strategy_config=invalid_strategy,
            pattern_name='NVDA Earnings Volatility Trading',
            api_key=api_key
        )
    assert "Strategy validation failed" in str(exc_info.value)

def test_invalid_pattern_backtest(api_key: str) -> None:
    """Test backtesting against a non-existent pattern."""
    with pytest.raises(ValueError) as exc_info:
        run_recent_pattern_backtest(
            strategy_config=NVDA_EARNINGS_STRATEGY,
            pattern_name='NonExistentPattern',
            api_key=api_key
        )
    assert "Pattern NonExistentPattern not found" in str(exc_info.value)

def test_custom_time_range_backtest(api_key: str) -> None:
    """Test backtesting with a custom time range."""
    start_time = datetime(2024, 2, 21, 15, 30)  # 30 minutes before earnings
    end_time = datetime(2024, 2, 21, 16, 30)   # 30 minutes after earnings
    
    result = run_recent_pattern_backtest(
        strategy_config=NVDA_EARNINGS_STRATEGY,
        pattern_name='NVDA Earnings Volatility Trading',
        api_key=api_key
    )
    
    assert result.start_time >= start_time
    assert result.end_time <= end_time

if __name__ == '__main__':
    # Run the tests if executed directly
    pytest.main([__file__, '-v']) 