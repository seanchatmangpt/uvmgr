"""
Recent Pattern Backtest Runner

This module implements backtesting of strategies against recent market patterns using real market data.
It validates strategies against actual market conditions and events from the last 30 days.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import pandas as pd
import numpy as np
from databento import Historical
import os

from ..risk.recent_market_patterns import (
    RecentPatternDetector,
    RecentStrategyPattern,
    RecentMarketEvent,
    RecentMarketCondition
)

logger = logging.getLogger(__name__)

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

class RecentPatternBacktestRunner:
    """Runner for backtesting strategies against recent market patterns."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        detector: Optional[RecentPatternDetector] = None
    ):
        """Initialize the backtest runner."""
        self.api_key = api_key or os.getenv('DATABENTO_API_KEY')
        if not self.api_key:
            raise ValueError("Databento API key is required")
            
        self.client = Historical(self.api_key)
        self.detector = detector or create_recent_pattern_detector()
        
    def run_backtest(
        self,
        strategy_config: Dict[str, Any],
        pattern_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> BacktestResult:
        """
        Run a backtest against recent market patterns using real market data.
        
        Args:
            strategy_config: Strategy configuration to backtest
            pattern_name: Optional specific pattern to test against
            start_time: Optional start time (defaults to pattern event start)
            end_time: Optional end time (defaults to pattern event end)
            
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
        market_data = self._fetch_market_data(patterns[0])
        
        # Validate strategy against pattern
        is_valid, reasons, pattern = self.detector.validate_strategy(
            strategy_config,
            market_data
        )
        if not is_valid:
            raise ValueError(f"Strategy validation failed: {reasons}")
            
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
        
    def _fetch_market_data(self, pattern: RecentStrategyPattern) -> Dict[str, Any]:
        """Fetch real market data for the pattern's required events."""
        market_data = {
            'data': {},
            'venues': {},
            pattern.asset_class: {}
        }
        
        # Fetch data for each required event
        for event in pattern.required_events:
            for data_source in event.data_sources:
                try:
                    # Fetch market data using Databento
                    data = self.client.timeseries.get_range(
                        dataset=self._get_dataset(data_source),
                        schema=self._get_schema(data_source),
                        start=event.start_time.isoformat(),
                        end=event.end_time.isoformat(),
                        symbols=event.affected_assets
                    )
                    
                    # Process the data
                    df = data.to_df()
                    self._process_market_data(df, data_source, market_data)
                    
                except Exception as e:
                    logger.error(f"Error fetching data for {data_source}: {e}")
                    
        return market_data
        
    def _get_dataset(self, data_source: str) -> str:
        """Map data source to Databento dataset."""
        dataset_map = {
            'CME.MDP3': 'GLBX.MDP3',
            'NYSE.TAQ': 'XNYS.TAQ',
            'NASDAQ.TAQ': 'XNAS.TAQ',
            'OPRA': 'OPRA',
            'CBOE.VOL': 'XCBO.VOL',
            'ICE.IMPACT': 'IFEU.IMPACT'
        }
        return dataset_map.get(data_source, data_source)
        
    def _get_schema(self, data_source: str) -> str:
        """Map data source to Databento schema."""
        schema_map = {
            'CME.MDP3': 'mbo',  # Market by Order
            'NYSE.TAQ': 'trades',  # Trades
            'NASDAQ.TAQ': 'trades',
            'OPRA': 'trades',
            'CBOE.VOL': 'statistics',
            'ICE.IMPACT': 'mbo'
        }
        return schema_map.get(data_source, 'trades')
        
    def _process_market_data(
        self,
        df: pd.DataFrame,
        data_source: str,
        market_data: Dict[str, Any]
    ) -> None:
        """Process market data into required format."""
        if data_source.startswith('CME'):
            # Process futures data
            market_data['futures'].update({
                'basis': self._calculate_basis(df),
                'liquidity': self._calculate_liquidity(df),
                'volatility': self._calculate_volatility(df)
            })
        elif data_source.startswith(('NYSE', 'NASDAQ')):
            # Process equity data
            market_data['equity'].update({
                'volatility': self._calculate_volatility(df),
                'liquidity': self._calculate_liquidity(df),
                'correlation': self._calculate_correlation(df)
            })
        elif data_source == 'OPRA':
            # Process options data
            market_data['options'].update({
                'skew': self._calculate_skew(df),
                'volatility': self._calculate_volatility(df),
                'liquidity': self._calculate_liquidity(df)
            })
            
        # Update data quality metrics
        market_data['data'].update({
            'feeds': list(set(market_data['data'].get('feeds', []) + [data_source])),
            'min_depth': self._calculate_min_depth(df),
            'max_latency_ms': self._calculate_max_latency(df)
        })
        
        # Update venue metrics
        venue = data_source.split('.')[0]
        market_data['venues'].update({
            'primary': list(set(market_data['venues'].get('primary', []) + [venue])),
            'min_liquidity': self._calculate_venue_liquidity(df)
        })
        
    def _calculate_basis(self, df: pd.DataFrame) -> float:
        """Calculate futures basis."""
        if 'basis' in df.columns:
            return df['basis'].mean()
        # Implement basis calculation if not available
        return 0.0
        
    def _calculate_liquidity(self, df: pd.DataFrame) -> float:
        """Calculate market liquidity score."""
        if 'size' in df.columns:
            return df['size'].mean() * df['size'].count() / len(df)
        return 0.0
        
    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """Calculate market volatility."""
        if 'price' in df.columns:
            returns = df['price'].pct_change()
            return returns.std() * np.sqrt(252)  # Annualized
        return 0.0
        
    def _calculate_correlation(self, df: pd.DataFrame) -> float:
        """Calculate market correlation."""
        # Implement correlation calculation
        return 0.0
        
    def _calculate_skew(self, df: pd.DataFrame) -> float:
        """Calculate options skew."""
        if 'implied_volatility' in df.columns:
            return df['implied_volatility'].std()
        return 0.0
        
    def _calculate_min_depth(self, df: pd.DataFrame) -> int:
        """Calculate minimum order book depth."""
        if 'depth' in df.columns:
            return df['depth'].min()
        return 0
        
    def _calculate_max_latency(self, df: pd.DataFrame) -> float:
        """Calculate maximum latency in milliseconds."""
        if 'timestamp' in df.columns:
            return (df['timestamp'].max() - df['timestamp'].min()).total_seconds() * 1000
        return 0.0
        
    def _calculate_venue_liquidity(self, df: pd.DataFrame) -> float:
        """Calculate venue liquidity score."""
        if 'size' in df.columns:
            return df['size'].sum() / len(df)
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

def run_recent_pattern_backtest(
    strategy_config: Dict[str, Any],
    pattern_name: Optional[str] = None,
    api_key: Optional[str] = None
) -> BacktestResult:
    """
    Run a backtest against recent market patterns.
    
    Args:
        strategy_config: Strategy configuration to backtest
        pattern_name: Optional specific pattern to test against
        api_key: Optional Databento API key
        
    Returns:
        BacktestResult: Results of the backtest
    """
    runner = RecentPatternBacktestRunner(api_key=api_key)
    return runner.run_backtest(strategy_config, pattern_name) 