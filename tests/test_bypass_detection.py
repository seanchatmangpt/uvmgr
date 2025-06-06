"""
Test suite for bypass detection system.

This module contains tests to verify that the bypass detection system correctly
identifies various attempts to bypass return safeguards and risk management controls.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Any

from uvmgr.risk.bypass_detection import (
    BypassDetector,
    BypassAttemptType,
    BypassDetectionConfig,
    create_default_detector,
    create_custom_detector,
    MarketContext
)

@pytest.fixture
def detector():
    """Create a default bypass detector for testing."""
    return create_default_detector()

@pytest.fixture
def suspicious_params() -> Dict[str, Any]:
    """Create a dictionary of suspicious strategy parameters."""
    return {
        'bar_type': 'ETHUSDT.BINANCE-1-MINUTE-BID-INTERNAL',  # Too short timeframe
        'trade_size': Decimal('0.10'),  # 10% position size (use Decimal)
        'fast_ema_period': 3,  # Too short EMA period
        'slow_ema_period': 5,  # Too short EMA period
        'twap_horizon_secs': 2.0,  # Too short TWAP horizon
        'twap_interval_secs': 0.5,  # Too short TWAP interval
    }

@pytest.fixture
def suspicious_data() -> Dict[str, Any]:
    """Create a dictionary of suspicious data configuration."""
    return {
        'start_time': (datetime.utcnow() - timedelta(days=30)).isoformat(),  # Too short period
        'end_time': datetime.utcnow().isoformat(),
        'data_gaps': [10],  # Large data gap
        'smoothing_factor': 0.5,  # Excessive smoothing
    }

@pytest.fixture
def suspicious_strategy() -> Dict[str, Any]:
    """Create a dictionary of suspicious strategy configuration."""
    return {
        'use_martingale': True,  # Martingale strategy
        'use_stop_loss': False,  # No stop-loss
        'use_grid_trading': True,
        'grid_levels': 50,  # Too many grid levels
        'use_multiple_strategies': True,
        'strategy_count': 10,  # Too many strategies
    }

@pytest.fixture
def suspicious_risk() -> Dict[str, Any]:
    """Create a dictionary of suspicious risk management configuration."""
    return {
        'disable_position_limits': True,
        'disable_drawdown_limits': True,
        'disable_volatility_checks': True,
        'leverage': 10.0,  # Excessive leverage
        'stop_loss_pct': Decimal('0.01'),  # Too tight stop-loss (use Decimal)
    }

@pytest.fixture
def suspicious_performance() -> Dict[str, Any]:
    """Create a dictionary of suspicious performance metrics."""
    return {
        'win_rate': 0.95,  # Unrealistic win rate
        'trade_count': 50,  # Too few trades
        'include_fees': False,  # Fees excluded
        'include_slippage': False,  # Slippage excluded
    }

def test_parameter_manipulation_detection(detector: BypassDetector, suspicious_params: Dict[str, Any]):
    """Test detection of parameter manipulation attempts."""
    assert detector.detect_parameter_manipulation(suspicious_params)
    report = detector.get_detection_report()
    assert BypassAttemptType.PARAMETER_MANIPULATION.name in [d['type'] for d in report['detected_attempts']]

def test_data_manipulation_detection(detector: BypassDetector, suspicious_data: Dict[str, Any]):
    """Test detection of data manipulation attempts."""
    assert detector.detect_data_manipulation(suspicious_data)
    report = detector.get_detection_report()
    assert BypassAttemptType.DATA_MANIPULATION.name in [d['type'] for d in report['detected_attempts']]

def test_strategy_manipulation_detection(detector: BypassDetector, suspicious_strategy: Dict[str, Any]):
    """Test detection of strategy manipulation attempts."""
    assert detector.detect_strategy_manipulation(suspicious_strategy)
    report = detector.get_detection_report()
    assert BypassAttemptType.STRATEGY_MANIPULATION.name in [d['type'] for d in report['detected_attempts']]
    assert len(report['suspicious_patterns']) > 0

def test_risk_management_bypass_detection(detector: BypassDetector, suspicious_risk: Dict[str, Any]):
    """Test detection of risk management bypass attempts."""
    assert detector.detect_risk_management_bypass(suspicious_risk)
    report = detector.get_detection_report()
    assert BypassAttemptType.RISK_MANAGEMENT_BYPASS.name in [d['type'] for d in report['detected_attempts']]
    assert len(report['suspicious_patterns']) > 0

def test_performance_manipulation_detection(detector: BypassDetector, suspicious_performance: Dict[str, Any]):
    """Test detection of performance manipulation attempts."""
    assert detector.detect_performance_manipulation(suspicious_performance)
    report = detector.get_detection_report()
    assert BypassAttemptType.PERFORMANCE_MANIPULATION.name in [d['type'] for d in report['detected_attempts']]
    assert len(report['suspicious_patterns']) > 0

def test_multiple_bypass_attempts(
    detector: BypassDetector,
    suspicious_params: Dict[str, Any],
    suspicious_data: Dict[str, Any],
    suspicious_strategy: Dict[str, Any],
    suspicious_risk: Dict[str, Any],
    suspicious_performance: Dict[str, Any]
):
    """Test detection of multiple bypass attempts."""
    # Check all types of manipulation
    detector.detect_parameter_manipulation(suspicious_params)
    detector.detect_data_manipulation(suspicious_data)
    detector.detect_strategy_manipulation(suspicious_strategy)
    detector.detect_risk_management_bypass(suspicious_risk)
    detector.detect_performance_manipulation(suspicious_performance)
    
    report = detector.get_detection_report()
    assert len(report['detected_attempts']) == 5
    assert len(report['suspicious_patterns']) > 5

def test_custom_detector():
    """Test creation and behavior of custom detector."""
    # Provide a market context that matches the index_arbitrage pattern
    market_context = MarketContext(
        market_type='volatile',
        volatility_regime='extreme',
        market_cap=Decimal('1000000000'),
        trading_volume=Decimal('10000000'),
        liquidity_score=0.9,
        market_maturity='mature',
        has_significant_events=True,
        correlation_with_major_assets={'SPY': 0.5},
        market_microstructure={'spread_multiple': Decimal('3.0'), 'depth_reduction': Decimal('0.5')},
        regulatory_environment='normal',
        market_participants={'HFT': 10, 'MM': 5}
    )
    custom_detector = create_custom_detector(
        min_timeframe=1,  # Allow 1-minute timeframe
        max_position_size=Decimal('0.10'),  # Allow 10% position size
        max_leverage=Decimal('5.0'),  # Allow 5x leverage
        min_ema_period=3,  # Allow shorter EMA periods
        min_twap_horizon=2.0,  # Allow shorter TWAP horizon
        min_twap_interval=0.5,  # Allow shorter TWAP interval
        min_backtest_days=30,  # Allow shorter backtest period
        max_data_gap=10,  # Allow larger data gaps
        min_data_points=500,  # Allow fewer data points
        max_smoothing=0.5,  # Allow more smoothing
        max_grid_levels=50,  # Allow more grid levels
        max_strategies=10,  # Allow more strategies
        min_stop_loss=Decimal('0.01'),  # Allow tighter stop-loss
        max_correlation=0.8,  # Allow higher correlation
        max_drawdown=Decimal('0.20'),  # Allow larger drawdown
        max_volatility=Decimal('0.40'),  # Allow higher volatility
        min_sharpe=Decimal('0.8'),  # Allow lower Sharpe ratio
        max_win_rate=0.9,  # Allow higher win rate
        min_trades=50,  # Allow fewer trades
        max_trade_duration=2880,  # Allow longer trade duration
        require_fees=False,  # Don't require fee inclusion
        require_slippage=False  # Don't require slippage inclusion
    )
    # Attach the market context
    custom_detector.market_context = market_context
    # Test that custom detector allows previously suspicious parameters (matching index_arbitrage pattern keys)
    params = {
        'min_timeframe': 1,
        'max_position_size': Decimal('0.10'),
        'leverage': Decimal('5.0'),
        'min_trades': 1000,
        'required_venues': ['CME', 'NYSE', 'NASDAQ'],
        'risk_management': {
            'max_drawdown': Decimal('0.20'),  # within allowed by custom detector
            'position_limits': True,
            'correlation_checks': True,
            'index_constituent_validation': True,
            'circuit_breaker_checks': True
        }
    }
    result = custom_detector.detect_parameter_manipulation(params)
    if result:
        # Try to get reasons from the detector by running the pattern check directly
        for pattern_name, pattern in custom_detector.config.high_return_patterns.items():
            is_valid, reasons = custom_detector._validate_high_return_pattern(params, pattern)
            if not is_valid:
                print(f"Pattern {pattern_name} did not match: {reasons}")
    assert not result
    # Test that custom detector still catches extreme violations
    assert custom_detector.detect_parameter_manipulation({
        'min_timeframe': 1,
        'max_position_size': Decimal('0.50'),  # Even larger position size
        'leverage': Decimal('10.0'),  # Even larger leverage
        'min_trades': 1000,
        'required_venues': ['CME', 'NYSE', 'NASDAQ'],
        'risk_management': {
            'max_drawdown': Decimal('0.50'),  # Too high
            'position_limits': True,
            'correlation_checks': True,
            'index_constituent_validation': True,
            'circuit_breaker_checks': True
        }
    })

def test_detector_reset(detector: BypassDetector, suspicious_params: Dict[str, Any]):
    """Test that detector state can be reset."""
    # Detect some suspicious patterns
    detector.detect_parameter_manipulation(suspicious_params)
    assert len(detector.get_detection_report()['detected_attempts']) > 0
    
    # Reset detector
    detector.reset()
    assert len(detector.get_detection_report()['detected_attempts']) == 0
    assert len(detector.get_detection_report()['suspicious_patterns']) == 0

def test_timeframe_extraction():
    """Test extraction of timeframe from bar type string."""
    detector = create_default_detector()
    
    # Test various bar types
    assert detector._extract_timeframe('ETHUSDT.BINANCE-1-MINUTE-BID-INTERNAL') == 1
    assert detector._extract_timeframe('ETHUSDT.BINANCE-5-MINUTE-BID-INTERNAL') == 5
    assert detector._extract_timeframe('ETHUSDT.BINANCE-1-HOUR-BID-INTERNAL') == 60
    assert detector._extract_timeframe('ETHUSDT.BINANCE-1-DAY-BID-INTERNAL') == 1440
    
    # Test invalid bar types
    assert detector._extract_timeframe('INVALID-BAR-TYPE') == 0
    assert detector._extract_timeframe('ETHUSDT.BINANCE-INVALID-MINUTE-BID-INTERNAL') == 0

def test_detection_report_format(detector: BypassDetector, suspicious_params: Dict[str, Any]):
    """Test format of detection report."""
    detector.detect_parameter_manipulation(suspicious_params)
    report = detector.get_detection_report()
    
    assert 'detected_attempts' in report
    assert 'suspicious_patterns' in report
    assert 'timestamp' in report
    assert isinstance(report['detected_attempts'], list)
    assert isinstance(report['suspicious_patterns'], list)
    assert isinstance(report['timestamp'], str)
    
    for pattern in report['suspicious_patterns']:
        assert 'type' in pattern
        assert 'message' in pattern
        assert 'timestamp' in pattern
        assert isinstance(pattern['type'], str)
        assert isinstance(pattern['message'], str)
        assert isinstance(pattern['timestamp'], str) 