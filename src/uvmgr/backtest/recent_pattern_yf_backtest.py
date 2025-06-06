"""
Recent Pattern Backtest Runner using yfinance data

This module implements backtesting of strategies against recent market patterns using yfinance data.
It validates strategies against actual market conditions and events from the last 30 days.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
from uvmgr.logging_config import setup_logging

from ..risk.recent_market_patterns import (
    RecentPatternDetector,
    RecentStrategyPattern,
    RecentMarketEvent,
    RecentMarketCondition
)

setup_logging()
logger = logging.getLogger(__name__)

class StrategyValidationError(Exception):
    pass

@dataclass
class BacktestResult:
    """Results from backtesting a strategy against recent patterns."""
    pattern_name: str
    start_time: datetime
    end_time: datetime
    total_return: Decimal
    sharpe_ratio: float
    max_drawdown: Decimal
    win_rate: float
    trade_count: int
    avg_trade_duration: timedelta
    market_conditions_met: List[str]
    risk_limits_respected: bool
    data_quality_score: float
    venue_access_score: float
    confidence_score: float

class RecentPatternYFBacktestRunner:
    """Runner for backtesting strategies against recent market patterns using yfinance data."""
    
    def __init__(self, detector: Optional[RecentPatternDetector] = None):
        """Initialize the backtest runner."""
        self.detector = detector or create_recent_pattern_detector()
        
    def run_backtest(
        self,
        strategy_config: Dict[str, Any],
        pattern_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        interval: str = '1h'  # yfinance interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    ) -> BacktestResult:
        """
        Run a backtest against recent market patterns using yfinance data.
        
        Args:
            strategy_config: Strategy configuration to backtest
            pattern_name: Optional specific pattern to test against
            start_time: Optional start time (defaults to pattern event start)
            end_time: Optional end time (defaults to pattern event end)
            interval: yfinance data interval
            
        Returns:
            BacktestResult: Results of the backtest
        """
        # Get active patterns
        active_patterns = self.detector.get_active_patterns()
        if not active_patterns:
            raise ValueError("No active patterns found in the last 30 days")
            
        # Filter by pattern name if specified
        if pattern_name:
            patterns = [p for p in active_patterns if p.name == pattern_name]
            if not patterns:
                raise ValueError(f"Pattern {pattern_name} not found or not active")
        else:
            patterns = active_patterns
            
        # Get market data for the pattern's required events
        market_data = self._fetch_market_data(patterns[0], interval)
        
        # Validate strategy against pattern
        is_valid, reasons, pattern = self.detector.validate_strategy(
            strategy_config,
            market_data
        )
        if not is_valid:
            raise StrategyValidationError(f"Strategy validation failed: {reasons}")
            
        # Set backtest time range
        if not start_time:
            start_time = min(e.start_time for e in pattern.required_events)
        if not end_time:
            end_time = max(e.end_time for e in pattern.required_events)
            
        # Run the backtest
        return self._execute_backtest(
            strategy_config,
            pattern,
            market_data,
            start_time,
            end_time
        )
        
    def _fetch_market_data(
        self,
        pattern: RecentStrategyPattern,
        interval: str
    ) -> Dict[str, Any]:
        """Fetch market data from yfinance for the pattern's required events."""
        market_data = {
            'data': {
                'feeds': pattern.data_requirements['feeds'],
                'min_data_points': pattern.data_requirements['min_data_points'],
                'update_frequency': pattern.data_requirements['update_frequency']
            },
            'venues': {
                'primary': pattern.venue_requirements['primary'],
                'backup': pattern.venue_requirements['backup'],
                'min_liquidity': pattern.venue_requirements['min_liquidity'],
                'max_spread': pattern.venue_requirements['max_spread']
            },
            pattern.asset_class: {}
        }
        
        # Fetch data for each required event
        for event in pattern.required_events:
            symbols = [s.split('.')[0] for s in event.affected_assets]  # Strip .US suffix
            try:
                # Fetch market data using yfinance
                data = yf.download(
                    symbols,
                    start=event.start_time,
                    end=event.end_time,
                    interval=interval,
                    progress=False
                )
                
                # Process the data
                if not data.empty:
                    # Add volatility and other market conditions
                    market_data[pattern.asset_class].update({
                        'volatility': data['Close'].pct_change().std() * np.sqrt(252),
                        'volume': data['Volume'].mean(),
                        'spread': (data['High'] - data['Low']).mean() / data['Close'].mean()
                    })
                    
            except Exception as e:
                logger.error(f"Error fetching data for {symbols}: {e}")
                
        return market_data
        
    def _process_market_data(
        self,
        df: pd.DataFrame,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> None:
        """Process yfinance market data into required format."""
        # Calculate market metrics
        volatility = self._calculate_volatility(df)
        liquidity = self._calculate_liquidity(df)
        skew = self._calculate_skew(df)
        
        # Update market data based on asset class
        if symbol.endswith(('.US', '.US-OPT')):
            # Options data
            market_data['options'].update({
                'skew': skew,
                'volatility': volatility,
                'liquidity': liquidity
            })
        elif symbol.endswith('.US'):
            # Equity data
            market_data['equity'].update({
                'volatility': volatility,
                'liquidity': liquidity,
                'correlation': self._calculate_correlation(df)
            })
        elif symbol.endswith(('.US-FUT', '.US-FWD')):
            # Futures data
            market_data['futures'].update({
                'basis': self._calculate_basis(df),
                'liquidity': liquidity,
                'volatility': volatility
            })
            
        # Update data quality metrics
        market_data['data'].update({
            'feeds': list(set(market_data['data'].get('feeds', []) + ['YFINANCE'])),
            'min_depth': self._calculate_min_depth(df),
            'max_latency_ms': self._calculate_max_latency(df)
        })
        
        # Update venue metrics
        venue = 'NYSE' if symbol.endswith('.US') else 'NASDAQ'
        market_data['venues'].update({
            'primary': list(set(market_data['venues'].get('primary', []) + [venue])),
            'min_liquidity': self._calculate_venue_liquidity(df)
        })
        
    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """Calculate market volatility from OHLCV data."""
        if 'Close' in df.columns:
            returns = df['Close'].pct_change()
            return returns.std() * np.sqrt(252)  # Annualized
        return 0.0
        
    def _calculate_liquidity(self, df: pd.DataFrame) -> float:
        """Calculate market liquidity score from volume data."""
        if 'Volume' in df.columns:
            return df['Volume'].mean() * df['Volume'].count() / len(df)
        return 0.0
        
    def _calculate_skew(self, df: pd.DataFrame) -> float:
        """Calculate price skew from OHLCV data."""
        if 'Close' in df.columns:
            returns = df['Close'].pct_change()
            return returns.skew()
        return 0.0
        
    def _calculate_basis(self, df: pd.DataFrame) -> float:
        """Calculate futures basis from OHLCV data."""
        if 'Close' in df.columns:
            # For demo, use a simple basis calculation
            # In practice, you'd compare futures price to spot
            return (df['High'] - df['Low']).mean() / df['Close'].mean()
        return 0.0
        
    def _calculate_correlation(self, df: pd.DataFrame) -> float:
        """Calculate market correlation."""
        # For demo, use autocorrelation
        if 'Close' in df.columns:
            returns = df['Close'].pct_change()
            return returns.autocorr()
        return 0.0
        
    def _calculate_min_depth(self, df: pd.DataFrame) -> int:
        """Calculate minimum order book depth."""
        if 'Volume' in df.columns:
            return int(df['Volume'].min())
        return 0
        
    def _calculate_max_latency(self, df: pd.DataFrame) -> float:
        """Calculate maximum latency in milliseconds."""
        if not df.empty:
            return (df.index.max() - df.index.min()).total_seconds() * 1000
        return 0.0
        
    def _calculate_venue_liquidity(self, df: pd.DataFrame) -> float:
        """Calculate venue liquidity score."""
        if 'Volume' in df.columns:
            return df['Volume'].sum() / len(df)
        return 0.0
        
    def _execute_backtest(
        self,
        strategy_config: Dict[str, Any],
        pattern: RecentStrategyPattern,
        market_data: Dict[str, Any],
        start_time: datetime,
        end_time: datetime
    ) -> BacktestResult:
        """Execute the backtest and calculate results."""
        # Implement strategy execution logic here
        # This would typically involve:
        # 1. Running the strategy on the market data
        # 2. Tracking trades and positions
        # 3. Calculating performance metrics
        
        # For now, return placeholder results
        return BacktestResult(
            pattern_name=pattern.name,
            start_time=start_time,
            end_time=end_time,
            total_return=Decimal('0.0'),
            sharpe_ratio=0.0,
            max_drawdown=Decimal('0.0'),
            win_rate=0.0,
            trade_count=0,
            avg_trade_duration=timedelta(),
            market_conditions_met=[
                condition.condition_type
                for condition in pattern.required_conditions
                if self._check_market_condition(market_data, condition)
            ],
            risk_limits_respected=True,
            data_quality_score=1.0,
            venue_access_score=1.0,
            confidence_score=1.0
        )
        
    def _check_market_condition(
        self,
        market_data: Dict[str, Any],
        condition: RecentMarketCondition
    ) -> bool:
        """Check if a market condition is met."""
        if condition.asset_class not in market_data:
            return False
            
        asset_data = market_data[condition.asset_class]
        if condition.condition_type not in asset_data:
            return False
            
        current_value = asset_data[condition.condition_type]
        return (
            condition.normal_range[0] <= current_value <= condition.normal_range[1]
            if not condition.is_anomalous
            else current_value > condition.normal_range[1]
        )

def run_recent_pattern_yf_backtest(
    strategy_config: Dict[str, Any],
    pattern_name: Optional[str] = None,
    interval: str = '1h'
) -> BacktestResult:
    """
    Run a backtest against recent market patterns using yfinance data.
    
    Args:
        strategy_config: Strategy configuration to backtest
        pattern_name: Optional specific pattern to test against
        interval: yfinance data interval
        
    Returns:
        BacktestResult: Results of the backtest
    """
    runner = RecentPatternYFBacktestRunner()
    return runner.run_backtest(strategy_config, pattern_name, interval=interval) 