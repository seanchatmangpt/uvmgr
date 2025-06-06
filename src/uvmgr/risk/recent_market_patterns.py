"""
Recent Market Patterns Detection Module

This module implements detection of legitimate high-return patterns in recent market conditions
(within the last 30 days) that might otherwise trigger bypass detection alerts. It focuses on
current market microstructure, recent events, and emerging opportunities across different asset classes.

The module is designed to be updated frequently to reflect current market conditions and
reduce false positives for legitimate trading strategies operating in recent market environments.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta, timezone
import logging
from enum import Enum, auto
from uvmgr.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

class StrategyValidationError(Exception):
    pass

@dataclass
class RecentMarketEvent:
    """Recent market event that could create legitimate trading opportunities."""
    event_type: str  # e.g., 'earnings', 'fed_meeting', 'economic_data', 'corporate_action'
    event_name: str
    start_time: datetime
    end_time: datetime
    affected_assets: List[str]
    expected_volatility: float  # 0.0 to 1.0
    market_impact: float  # 0.0 to 1.0
    data_sources: List[str]  # Required data feeds
    venue_access: List[str]  # Required venue access
    historical_precedent: Optional[str] = None

@dataclass
class RecentMarketCondition:
    """Current market conditions that could support legitimate high-return strategies."""
    asset_class: str  # e.g., 'equity', 'futures', 'options', 'fx'
    condition_type: str  # e.g., 'volatility', 'liquidity', 'correlation', 'basis'
    start_time: datetime
    current_value: float
    normal_range: Tuple[float, float]
    is_anomalous: bool
    affected_venues: List[str]
    required_data_feeds: List[str]
    risk_factors: List[str]

@dataclass
class RecentStrategyPattern:
    """Pattern of legitimate high-return strategies in recent market conditions."""
    name: str
    description: str
    asset_class: str
    required_events: List[RecentMarketEvent]
    required_conditions: List[RecentMarketCondition]
    strategy_parameters: Dict[str, Any]
    risk_management: Dict[str, Any]
    expected_return_range: Tuple[Decimal, Decimal]
    success_probability: float
    data_requirements: Dict[str, Any]
    venue_requirements: Dict[str, Any]
    last_updated: datetime

class RecentPatternDetector:
    """Detector for identifying legitimate high-return patterns in recent market conditions."""
    
    def __init__(self):
        """Initialize the recent pattern detector."""
        self.events: List[RecentMarketEvent] = []
        self.conditions: List[RecentMarketCondition] = []
        self.patterns: List[RecentStrategyPattern] = []
        self.last_update: datetime = datetime.now(timezone.utc)
        
    def update_market_events(self) -> None:
        """Update the list of recent market events (to be called daily)."""
        current_time = datetime.now(timezone.utc)
        thirty_days_ago = current_time - timedelta(days=30)
        
        # Recent Fed-related events
        self.events.extend([
            RecentMarketEvent(
                event_type='fed_meeting',
                event_name='FOMC March 2024 Meeting',
                start_time=datetime(2024, 3, 20, 18, 0, tzinfo=timezone.utc),  # 2:00 PM ET
                end_time=datetime(2024, 3, 20, 19, 0, tzinfo=timezone.utc),    # 3:00 PM ET
                affected_assets=['ES', 'ZN', 'USD', 'SPY', 'QQQ'],
                expected_volatility=0.8,
                market_impact=0.9,
                data_sources=['CME.MDP3', 'OPRA', 'NYSE.TAQ'],
                venue_access=['CME', 'NYSE', 'NASDAQ', 'CBOE'],
                historical_precedent='March 2023 FOMC meeting'
            ),
            RecentMarketEvent(
                event_type='economic_data',
                event_name='March 2024 NFP Release',
                start_time=datetime(2024, 4, 5, 12, 30, tzinfo=timezone.utc),  # 8:30 AM ET
                end_time=datetime(2024, 4, 5, 13, 0, tzinfo=timezone.utc),     # 9:00 AM ET
                affected_assets=['ES', 'ZN', 'USD', 'SPY', 'QQQ'],
                expected_volatility=0.7,
                market_impact=0.8,
                data_sources=['CME.MDP3', 'NYSE.TAQ'],
                venue_access=['CME', 'NYSE', 'NASDAQ']
            )
        ])
        
        # Recent corporate events
        self.events.extend([
            RecentMarketEvent(
                event_type='earnings',
                event_name='NVDA Q4 2024 Earnings',
                start_time=datetime(2024, 2, 21, 16, 0, tzinfo=timezone.utc),  # 4:00 PM ET
                end_time=datetime(2024, 2, 21, 17, 0, tzinfo=timezone.utc),    # 5:00 PM ET
                affected_assets=['NVDA', 'SOXX', 'SMH', 'QQQ'],
                expected_volatility=0.9,
                market_impact=0.9,
                data_sources=['NYSE.TAQ', 'OPRA'],
                venue_access=['NYSE', 'NASDAQ', 'CBOE'],
                historical_precedent='NVDA Q3 2023 earnings'
            ),
            RecentMarketEvent(
                event_type='corporate_action',
                event_name='NVDA Stock Split Announcement',
                start_time=datetime(2024, 2, 21, 16, 0, tzinfo=timezone.utc),  # 4:00 PM ET
                end_time=datetime(2024, 2, 21, 17, 0, tzinfo=timezone.utc),    # 5:00 PM ET
                affected_assets=['NVDA', 'SOXX', 'SMH'],
                expected_volatility=0.8,
                market_impact=0.8,
                data_sources=['NYSE.TAQ', 'OPRA'],
                venue_access=['NYSE', 'NASDAQ', 'CBOE']
            )
        ])
        
        # Recent market conditions
        self.conditions.extend([
            RecentMarketCondition(
                asset_class='equity',
                condition_type='volatility',
                start_time=datetime(2024, 2, 21, tzinfo=timezone.utc),
                current_value=0.35,  # Current VIX level
                normal_range=(0.15, 0.25),
                is_anomalous=True,
                affected_venues=['NYSE', 'NASDAQ', 'CBOE'],
                required_data_feeds=['CBOE.VOL', 'NYSE.TAQ', 'NASDAQ.TAQ'],
                risk_factors=['earnings_volatility', 'fed_uncertainty']
            ),
            RecentMarketCondition(
                asset_class='options',
                condition_type='skew',
                start_time=datetime(2024, 2, 21, tzinfo=timezone.utc),
                current_value=0.45,  # Current skew level
                normal_range=(0.20, 0.30),
                is_anomalous=True,
                affected_venues=['CBOE', 'ISE', 'NYSE'],
                required_data_feeds=['OPRA', 'CBOE.VOL'],
                risk_factors=['volatility_regime', 'market_stress']
            ),
            RecentMarketCondition(
                asset_class='futures',
                condition_type='basis',
                start_time=datetime(2024, 2, 21, tzinfo=timezone.utc),
                current_value=0.0025,  # Current basis level
                normal_range=(0.0005, 0.0015),
                is_anomalous=True,
                affected_venues=['CME', 'ICE'],
                required_data_feeds=['CME.MDP3', 'ICE.IMPACT'],
                risk_factors=['funding_rate', 'market_liquidity']
            )
        ])
        
        # Recent strategy patterns
        self.patterns.extend([
            RecentStrategyPattern(
                name='NVDA Earnings Volatility Trading',
                description='Trading NVDA options volatility around earnings and stock split',
                asset_class='options',
                required_events=[
                    event for event in self.events 
                    if event.event_name in ['NVDA Q4 2024 Earnings', 'NVDA Stock Split Announcement']
                ],
                required_conditions=[
                    condition for condition in self.conditions 
                    if condition.condition_type == 'skew' and condition.asset_class == 'options'
                ],
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
                    'min_depth': 100,
                    'max_latency_ms': 1
                },
                venue_requirements={
                    'primary': ['CBOE'],
                    'backup': ['ISE', 'NYSE'],
                    'min_liquidity': 1000
                },
                last_updated=datetime(2024, 2, 21, tzinfo=timezone.utc)
            ),
            RecentStrategyPattern(
                name='FOMC Meeting Basis Trading',
                description='Trading futures basis around FOMC meeting',
                asset_class='futures',
                required_events=[
                    event for event in self.events 
                    if event.event_name == 'FOMC March 2024 Meeting'
                ],
                required_conditions=[
                    condition for condition in self.conditions 
                    if condition.condition_type == 'basis' and condition.asset_class == 'futures'
                ],
                strategy_parameters={
                    'min_timeframe': 1,  # 1-second bars
                    'max_position_size': Decimal('0.20'),
                    'leverage': Decimal('4.0'),
                    'min_trades': 200,
                    'required_venues': ['CME', 'ICE']
                },
                risk_management={
                    'max_drawdown': Decimal('0.30'),
                    'position_limits': True,
                    'funding_rate_checks': True,
                    'liquidity_checks': True,
                    'circuit_breaker_checks': True
                },
                expected_return_range=(Decimal('15.0'), Decimal('40.0')),
                success_probability=0.12,
                data_requirements={
                    'feeds': ['CME.MDP3', 'ICE.IMPACT'],
                    'min_depth': 500,
                    'max_latency_ms': 1
                },
                venue_requirements={
                    'primary': ['CME'],
                    'backup': ['ICE'],
                    'min_liquidity': 2000
                },
                last_updated=datetime(2024, 3, 20, tzinfo=timezone.utc)
            )
        ])
        
        # Remove events and conditions older than 30 days
        self.events = [e for e in self.events if e.start_time >= thirty_days_ago]
        self.conditions = [c for c in self.conditions if c.start_time >= thirty_days_ago]
        self.patterns = [p for p in self.patterns if p.last_updated >= thirty_days_ago]
        
        self.last_update = current_time
        
    def get_active_patterns(self) -> List[RecentStrategyPattern]:
        """Get currently active strategy patterns."""
        current_time = datetime.now(timezone.utc)
        return [
            pattern for pattern in self.patterns
            if any(
                event.start_time <= current_time <= event.end_time
                for event in pattern.required_events
            )
        ]
        
    def validate_strategy(
        self,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Tuple[bool, List[str], Optional[RecentStrategyPattern]]:
        """
        Validate if a strategy matches any recent legitimate patterns.
        
        Args:
            strategy_config: Strategy configuration to validate
            market_data: Current market data and conditions
            
        Returns:
            Tuple[bool, List[str], Optional[RecentStrategyPattern]]:
                (is_valid, reasons, matching_pattern)
        """
        # Update market events if needed
        if (datetime.now(timezone.utc) - self.last_update) > timedelta(hours=1):
            self.update_market_events()
            
        active_patterns = self.get_active_patterns()
        
        for pattern in active_patterns:
            is_valid, reasons = self._validate_against_pattern(
                strategy_config,
                market_data,
                pattern
            )
            if is_valid:
                return True, reasons, pattern
                
        return False, ["No matching recent market patterns"], None
        
    def _validate_against_pattern(
        self,
        strategy_config: Dict[str, Any],
        market_data: Dict[str, Any],
        pattern: RecentStrategyPattern
    ) -> Tuple[bool, List[str]]:
        """Validate strategy against a specific pattern."""
        reasons = []
        is_valid = True
        
        # Check if all required events are active
        current_time = datetime.now(timezone.utc)
        active_events = [
            event for event in pattern.required_events
            if event.start_time <= current_time <= event.end_time
        ]
        if not active_events:
            logger.debug("No active required events for pattern %s", pattern.name)
            return False, ["No active required events"]
            
        # Check if all required conditions are met
        for condition in pattern.required_conditions:
            result = self._check_market_condition(market_data, condition)
            logger.debug(f"Market condition {condition.condition_type}: {result}")
            if not result:
                is_valid = False
                reasons.append(f"Market condition not met: {condition.condition_type}")
                
        # Check strategy parameters
        for param, value in pattern.strategy_parameters.items():
            result = self._check_strategy_parameter(strategy_config, param, value)
            logger.debug(f"Strategy parameter {param}: expected {value}, got {strategy_config.get(param)}, result: {result}")
            if not result:
                is_valid = False
                reasons.append(f"Strategy parameter not met: {param}")
                
        # Check risk management
        for risk_param, value in pattern.risk_management.items():
            result = self._check_risk_management(strategy_config, risk_param, value)
            logger.debug(f"Risk management {risk_param}: expected {value}, got {strategy_config.get('risk_management', {}).get(risk_param)}, result: {result}")
            if not result:
                is_valid = False
                reasons.append(f"Risk management not met: {risk_param}")
                
        # Check data requirements
        for req, value in pattern.data_requirements.items():
            result = self._check_data_requirement(market_data, req, value)
            logger.debug(f"Data requirement {req}: expected {value}, got {market_data.get('data', {}).get(req)}, result: {result}")
            if not result:
                is_valid = False
                reasons.append(f"Data requirement not met: {req}")
                
        # Check venue requirements
        for req, value in pattern.venue_requirements.items():
            result = self._check_venue_requirement(market_data, req, value)
            logger.debug(f"Venue requirement {req}: expected {value}, got {market_data.get('venues', {}).get(req)}, result: {result}")
            if not result:
                is_valid = False
                reasons.append(f"Venue requirement not met: {req}")
                
        return is_valid, reasons
        
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
        
    def _check_strategy_parameter(
        self,
        strategy_config: Dict[str, Any],
        param: str,
        required_value: Any
    ) -> bool:
        """Check if a strategy parameter meets requirements."""
        if param not in strategy_config:
            return False
        actual_value = strategy_config[param]
        if isinstance(required_value, (int, float, Decimal)):
            return actual_value <= required_value
        elif isinstance(required_value, (list, tuple, set)):
            return list(actual_value) == list(required_value)
        elif isinstance(required_value, str):
            return actual_value == required_value
        elif isinstance(required_value, bool):
            return actual_value == required_value
        return False
        
    def _check_risk_management(
        self,
        strategy_config: Dict[str, Any],
        risk_param: str,
        required_value: Any
    ) -> bool:
        """Check if risk management meets requirements."""
        if 'risk_management' not in strategy_config:
            return False
            
        risk_config = strategy_config['risk_management']
        if risk_param not in risk_config:
            return False
            
        actual_value = risk_config[risk_param]
        if isinstance(required_value, (int, float, Decimal)):
            return actual_value <= required_value
        elif isinstance(required_value, bool):
            return actual_value == required_value
            
        return False
        
    def _check_data_requirement(
        self,
        market_data: Dict[str, Any],
        requirement: str,
        required_value: Any
    ) -> bool:
        """Check if data requirements are met."""
        if 'data' not in market_data:
            return False
        data_config = market_data['data']
        if requirement not in data_config:
            return False
        actual_value = data_config[requirement]
        if isinstance(required_value, (int, float, Decimal)):
            return actual_value >= required_value
        elif isinstance(required_value, (list, tuple, set)):
            return list(actual_value) == list(required_value)
        elif isinstance(required_value, str):
            return actual_value == required_value
        return False
        
    def _check_venue_requirement(
        self,
        market_data: Dict[str, Any],
        requirement: str,
        required_value: Any
    ) -> bool:
        """Check if venue requirements are met."""
        if 'venues' not in market_data:
            return False
        venue_config = market_data['venues']
        if requirement not in venue_config:
            return False
        actual_value = venue_config[requirement]
        if isinstance(required_value, (int, float, Decimal)):
            return actual_value >= required_value
        elif isinstance(required_value, (list, tuple, set)):
            return list(actual_value) == list(required_value)
        elif isinstance(required_value, str):
            return actual_value == required_value
        return False

def create_recent_pattern_detector() -> RecentPatternDetector:
    """Create a new instance of RecentPatternDetector."""
    detector = RecentPatternDetector()
    detector.update_market_events()
    return detector 