"""
Return Safeguards Module

This module implements safeguards against unrealistic return expectations and enforces
responsible trading practices. It provides validation and monitoring of return targets,
risk parameters, and position sizing to ensure sustainable trading strategies.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class ReturnSafeguards:
    """Configuration for return safeguards and risk parameters."""
    
    # Maximum allowed annualized return target (as a decimal, e.g., 0.20 for 20%)
    max_annualized_return_target: Decimal = Decimal("0.20")
    
    # Maximum allowed daily return target (as a decimal)
    max_daily_return_target: Decimal = Decimal("0.02")
    
    # Maximum allowed drawdown (as a decimal)
    max_allowed_drawdown: Decimal = Decimal("0.15")
    
    # Maximum position size as percentage of portfolio (as a decimal)
    max_position_size_pct: Decimal = Decimal("0.05")
    
    # Maximum leverage allowed
    max_leverage: Decimal = Decimal("3.0")
    
    # Minimum required Sharpe ratio for strategy approval
    min_sharpe_ratio: Decimal = Decimal("1.0")
    
    # Maximum allowed volatility (annualized)
    max_volatility: Decimal = Decimal("0.30")
    
    # Minimum required trading history (in days) for strategy evaluation
    min_trading_history_days: int = 90
    
    def validate_return_target(self, target_return: Decimal, timeframe: str) -> bool:
        """
        Validate if a return target is within acceptable limits.
        
        Args:
            target_return: The target return as a decimal (e.g., 0.20 for 20%)
            timeframe: The timeframe for the return target ('daily' or 'annual')
            
        Returns:
            bool: True if the target is acceptable, False otherwise
            
        Raises:
            ValueError: If timeframe is invalid
        """
        if timeframe.lower() == 'daily':
            if target_return > self.max_daily_return_target:
                logger.warning(
                    f"Daily return target {target_return:.2%} exceeds maximum allowed "
                    f"{self.max_daily_return_target:.2%}"
                )
                return False
        elif timeframe.lower() == 'annual':
            if target_return > self.max_annualized_return_target:
                logger.warning(
                    f"Annual return target {target_return:.2%} exceeds maximum allowed "
                    f"{self.max_annualized_return_target:.2%}"
                )
                return False
        else:
            raise ValueError("timeframe must be 'daily' or 'annual'")
            
        return True
    
    def validate_strategy_parameters(
        self,
        params: Dict[str, Any],
        historical_performance: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Validate strategy parameters against risk limits.
        
        Args:
            params: Dictionary of strategy parameters
            historical_performance: Optional dictionary of historical performance metrics
            
        Returns:
            bool: True if parameters are acceptable, False otherwise
        """
        # Check position sizing
        if 'position_size' in params:
            position_size = Decimal(str(params['position_size']))
            if position_size > self.max_position_size_pct:
                logger.warning(
                    f"Position size {position_size:.2%} exceeds maximum allowed "
                    f"{self.max_position_size_pct:.2%}"
                )
                return False
        
        # Check leverage
        if 'leverage' in params:
            leverage = Decimal(str(params['leverage']))
            if leverage > self.max_leverage:
                logger.warning(
                    f"Leverage {leverage}x exceeds maximum allowed {self.max_leverage}x"
                )
                return False
        
        # Validate historical performance if provided
        if historical_performance:
            # Check Sharpe ratio
            if 'sharpe_ratio' in historical_performance:
                sharpe = Decimal(str(historical_performance['sharpe_ratio']))
                if sharpe < self.min_sharpe_ratio:
                    logger.warning(
                        f"Sharpe ratio {sharpe:.2f} below minimum required "
                        f"{self.min_sharpe_ratio:.2f}"
                    )
                    return False
            
            # Check volatility
            if 'volatility' in historical_performance:
                vol = Decimal(str(historical_performance['volatility']))
                if vol > self.max_volatility:
                    logger.warning(
                        f"Volatility {vol:.2%} exceeds maximum allowed "
                        f"{self.max_volatility:.2%}"
                    )
                    return False
            
            # Check trading history
            if 'trading_days' in historical_performance:
                days = int(historical_performance['trading_days'])
                if days < self.min_trading_history_days:
                    logger.warning(
                        f"Trading history of {days} days below minimum required "
                        f"{self.min_trading_history_days} days"
                    )
                    return False
        
        return True
    
    def get_realistic_return_guidelines(self) -> Dict[str, str]:
        """
        Get guidelines for realistic return expectations.
        
        Returns:
            Dict[str, str]: Dictionary of return guidelines by timeframe
        """
        return {
            "daily": f"Maximum realistic daily return target: {self.max_daily_return_target:.2%}",
            "monthly": f"Maximum realistic monthly return target: {self.max_daily_return_target * 21:.2%}",
            "annual": f"Maximum realistic annual return target: {self.max_annualized_return_target:.2%}",
            "note": "These targets assume proper risk management and diversification. "
                   "Higher returns typically require taking on significantly more risk, "
                   "which may not be sustainable in the long term."
        }

def create_default_safeguards() -> ReturnSafeguards:
    """Create a default instance of ReturnSafeguards with conservative parameters."""
    return ReturnSafeguards()

def create_custom_safeguards(
    max_annualized_return: Optional[Decimal] = None,
    max_daily_return: Optional[Decimal] = None,
    max_drawdown: Optional[Decimal] = None,
    max_position_size: Optional[Decimal] = None,
    max_leverage: Optional[Decimal] = None,
    min_sharpe: Optional[Decimal] = None,
    max_vol: Optional[Decimal] = None,
    min_history_days: Optional[int] = None
) -> ReturnSafeguards:
    """
    Create a custom instance of ReturnSafeguards with specified parameters.
    
    Args:
        max_annualized_return: Maximum allowed annualized return target
        max_daily_return: Maximum allowed daily return target
        max_drawdown: Maximum allowed drawdown
        max_position_size: Maximum position size as percentage of portfolio
        max_leverage: Maximum allowed leverage
        min_sharpe: Minimum required Sharpe ratio
        max_vol: Maximum allowed volatility
        min_history_days: Minimum required trading history in days
        
    Returns:
        ReturnSafeguards: Customized safeguards instance
    """
    defaults = create_default_safeguards()
    
    return ReturnSafeguards(
        max_annualized_return_target=max_annualized_return or defaults.max_annualized_return_target,
        max_daily_return_target=max_daily_return or defaults.max_daily_return_target,
        max_allowed_drawdown=max_drawdown or defaults.max_allowed_drawdown,
        max_position_size_pct=max_position_size or defaults.max_position_size_pct,
        max_leverage=max_leverage or defaults.max_leverage,
        min_sharpe_ratio=min_sharpe or defaults.min_sharpe_ratio,
        max_volatility=max_vol or defaults.max_volatility,
        min_trading_history_days=min_history_days or defaults.min_trading_history_days
    ) 