"""
Bypass Detection Module

This module implements detection and prevention of attempts to bypass return safeguards
and risk management controls. It identifies suspicious patterns in strategy parameters,
data usage, and performance reporting that might indicate attempts to achieve unrealistic returns.

The system uses a confidence-based scoring mechanism to reduce false positives and
recognizes legitimate trading patterns that might otherwise trigger alerts, including
valid high-return strategies that operate in specific market conditions across traditional
and alternative markets.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
import logging
from enum import Enum, auto

logger = logging.getLogger(__name__)

class BypassAttemptType(Enum):
    """Types of bypass attempts that can be detected."""
    PARAMETER_MANIPULATION = auto()
    DATA_MANIPULATION = auto()
    STRATEGY_MANIPULATION = auto()
    RISK_MANAGEMENT_BYPASS = auto()
    PERFORMANCE_MANIPULATION = auto()

@dataclass
class DetectionConfidence:
    """Confidence scoring for bypass detection."""
    score: float  # 0.0 to 1.0
    factors: List[str]  # Factors contributing to the score
    legitimate_patterns: List[str]  # Legitimate patterns that reduced the score

@dataclass
class MarketContext:
    """Market context information for strategy validation."""
    market_type: str  # e.g., 'bull_market', 'bear_market', 'sideways', 'volatile'
    volatility_regime: str  # e.g., 'low', 'medium', 'high', 'extreme'
    market_cap: Decimal  # Market capitalization
    trading_volume: Decimal  # 24h trading volume
    liquidity_score: float  # 0.0 to 1.0
    market_maturity: str  # e.g., 'emerging', 'developing', 'mature'
    has_significant_events: bool  # Whether market has significant events
    correlation_with_major_assets: Dict[str, float]  # Correlation with major assets
    market_microstructure: Dict[str, Any]  # Order book depth, spread, etc.
    regulatory_environment: str  # e.g., 'normal', 'restricted', 'heightened'
    market_participants: Dict[str, int]  # Count of market makers, HFTs, etc.

@dataclass
class HighReturnPattern:
    """Pattern of legitimate high-return strategies."""
    name: str
    description: str
    required_market_conditions: Dict[str, Any]
    strategy_parameters: Dict[str, Any]
    risk_management: Dict[str, Any]
    expected_return_range: Tuple[Decimal, Decimal]
    success_probability: float
    historical_examples: List[str]
    market_type: str  # e.g., 'equity', 'futures', 'options', 'fx'
    required_data_feeds: List[str]  # Required market data feeds
    required_venue_access: List[str]  # Required exchange/market access

@dataclass
class BypassDetectionConfig:
    """Configuration for bypass detection parameters."""
    
    # Parameter validation limits
    min_timeframe_minutes: int = 5
    max_position_size_pct: Decimal = Decimal("0.05")
    max_leverage: Decimal = Decimal("3.0")
    min_ema_period: int = 5
    min_twap_horizon_secs: float = 5.0
    min_twap_interval_secs: float = 1.0
    
    # Data validation limits
    min_backtest_days: int = 90
    max_data_gap_days: int = 5
    min_data_points: int = 1000
    max_smoothing_factor: float = 0.1
    
    # Strategy validation limits
    max_grid_levels: int = 20
    max_strategies: int = 5
    min_stop_loss_pct: Decimal = Decimal("0.02")
    max_correlation_threshold: float = 0.7
    
    # Risk management limits
    max_drawdown_pct: Decimal = Decimal("0.15")
    max_volatility_pct: Decimal = Decimal("0.30")
    min_sharpe_ratio: Decimal = Decimal("1.0")
    max_correlation_pct: Decimal = Decimal("0.7")
    
    # Performance validation limits
    max_win_rate: float = 0.8
    min_trades: int = 100
    max_avg_trade_duration_minutes: int = 1440  # 24 hours
    min_fee_inclusion: bool = True
    min_slippage_inclusion: bool = True
    
    # Confidence thresholds
    min_confidence_score: float = 0.85  # Minimum confidence to trigger alert
    max_false_positive_rate: float = 0.01  # Maximum acceptable false positive rate
    
    # Legitimate strategy patterns
    legitimate_patterns: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'high_frequency_trading': {
            'min_timeframe': 1,  # 1-minute timeframe is legitimate for HFT
            'min_sharpe': Decimal('2.0'),  # HFT strategies typically have high Sharpe
            'max_position_size': Decimal('0.02'),  # Small positions for HFT
            'max_trade_duration': 5,  # Short trade duration
            'min_trades': 1000,  # High trade frequency
        },
        'market_making': {
            'min_timeframe': 1,
            'max_position_size': Decimal('0.03'),
            'min_trades': 500,
            'max_trade_duration': 10,
            'grid_levels': 20,  # Grid trading is legitimate for market making
        },
        'statistical_arbitrage': {
            'min_timeframe': 5,
            'max_position_size': Decimal('0.10'),
            'min_trades': 200,
            'max_correlation': 0.8,
            'min_sharpe': Decimal('1.5'),
        },
        'trend_following': {
            'min_timeframe': 15,
            'max_position_size': Decimal('0.05'),
            'min_trades': 100,
            'max_trade_duration': 1440,  # 24 hours
            'min_sharpe': Decimal('1.0'),
        }
    })

    # High-return strategy patterns
    high_return_patterns: Dict[str, HighReturnPattern] = field(default_factory=lambda: {
        'index_arbitrage': HighReturnPattern(
            name='Index Arbitrage',
            description='Arbitrage between index futures and underlying stocks during market stress',
            required_market_conditions={
                'market_type': 'volatile',
                'volatility_regime': 'extreme',
                'market_microstructure': {
                    'spread_multiple': 3.0,  # Normal spread * 3
                    'depth_reduction': 0.5,  # 50% reduction in order book depth
                },
                'regulatory_environment': 'normal'
            },
            strategy_parameters={
                'min_timeframe': 1,  # 1-second bars
                'max_position_size': Decimal('0.20'),
                'leverage': Decimal('5.0'),
                'min_trades': 1000,
                'required_venues': ['CME', 'NYSE', 'NASDAQ']
            },
            risk_management={
                'max_drawdown': Decimal('0.25'),
                'position_limits': True,
                'correlation_checks': True,
                'index_constituent_validation': True,
                'circuit_breaker_checks': True
            },
            expected_return_range=(Decimal('10.0'), Decimal('50.0')),
            success_probability=0.08,
            historical_examples=['Flash Crash 2010 arbitrage', 'March 2020 index arb'],
            market_type='equity',
            required_data_feeds=['CME.MDP3', 'NYSE.TAQ', 'NASDAQ.TAQ'],
            required_venue_access=['CME', 'NYSE', 'NASDAQ']
        ),
        'options_volatility_arbitrage': HighReturnPattern(
            name='Options Volatility Arbitrage',
            description='Trading volatility skew and term structure during market stress',
            required_market_conditions={
                'volatility_regime': 'extreme',
                'market_type': 'volatile',
                'has_significant_events': True,
                'market_microstructure': {
                    'implied_vol_spread': 0.5,  # 50% spread in implied vols
                    'term_structure_inversion': True
                }
            },
            strategy_parameters={
                'min_timeframe': 1,
                'max_position_size': Decimal('0.15'),
                'leverage': Decimal('3.0'),
                'min_trades': 500,
                'required_venues': ['CBOE', 'ISE', 'NYSE']
            },
            risk_management={
                'max_drawdown': Decimal('0.30'),
                'position_limits': True,
                'greeks_limits': True,
                'volatility_scaling': True,
                'liquidity_checks': True
            },
            expected_return_range=(Decimal('15.0'), Decimal('100.0')),
            success_probability=0.05,
            historical_examples=['VIX spike 2018', 'COVID-19 volatility arb'],
            market_type='options',
            required_data_feeds=['OPRA', 'CBOE.VOL'],
            required_venue_access=['CBOE', 'ISE', 'NYSE']
        ),
        'futures_basis_trading': HighReturnPattern(
            name='Futures Basis Trading',
            description='Trading futures basis during supply/demand imbalances',
            required_market_conditions={
                'market_type': 'volatile',
                'has_significant_events': True,
                'market_microstructure': {
                    'basis_widening': 3.0,  # 3x normal basis
                    'inventory_imbalance': True
                }
            },
            strategy_parameters={
                'min_timeframe': 1,
                'max_position_size': Decimal('0.25'),
                'leverage': Decimal('4.0'),
                'min_trades': 200,
                'required_venues': ['CME', 'ICE']
            },
            risk_management={
                'max_drawdown': Decimal('0.35'),
                'position_limits': True,
                'delivery_risk_management': True,
                'storage_cost_analysis': True,
                'transport_cost_analysis': True
            },
            expected_return_range=(Decimal('20.0'), Decimal('80.0')),
            success_probability=0.07,
            historical_examples=['Crude oil contango 2020', 'Natural gas basis 2021'],
            market_type='futures',
            required_data_feeds=['CME.MDP3', 'ICE.IMPACT'],
            required_venue_access=['CME', 'ICE']
        ),
        'fx_carry_trade': HighReturnPattern(
            name='FX Carry Trade',
            description='High-yield currency carry trade during rate divergence',
            required_market_conditions={
                'market_type': 'trending',
                'volatility_regime': 'low',
                'has_significant_events': True,
                'market_microstructure': {
                    'interest_rate_spread': 5.0,  # 5% rate differential
                    'currency_volatility': 'low'
                }
            },
            strategy_parameters={
                'min_timeframe': 5,
                'max_position_size': Decimal('0.30'),
                'leverage': Decimal('3.0'),
                'min_trades': 50,
                'required_venues': ['FX_ECN']
            },
            risk_management={
                'max_drawdown': Decimal('0.20'),
                'position_limits': True,
                'currency_correlation_checks': True,
                'political_risk_analysis': True,
                'liquidity_checks': True
            },
            expected_return_range=(Decimal('7.0'), Decimal('30.0')),
            success_probability=0.12,
            historical_examples=['JPY carry trade 2005-2007', 'EM carry trade 2010-2013'],
            market_type='fx',
            required_data_feeds=['FX.SPOT'],
            required_venue_access=['FX_ECN']
        )
    })

class BypassDetector:
    """Detector for identifying bypass attempts in trading strategies."""
    
    def __init__(
        self,
        config: Optional[BypassDetectionConfig] = None,
        market_context: Optional[MarketContext] = None
    ):
        """Initialize the bypass detector with market context."""
        self.config = config or BypassDetectionConfig()
        self.market_context = market_context
        self.detected_attempts: Set[BypassAttemptType] = set()
        self.suspicious_patterns: List[Dict[str, Any]] = []
        self.confidence_scores: Dict[BypassAttemptType, DetectionConfidence] = {}
        
    def _calculate_confidence_score(
        self,
        attempt_type: BypassAttemptType,
        suspicious_factors: List[str],
        strategy_type: Optional[str] = None,
        legitimate_patterns: List[str] = []
    ) -> DetectionConfidence:
        """Calculate confidence score for a detection, considering legitimate patterns."""
        base_score = 1.0
        
        # Check for legitimate strategy patterns
        if strategy_type and strategy_type in self.config.legitimate_patterns:
            pattern = self.config.legitimate_patterns[strategy_type]
            for factor in suspicious_factors:
                if self._is_legitimate_for_strategy(factor, pattern):
                    base_score *= 0.5  # Reduce confidence for legitimate patterns
                    legitimate_patterns.append(f"Legitimate for {strategy_type}: {factor}")
        
        # Adjust score based on number of suspicious factors
        factor_count = len(suspicious_factors)
        if factor_count > 3:
            base_score *= 1.2  # Increase confidence for multiple factors
        elif factor_count == 1:
            base_score *= 0.8  # Reduce confidence for single factor
            
        # Cap score between 0 and 1
        final_score = min(max(base_score, 0.0), 1.0)
        
        return DetectionConfidence(
            score=final_score,
            factors=suspicious_factors,
            legitimate_patterns=legitimate_patterns
        )
        
    def _is_legitimate_for_strategy(self, factor: str, pattern: Dict[str, Any]) -> bool:
        """Check if a suspicious factor is legitimate for a given strategy type."""
        # Map factor descriptions to pattern parameters
        factor_mapping = {
            'short_timeframe': ('min_timeframe', lambda x, y: x >= y),
            'large_position': ('max_position_size', lambda x, y: x <= y),
            'high_trade_frequency': ('min_trades', lambda x, y: x >= y),
            'short_trade_duration': ('max_trade_duration', lambda x, y: x <= y),
            'grid_trading': ('grid_levels', lambda x, y: x <= y),
            'high_correlation': ('max_correlation', lambda x, y: x <= y),
            'low_sharpe': ('min_sharpe', lambda x, y: x >= y),
        }
        
        for factor_key, (pattern_key, comparison) in factor_mapping.items():
            if factor_key in factor.lower():
                if pattern_key in pattern:
                    return comparison(factor, pattern[pattern_key])
        return False

    def _validate_high_return_pattern(
        self,
        strategy_config: Dict[str, Any],
        pattern: HighReturnPattern
    ) -> Tuple[bool, List[str]]:
        """
        Validate if a strategy matches a legitimate high-return pattern.
        
        Args:
            strategy_config: Strategy configuration to validate
            pattern: High-return pattern to check against
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, reasons)
        """
        if not self.market_context:
            return False, ["No market context available"]
            
        reasons = []
        is_valid = True
        
        # Check market conditions
        for condition, value in pattern.required_market_conditions.items():
            if not self._check_market_condition(condition, value):
                is_valid = False
                reasons.append(f"Market condition not met: {condition}")
                
        # Check strategy parameters
        for param, value in pattern.strategy_parameters.items():
            if not self._check_strategy_parameter(strategy_config, param, value):
                is_valid = False
                reasons.append(f"Strategy parameter not met: {param}")
                
        # Check risk management
        for risk_param, value in pattern.risk_management.items():
            if not self._check_risk_management(strategy_config, risk_param, value):
                is_valid = False
                reasons.append(f"Risk management not met: {risk_param}")
                
        return is_valid, reasons
        
    def _check_market_condition(self, condition: str, required_value: Any) -> bool:
        """Check if a market condition is met."""
        if not hasattr(self.market_context, condition):
            return False
            
        actual_value = getattr(self.market_context, condition)
        
        if isinstance(required_value, (int, float, Decimal)):
            return actual_value >= required_value
        elif isinstance(required_value, bool):
            return actual_value == required_value
        elif isinstance(required_value, str):
            return actual_value == required_value
        elif isinstance(required_value, dict):
            return all(
                self._check_market_condition(k, v)
                for k, v in required_value.items()
            )
            
        return False
        
    def _check_strategy_parameter(self, strategy_config: Dict[str, Any], param: str, required_value: Any) -> bool:
        """Check if a strategy parameter meets requirements for high-return pattern validation."""
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

    def _check_risk_management(self, strategy_config: Dict[str, Any], risk_param: str, required_value: Any) -> bool:
        """Check if risk management meets requirements for high-return pattern validation."""
        # Accept both flat and nested risk management configs
        risk_config = strategy_config.get('risk_management', strategy_config)
        if risk_param not in risk_config:
            return False
        actual_value = risk_config[risk_param]
        if isinstance(required_value, (int, float, Decimal)):
            return actual_value <= required_value
        elif isinstance(required_value, bool):
            return actual_value == required_value
        return False

    def detect_parameter_manipulation(
        self,
        params: Dict[str, Any],
        strategy_type: Optional[str] = None
    ) -> bool:
        """Detect attempts to manipulate strategy parameters with high-return pattern awareness."""
        suspicious_factors = []
        legitimate_patterns = []
        
        # Check for high-return patterns first
        for pattern_name, pattern in self.config.high_return_patterns.items():
            is_valid, reasons = self._validate_high_return_pattern(params, pattern)
            if is_valid:
                legitimate_patterns.append(f"Matches {pattern_name} pattern")
                # Reduce confidence for legitimate high-return patterns
                return False
                
        # Check timeframe
        if 'bar_type' in params:
            timeframe = self._extract_timeframe(params['bar_type'])
            if timeframe < self.config.min_timeframe_minutes:
                suspicious_factors.append(
                    f"Suspiciously short timeframe: {timeframe} minutes"
                )
        
        # Check position size
        if 'trade_size' in params:
            position_size = Decimal(str(params['trade_size']))
            if position_size > self.config.max_position_size_pct:
                suspicious_factors.append(
                    f"Excessive position size: {position_size:.2%}"
                )
        
        # Check EMA periods
        if 'fast_ema_period' in params and 'slow_ema_period' in params:
            if (params['fast_ema_period'] < self.config.min_ema_period or
                params['slow_ema_period'] < self.config.min_ema_period):
                suspicious_factors.append(
                    f"Suspiciously short EMA periods: {params['fast_ema_period']}, {params['slow_ema_period']}"
                )
        
        # Check TWAP parameters
        if 'twap_horizon_secs' in params and 'twap_interval_secs' in params:
            if (params['twap_horizon_secs'] < self.config.min_twap_horizon_secs or
                params['twap_interval_secs'] < self.config.min_twap_interval_secs):
                suspicious_factors.append(
                    f"Aggressive TWAP parameters: {params['twap_horizon_secs']}s, {params['twap_interval_secs']}s"
                )
        
        # Calculate confidence score with high-return pattern awareness
        confidence = self._calculate_confidence_score(
            BypassAttemptType.PARAMETER_MANIPULATION,
            suspicious_factors,
            strategy_type,
            legitimate_patterns
        )
        
        # Only trigger if confidence exceeds threshold
        if confidence.score >= self.config.min_confidence_score:
            self.detected_attempts.add(BypassAttemptType.PARAMETER_MANIPULATION)
            self.confidence_scores[BypassAttemptType.PARAMETER_MANIPULATION] = confidence
            
            # Log with pattern information
            for factor in suspicious_factors:
                self._log_suspicious_pattern(
                    BypassAttemptType.PARAMETER_MANIPULATION,
                    factor,
                    confidence
                )
            return True
            
        return False
        
    def detect_data_manipulation(self, data_config: Dict[str, Any]) -> bool:
        """
        Detect attempts to manipulate backtest data.
        
        Args:
            data_config: Dictionary of data configuration parameters
            
        Returns:
            bool: True if manipulation is detected, False otherwise
        """
        suspicious = False
        
        # Check backtest period
        if 'start_time' in data_config and 'end_time' in data_config:
            start = datetime.fromisoformat(data_config['start_time'])
            end = datetime.fromisoformat(data_config['end_time'])
            days = (end - start).days
            
            if days < self.config.min_backtest_days:
                self._log_suspicious_pattern(
                    BypassAttemptType.DATA_MANIPULATION,
                    f"Insufficient backtest period: {days} days"
                )
                suspicious = True
        
        # Check data gaps
        if 'data_gaps' in data_config:
            for gap in data_config['data_gaps']:
                if gap > self.config.max_data_gap_days:
                    self._log_suspicious_pattern(
                        BypassAttemptType.DATA_MANIPULATION,
                        f"Large data gap detected: {gap} days"
                    )
                    suspicious = True
        
        # Check data smoothing
        if 'smoothing_factor' in data_config:
            if data_config['smoothing_factor'] > self.config.max_smoothing_factor:
                self._log_suspicious_pattern(
                    BypassAttemptType.DATA_MANIPULATION,
                    f"Excessive data smoothing: {data_config['smoothing_factor']}"
                )
                suspicious = True
        
        if suspicious:
            self.detected_attempts.add(BypassAttemptType.DATA_MANIPULATION)
            
        return suspicious
        
    def detect_strategy_manipulation(self, strategy_config: Dict[str, Any]) -> bool:
        """
        Detect attempts to manipulate strategy behavior.
        
        Args:
            strategy_config: Dictionary of strategy configuration parameters
            
        Returns:
            bool: True if manipulation is detected, False otherwise
        """
        suspicious = False
        
        # Check for martingale-like behavior
        if strategy_config.get('use_martingale', False):
            self._log_suspicious_pattern(
                BypassAttemptType.STRATEGY_MANIPULATION,
                "Martingale-like behavior detected"
            )
            suspicious = True
        
        # Check for missing risk management
        if not strategy_config.get('use_stop_loss', True):
            self._log_suspicious_pattern(
                BypassAttemptType.STRATEGY_MANIPULATION,
                "Missing stop-loss implementation"
            )
            suspicious = True
        
        # Check grid trading parameters
        if strategy_config.get('use_grid_trading', False):
            if strategy_config.get('grid_levels', 0) > self.config.max_grid_levels:
                self._log_suspicious_pattern(
                    BypassAttemptType.STRATEGY_MANIPULATION,
                    f"Excessive grid levels: {strategy_config['grid_levels']}"
                )
                suspicious = True
        
        # Check strategy stacking
        if strategy_config.get('use_multiple_strategies', False):
            if strategy_config.get('strategy_count', 0) > self.config.max_strategies:
                self._log_suspicious_pattern(
                    BypassAttemptType.STRATEGY_MANIPULATION,
                    f"Excessive strategy count: {strategy_config['strategy_count']}"
                )
                suspicious = True
        
        if suspicious:
            self.detected_attempts.add(BypassAttemptType.STRATEGY_MANIPULATION)
            
        return suspicious
        
    def detect_risk_management_bypass(self, risk_config: Dict[str, Any]) -> bool:
        """
        Detect attempts to bypass risk management controls.
        
        Args:
            risk_config: Dictionary of risk management parameters
            
        Returns:
            bool: True if bypass attempt is detected, False otherwise
        """
        suspicious = False
        
        # Check for disabled risk controls
        if any(risk_config.get(f"disable_{control}", False) 
               for control in ['position_limits', 'drawdown_limits', 'volatility_checks']):
            self._log_suspicious_pattern(
                BypassAttemptType.RISK_MANAGEMENT_BYPASS,
                "Disabled risk management controls detected"
            )
            suspicious = True
        
        # Check leverage usage
        if risk_config.get('leverage', 1.0) > self.config.max_leverage:
            self._log_suspicious_pattern(
                BypassAttemptType.RISK_MANAGEMENT_BYPASS,
                f"Excessive leverage: {risk_config['leverage']}x"
            )
            suspicious = True
        
        # Check stop-loss implementation
        if risk_config.get('stop_loss_pct', 0) < self.config.min_stop_loss_pct:
            self._log_suspicious_pattern(
                BypassAttemptType.RISK_MANAGEMENT_BYPASS,
                f"Insufficient stop-loss: {risk_config['stop_loss_pct']:.2%}"
            )
            suspicious = True
        
        if suspicious:
            self.detected_attempts.add(BypassAttemptType.RISK_MANAGEMENT_BYPASS)
            
        return suspicious
        
    def detect_performance_manipulation(self, performance: Dict[str, Any]) -> bool:
        """
        Detect attempts to manipulate performance reporting.
        
        Args:
            performance: Dictionary of performance metrics
            
        Returns:
            bool: True if manipulation is detected, False otherwise
        """
        suspicious = False
        
        # Check win rate
        if performance.get('win_rate', 0) > self.config.max_win_rate:
            self._log_suspicious_pattern(
                BypassAttemptType.PERFORMANCE_MANIPULATION,
                f"Unrealistic win rate: {performance['win_rate']:.2%}"
            )
            suspicious = True
        
        # Check trade count
        if performance.get('trade_count', 0) < self.config.min_trades:
            self._log_suspicious_pattern(
                BypassAttemptType.PERFORMANCE_MANIPULATION,
                f"Insufficient trade count: {performance['trade_count']}"
            )
            suspicious = True
        
        # Check fee inclusion
        if not performance.get('include_fees', True) and self.config.min_fee_inclusion:
            self._log_suspicious_pattern(
                BypassAttemptType.PERFORMANCE_MANIPULATION,
                "Trading fees excluded from performance"
            )
            suspicious = True
        
        # Check slippage inclusion
        if not performance.get('include_slippage', True) and self.config.min_slippage_inclusion:
            self._log_suspicious_pattern(
                BypassAttemptType.PERFORMANCE_MANIPULATION,
                "Slippage excluded from performance"
            )
            suspicious = True
        
        if suspicious:
            self.detected_attempts.add(BypassAttemptType.PERFORMANCE_MANIPULATION)
            
        return suspicious
        
    def _log_suspicious_pattern(
        self,
        attempt_type: BypassAttemptType,
        message: str,
        confidence: Optional[DetectionConfidence] = None
    ) -> None:
        """Log a suspicious pattern detection with confidence information."""
        pattern = {
            'type': attempt_type.name,
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        if confidence:
            pattern.update({
                'confidence_score': confidence.score,
                'legitimate_patterns': confidence.legitimate_patterns,
                'contributing_factors': confidence.factors
            })
            
            # Only log as warning if confidence is high
            if confidence.score >= self.config.min_confidence_score:
                logger.warning(
                    f"High confidence bypass attempt detected ({confidence.score:.2%}): {message}"
                )
            else:
                logger.info(
                    f"Low confidence suspicious pattern detected ({confidence.score:.2%}): {message}"
                )
        else:
            logger.warning(f"Bypass attempt detected: {message}")
            
        self.suspicious_patterns.append(pattern)
        
    def _extract_timeframe(self, bar_type: str) -> int:
        """
        Extract timeframe in minutes from bar type string.
        
        Args:
            bar_type: Bar type string (e.g., "ETHUSDT.BINANCE-1-MINUTE-BID-INTERNAL")
            
        Returns:
            int: Timeframe in minutes
        """
        try:
            parts = bar_type.split('-')
            if len(parts) >= 3:
                value = int(parts[1])
                unit = parts[2].lower()
                if unit == 'minute':
                    return value
                elif unit == 'hour':
                    return value * 60
                elif unit == 'day':
                    return value * 1440
            return 0
        except (ValueError, IndexError):
            return 0
            
    def get_detection_report(self) -> Dict[str, Any]:
        """Get a detailed report of detected bypass attempts with confidence scores."""
        return {
            'detected_attempts': [
                {
                    'type': attempt.name,
                    'confidence': self.confidence_scores.get(attempt, DetectionConfidence(0.0, [], [])).score,
                    'legitimate_patterns': self.confidence_scores.get(attempt, DetectionConfidence(0.0, [], [])).legitimate_patterns
                }
                for attempt in self.detected_attempts
            ],
            'suspicious_patterns': self.suspicious_patterns,
            'timestamp': datetime.utcnow().isoformat(),
            'false_positive_rate': self._estimate_false_positive_rate()
        }
        
    def _estimate_false_positive_rate(self) -> float:
        """Estimate the false positive rate based on confidence scores."""
        if not self.confidence_scores:
            return 0.0
            
        # Calculate weighted average of (1 - confidence) scores
        total_weight = 0
        weighted_sum = 0
        
        for confidence in self.confidence_scores.values():
            weight = len(confidence.factors)
            total_weight += weight
            weighted_sum += (1 - confidence.score) * weight
            
        return weighted_sum / total_weight if total_weight > 0 else 0.0
        
    def reset(self) -> None:
        """Reset the detector state."""
        self.detected_attempts.clear()
        self.suspicious_patterns.clear()
        self.confidence_scores.clear()

def create_default_detector() -> BypassDetector:
    """Create a default instance of BypassDetector with conservative parameters."""
    return BypassDetector()

def create_custom_detector(
    min_timeframe: Optional[int] = None,
    max_position_size: Optional[Decimal] = None,
    max_leverage: Optional[Decimal] = None,
    min_ema_period: Optional[int] = None,
    min_twap_horizon: Optional[float] = None,
    min_twap_interval: Optional[float] = None,
    min_backtest_days: Optional[int] = None,
    max_data_gap: Optional[int] = None,
    min_data_points: Optional[int] = None,
    max_smoothing: Optional[float] = None,
    max_grid_levels: Optional[int] = None,
    max_strategies: Optional[int] = None,
    min_stop_loss: Optional[Decimal] = None,
    max_correlation: Optional[float] = None,
    max_drawdown: Optional[Decimal] = None,
    max_volatility: Optional[Decimal] = None,
    min_sharpe: Optional[Decimal] = None,
    max_win_rate: Optional[float] = None,
    min_trades: Optional[int] = None,
    max_trade_duration: Optional[int] = None,
    require_fees: Optional[bool] = None,
    require_slippage: Optional[bool] = None
) -> BypassDetector:
    """
    Create a custom instance of BypassDetector with specified parameters.
    
    Args:
        min_timeframe: Minimum allowed timeframe in minutes
        max_position_size: Maximum allowed position size as percentage
        max_leverage: Maximum allowed leverage
        min_ema_period: Minimum allowed EMA period
        min_twap_horizon: Minimum TWAP horizon in seconds
        min_twap_interval: Minimum TWAP interval in seconds
        min_backtest_days: Minimum required backtest period in days
        max_data_gap: Maximum allowed data gap in days
        min_data_points: Minimum required data points
        max_smoothing: Maximum allowed data smoothing factor
        max_grid_levels: Maximum allowed grid trading levels
        max_strategies: Maximum allowed concurrent strategies
        min_stop_loss: Minimum required stop-loss percentage
        max_correlation: Maximum allowed strategy correlation
        max_drawdown: Maximum allowed drawdown percentage
        max_volatility: Maximum allowed volatility percentage
        min_sharpe: Minimum required Sharpe ratio
        max_win_rate: Maximum allowed win rate
        min_trades: Minimum required number of trades
        max_trade_duration: Maximum allowed average trade duration in minutes
        require_fees: Whether to require fee inclusion
        require_slippage: Whether to require slippage inclusion
        
    Returns:
        BypassDetector: Customized detector instance
    """
    defaults = BypassDetectionConfig()
    
    config = BypassDetectionConfig(
        min_timeframe_minutes=min_timeframe or defaults.min_timeframe_minutes,
        max_position_size_pct=max_position_size or defaults.max_position_size_pct,
        max_leverage=max_leverage or defaults.max_leverage,
        min_ema_period=min_ema_period or defaults.min_ema_period,
        min_twap_horizon_secs=min_twap_horizon or defaults.min_twap_horizon_secs,
        min_twap_interval_secs=min_twap_interval or defaults.min_twap_interval_secs,
        min_backtest_days=min_backtest_days or defaults.min_backtest_days,
        max_data_gap_days=max_data_gap or defaults.max_data_gap_days,
        min_data_points=min_data_points or defaults.min_data_points,
        max_smoothing_factor=max_smoothing or defaults.max_smoothing_factor,
        max_grid_levels=max_grid_levels or defaults.max_grid_levels,
        max_strategies=max_strategies or defaults.max_strategies,
        min_stop_loss_pct=min_stop_loss or defaults.min_stop_loss_pct,
        max_correlation_threshold=max_correlation or defaults.max_correlation_threshold,
        max_drawdown_pct=max_drawdown or defaults.max_drawdown_pct,
        max_volatility_pct=max_volatility or defaults.max_volatility_pct,
        min_sharpe_ratio=min_sharpe or defaults.min_sharpe_ratio,
        max_win_rate=max_win_rate or defaults.max_win_rate,
        min_trades=min_trades or defaults.min_trades,
        max_avg_trade_duration_minutes=max_trade_duration or defaults.max_avg_trade_duration_minutes,
        min_fee_inclusion=require_fees if require_fees is not None else defaults.min_fee_inclusion,
        min_slippage_inclusion=require_slippage if require_slippage is not None else defaults.min_slippage_inclusion
    )
    
    return BypassDetector(config) 