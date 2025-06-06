"""
Tests for the yfinance-based recent pattern backtest runner.
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, Any
import logging
import pandas as pd
import numpy as np

from uvmgr.risk.recent_market_patterns import (
    RecentPatternDetector,
    RecentStrategyPattern,
    RecentMarketEvent,
    RecentMarketCondition
)
from uvmgr.backtest.recent_pattern_yf_backtest import (
    RecentPatternYFBacktestRunner,
    BacktestResult,
    run_recent_pattern_yf_backtest
)

@pytest.fixture(autouse=True)
def set_debug_log_level():
    logging.getLogger().setLevel(logging.DEBUG)

@pytest.fixture
def mock_market_data():
    """Create mock market data for testing."""
    return {
        'equity': {
            'volatility': 0.35,  # Matches the test condition
            'liquidity': 1000000,
            'correlation': 0.5
        },
        'options': {
            'skew': 0.45,
            'volatility': 0.35,
            'liquidity': 500000
        },
        'data': {
            'feeds': ['OPRA', 'CBOE.VOL'],
            'min_data_points': 1000,
            'update_frequency': '1m',
            'min_depth': 100,
            'max_latency_ms': 1
        },
        'venues': {
            'primary': ['CBOE'],
            'backup': ['ISE', 'NYSE'],
            'min_liquidity': 1000,
            'max_spread': Decimal('0.05')
        }
    }

@pytest.fixture
def mock_pattern_detector(mock_market_data):
    """Create a mock pattern detector with test patterns."""
    detector = RecentPatternDetector()
    now = datetime.now(timezone.utc)
    
    # Set event times to be active (current time falls within event window)
    event_start = now - timedelta(minutes=5)  # 5 minutes ago
    event_end = now + timedelta(minutes=5)    # 5 minutes in future
    
    # Add a test pattern for NVDA earnings
    nvda_earnings = RecentMarketEvent(
        event_type='earnings',
        event_name='NVDA Q4 2024 Earnings',
        start_time=event_start,
        end_time=event_end,
        affected_assets=['NVDA.US'],
        expected_volatility=0.9,
        market_impact=0.9,
        data_sources=['NYSE.TAQ', 'OPRA'],
        venue_access=['NYSE', 'NASDAQ', 'CBOE'],
        historical_precedent='NVDA Q3 2023 earnings'
    )
    
    # Add a test market condition
    market_condition = RecentMarketCondition(
        asset_class='equity',
        condition_type='volatility',
        start_time=event_start,  # Use same start time as event
        current_value=mock_market_data['equity']['volatility'],
        normal_range=(0.15, 0.25),
        is_anomalous=True,
        affected_venues=['NYSE', 'NASDAQ', 'CBOE'],
        required_data_feeds=['CBOE.VOL', 'NYSE.TAQ', 'NASDAQ.TAQ'],
        risk_factors=['earnings_volatility', 'fed_uncertainty']
    )
    
    # Add a test strategy pattern
    strategy_pattern = RecentStrategyPattern(
        name='NVDA Earnings Volatility Trading',
        description='Trading NVDA options volatility around earnings',
        asset_class='options',
        required_events=[nvda_earnings],
        required_conditions=[market_condition],
        strategy_parameters={
            'min_timeframe': 1,  # 1-minute bars
            'max_position_size': Decimal('0.15'),
            'leverage': Decimal('3.0'),
            'min_trades': 100,
            'required_venues': ['CBOE', 'ISE', 'NYSE']
        },
        risk_management={
            'max_drawdown': Decimal('0.25'),
            'position_limits': True,
            'greeks_limits': True,
            'volatility_scaling': True,
            'liquidity_checks': True
        },
        expected_return_range=(Decimal('10.0'), Decimal('50.0')),
        success_probability=0.15,
        data_requirements={
            'feeds': ['OPRA', 'CBOE.VOL'],
            'min_data_points': 1000,
            'update_frequency': '1m'
        },
        venue_requirements={
            'primary': ['CBOE'],
            'backup': ['ISE', 'NYSE'],
            'min_liquidity': 1000,
            'max_spread': Decimal('0.05')
        },
        last_updated=now - timedelta(days=1)  # Set to yesterday to ensure it's within last 30 days
    )

    # Set the detector's state directly
    detector.events = [nvda_earnings]
    detector.conditions = [market_condition]
    detector.patterns = [strategy_pattern]
    detector.last_update = now - timedelta(days=1)  # Set to yesterday
    
    # Verify that patterns are active
    active_patterns = detector.get_active_patterns()
    if not active_patterns:
        raise ValueError("Fixture setup failed: No active patterns found")
        
    return detector

@pytest.fixture
def test_strategy_config():
    """Create a test strategy configuration."""
    return {
        "name": "NVDA Earnings Options Strategy",
        "asset_class": "options",
        "symbols": ["NVDA.US"],
        "min_timeframe": 1,  # 1-minute bars
        "max_position_size": Decimal('0.15'),
        "leverage": Decimal('2.0'),  # Within pattern's limit of 3.0
        "min_trades": 100,
        "required_venues": ["CBOE", "ISE", "NYSE"],
        "risk_management": {
            "max_drawdown": Decimal('0.15'),  # Within pattern's limit of 0.25
            "position_limits": True,
            "greeks_limits": True,
            "volatility_scaling": True,
            "liquidity_checks": True
        },
        "data_requirements": {
            "feeds": ["OPRA", "CBOE.VOL"],
            "min_data_points": 1000,
            "update_frequency": "1m"
        },
        "venue_requirements": {
            "primary": ["CBOE"],
            "backup": ["ISE", "NYSE"],
            "min_liquidity": 1000,
            "max_spread": Decimal('0.05')
        }
    }

def test_nvda_earnings_backtest(mock_pattern_detector, test_strategy_config, mock_market_data):
    """Test backtesting the NVDA earnings strategy."""
    runner = RecentPatternYFBacktestRunner(detector=mock_pattern_detector)
    
    # Mock the market data fetch
    def mock_fetch_market_data(*args, **kwargs):
        return mock_market_data
    
    runner._fetch_market_data = mock_fetch_market_data
    
    result = runner.run_backtest(
        test_strategy_config,
        pattern_name="NVDA Earnings Volatility Trading",
        interval='1h'
    )
    
    assert isinstance(result, BacktestResult)
    assert result.pattern_name == "NVDA Earnings Volatility Trading"
    event = mock_pattern_detector.patterns[0].required_events[0]
    assert result.start_time == event.start_time
    assert result.end_time == event.end_time
    assert isinstance(result.total_return, Decimal)
    assert isinstance(result.sharpe_ratio, float)
    assert isinstance(result.max_drawdown, Decimal)
    assert isinstance(result.win_rate, float)
    assert isinstance(result.trade_count, int)
    assert isinstance(result.avg_trade_duration, timedelta)
    assert isinstance(result.market_conditions_met, list)
    assert isinstance(result.risk_limits_respected, bool)
    assert isinstance(result.data_quality_score, float)
    assert isinstance(result.venue_access_score, float)
    assert isinstance(result.confidence_score, float)

def test_invalid_strategy_backtest(mock_pattern_detector):
    """Test backtesting an invalid strategy configuration."""
    invalid_config = {
        "name": "Invalid Strategy",
        "asset_class": "options",
        "symbols": ["NVDA.US"],
        "leverage": 5.0,  # Exceeds pattern's max_leverage
        "position_size": 2000000,  # Exceeds pattern's position_size_limit
        "data_feeds": ["YFINANCE"],
        "venues": ["NASDAQ"]
    }
    
    runner = RecentPatternYFBacktestRunner(detector=mock_pattern_detector)
    with pytest.raises(ValueError, match="Strategy validation failed"):
        runner.run_backtest(
            invalid_config,
            pattern_name="NVDA Earnings Volatility Trading"
        )

def test_invalid_pattern_backtest(mock_pattern_detector, test_strategy_config):
    """Test backtesting against a non-existent pattern."""
    runner = RecentPatternYFBacktestRunner(detector=mock_pattern_detector)
    with pytest.raises(ValueError, match="Pattern .* not found or not active"):
        runner.run_backtest(
            test_strategy_config,
            pattern_name="NonExistent Pattern"
        )

def test_custom_time_range_backtest(mock_pattern_detector, test_strategy_config):
    """Test backtesting with custom time range."""
    runner = RecentPatternYFBacktestRunner(detector=mock_pattern_detector)
    now = datetime.now(timezone.utc)
    # Use active time range for custom test
    custom_start = now - timedelta(minutes=5)
    custom_end = now + timedelta(minutes=5)
    
    result = runner.run_backtest(
        test_strategy_config,
        pattern_name="NVDA Earnings Volatility Trading",
        start_time=custom_start,
        end_time=custom_end
    )
    
    assert result.start_time == custom_start
    assert result.end_time == custom_end

def test_run_recent_pattern_yf_backtest(test_strategy_config):
    """Test the convenience function for running backtests."""
    result = run_recent_pattern_yf_backtest(
        test_strategy_config,
        pattern_name="NVDA Earnings Volatility Trading"
    )
    
    assert isinstance(result, BacktestResult)
    assert result.pattern_name == "NVDA Earnings Volatility Trading" 