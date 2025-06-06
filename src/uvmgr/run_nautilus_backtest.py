#!/usr/bin/env python3
"""
NautilusTrader Backtest Implementation

This module implements a high-performance backtesting system using NautilusTrader
for algorithmic trading strategies. It includes EMA Cross strategy with TWAP execution
on simulated Binance Spot exchange using historical trade tick data.

Key Features:
- Data loading and wrangling from external sources
- Configurable backtest engine setup
- Multiple venue support
- Strategy and execution algorithm management
- Comprehensive performance analysis
- Proper resource management and cleanup
- Return safeguards and risk management
"""

import logging
from decimal import Decimal
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.backtest.modules import FXRolloverInterestModule
from nautilus_trader.examples.algorithms.twap import TWAPExecAlgorithm
from nautilus_trader.examples.strategies.ema_cross_twap import EMACrossTWAP, EMACrossTWAPConfig
from nautilus_trader.model.currencies import ETH, USDT
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import TraderId, Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.persistence.wranglers import TradeTickDataWrangler
from nautilus_trader.test_kit.providers import TestDataProvider, TestInstrumentProvider

from uvmgr.risk.return_safeguards import ReturnSafeguards, create_default_safeguards
from uvmgr.risk.bypass_detection import BypassDetector, create_default_detector, BypassAttemptType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('backtest.log')
    ]
)
logger = logging.getLogger(__name__)

class SecurityError(Exception):
    """Exception raised when a security violation is detected."""
    pass

class NautilusBacktestRunner:
    """High-level interface for running NautilusTrader backtests."""
    
    def __init__(
        self,
        trader_id: str = "BACKTESTER-001",
        catalog_path: Optional[Path] = None,
        log_level: int = logging.INFO,
        safeguards: Optional[ReturnSafeguards] = None,
        bypass_detector: Optional[BypassDetector] = None
    ):
        """
        Initialize the backtest runner.
        
        Args:
            trader_id: Unique identifier for the trader
            catalog_path: Optional path to Parquet data catalog
            log_level: Logging level for the backtest
            safeguards: Optional return safeguards configuration
            bypass_detector: Optional bypass detector
        """
        self.trader_id = TraderId(trader_id)
        self.catalog_path = catalog_path
        self.log_level = log_level
        self.engine: Optional[BacktestEngine] = None
        self.safeguards = safeguards or create_default_safeguards()
        self.bypass_detector = bypass_detector or create_default_detector()
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """Configure logging for the backtest runner."""
        logger.setLevel(self.log_level)
        
    def _validate_strategy_config(self, config: EMACrossTWAPConfig) -> bool:
        """
        Validate strategy configuration against return safeguards and detect bypass attempts.
        
        Args:
            config: Strategy configuration to validate
            
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # Reset bypass detector state
        self.bypass_detector.reset()
        
        # Check for parameter manipulation
        if self.bypass_detector.detect_parameter_manipulation(config):
            report = self.bypass_detector.get_detection_report()
            raise SecurityError(
                f"Parameter manipulation detected: {report['suspicious_patterns']}"
            )
        
        # Check for strategy manipulation
        if self.bypass_detector.detect_strategy_manipulation(config):
            report = self.bypass_detector.get_detection_report()
            raise SecurityError(
                f"Strategy manipulation detected: {report['suspicious_patterns']}"
            )
        
        # Check for risk management bypass
        if self.bypass_detector.detect_risk_management_bypass(config.get('risk_management', {})):
            report = self.bypass_detector.get_detection_report()
            raise SecurityError(
                f"Risk management bypass detected: {report['suspicious_patterns']}"
            )
        
        # Validate against safeguards
        if not self.safeguards.validate_strategy_parameters(config):
            logger.error("Strategy configuration failed return safeguards validation")
            return False
            
        return True
        
    def _validate_backtest_results(self, results: Dict[str, Any]) -> bool:
        """
        Validate backtest results against return safeguards and detect performance manipulation.
        
        Args:
            results: Dictionary of backtest results
            
        Returns:
            bool: True if results are valid, False otherwise
        """
        # Check for performance manipulation
        if self.bypass_detector.detect_performance_manipulation(results):
            report = self.bypass_detector.get_detection_report()
            raise SecurityError(
                f"Performance manipulation detected: {report['suspicious_patterns']}"
            )
        
        # Calculate performance metrics
        sharpe = self._calculate_sharpe_ratio(results)
        volatility = self._calculate_volatility(results)
        max_drawdown = self._calculate_max_drawdown(results)
        trading_days = self._calculate_trading_days(results)
        annual_return = self._calculate_annual_return(results)
        
        # Validate against safeguards
        if not self.safeguards.validate_strategy_parameters({}, {
            'sharpe_ratio': sharpe,
            'volatility': volatility,
            'max_drawdown': max_drawdown,
            'trading_days': trading_days,
            'annual_return': annual_return
        }):
            logger.error("Backtest results failed return safeguards validation")
            return False
            
        # Validate return targets
        if not self.safeguards.validate_return_target(annual_return, 'annual'):
            logger.error("Backtest results show unrealistic annual returns")
            return False
            
        return True
        
    def _initialize_engine(self) -> None:
        """Initialize the backtest engine with configuration."""
        config = BacktestEngineConfig(
            trader_id=self.trader_id,
            logging=True,
            log_level=self.log_level,
            log_colors=True,
            bypass_logging=False,
        )
        
        self.engine = BacktestEngine(config=config)
        
        # Add FX rollover interest module for forex backtesting
        if self.catalog_path and self.catalog_path.exists():
            catalog = ParquetDataCatalog(self.catalog_path)
            self.engine.add_data_catalog(catalog)
            self.engine.add_module(FXRolloverInterestModule(catalog))
            
    def _setup_venue(self, venue: Venue, starting_balances: List[Money]) -> None:
        """
        Set up a trading venue with specified configuration.
        
        Args:
            venue: The trading venue to set up
            starting_balances: List of initial account balances
        """
        if not self.engine:
            raise RuntimeError("Engine not initialized")
            
        self.engine.add_venue(
            venue=venue,
            oms_type=OmsType.NETTING,
            account_type=AccountType.CASH,
            base_currency=None,  # Multi-currency account
            starting_balances=starting_balances,
        )
        
    def _load_and_process_data(
        self,
        data_path: Path,
        instrument_id: str,
        wrangler: TradeTickDataWrangler
    ) -> List:
        """
        Load and process market data from external source.
        
        Args:
            data_path: Path to the data file
            instrument_id: Identifier for the instrument
            wrangler: Data wrangler for processing
            
        Returns:
            List of processed market data objects
        """
        try:
            if data_path.suffix == '.csv':
                df = pd.read_csv(data_path)
            elif data_path.suffix == '.parquet':
                df = pd.read_parquet(data_path)
            else:
                raise ValueError(f"Unsupported file format: {data_path.suffix}")
                
            return wrangler.process(df)
        except Exception as e:
            logger.error(f"Error loading data from {data_path}: {e}")
            raise
            
    def run_backtest(
        self,
        data_path: Path,
        instrument_id: str,
        venue: Venue,
        strategy_config: EMACrossTWAPConfig,
        starting_balances: List[Money],
        exec_algorithm: Optional[TWAPExecAlgorithm] = None
    ) -> None:
        """
        Run a complete backtest with the specified configuration.
        
        Args:
            data_path: Path to market data
            instrument_id: Identifier for the instrument
            venue: Trading venue
            strategy_config: Strategy configuration
            starting_balances: Initial account balances
            exec_algorithm: Optional execution algorithm
        """
        try:
            # Validate strategy configuration
            if not self._validate_strategy_config(strategy_config):
                raise ValueError("Strategy configuration failed return safeguards validation")
                
            # Initialize engine
            self._initialize_engine()
            if not self.engine:
                raise RuntimeError("Failed to initialize engine")
                
            # Set up venue
            self._setup_venue(venue, starting_balances)
            
            # Load and process data
            instrument = TestInstrumentProvider.ethusdt_binance()  # Example instrument
            wrangler = TradeTickDataWrangler(instrument=instrument)
            data = self._load_and_process_data(data_path, instrument_id, wrangler)
            
            # Add data and instrument
            self.engine.add_instrument(instrument)
            self.engine.add_data(data)
            
            # Add strategy
            strategy = EMACrossTWAP(config=strategy_config)
            self.engine.add_strategy(strategy=strategy)
            
            # Add execution algorithm if provided
            if exec_algorithm:
                self.engine.add_exec_algorithm(exec_algorithm)
                
            # Run backtest
            logger.info("Starting backtest...")
            self.engine.run()
            
            # Generate and validate reports
            results = self._generate_reports(venue)
            if not self._validate_backtest_results(results):
                raise ValueError("Backtest results failed return safeguards validation")
            
        except Exception as e:
            logger.error(f"Error during backtest: {e}")
            raise
        finally:
            if self.engine:
                self.engine.dispose()
                
    def _generate_reports(self, venue: Venue) -> Dict[str, Any]:
        """
        Generate performance and execution reports.
        
        Args:
            venue: Trading venue for report generation
            
        Returns:
            Dict[str, Any]: Dictionary containing backtest results and metrics
        """
        if not self.engine:
            return {}
            
        try:
            # Generate various reports
            account_report = self.engine.trader.generate_account_report(venue)
            order_fills_report = self.engine.trader.generate_order_fills_report()
            positions_report = self.engine.trader.generate_positions_report()
            
            # Extract key metrics
            results = {
                'account_report': account_report,
                'order_fills_report': order_fills_report,
                'positions_report': positions_report,
                'sharpe_ratio': self._calculate_sharpe_ratio(),
                'volatility': self._calculate_volatility(),
                'max_drawdown': self._calculate_max_drawdown(),
                'trading_days': self._calculate_trading_days(),
                'annual_return': self._calculate_annual_return()
            }
            
            # Log completion
            logger.info("Backtest completed successfully")
            logger.info("\nReturn Guidelines:")
            for guideline in self.safeguards.get_realistic_return_guidelines().values():
                logger.info(guideline)
            
            return results
            
        except Exception as e:
            logger.error(f"Error generating reports: {e}")
            raise
            
    def _calculate_sharpe_ratio(self, results: Dict[str, Any]) -> float:
        """Calculate the Sharpe ratio from backtest results."""
        # Implementation depends on available data
        return 0.0  # Placeholder
        
    def _calculate_volatility(self, results: Dict[str, Any]) -> float:
        """Calculate the annualized volatility from backtest results."""
        # Implementation depends on available data
        return 0.0  # Placeholder
        
    def _calculate_max_drawdown(self, results: Dict[str, Any]) -> float:
        """Calculate the maximum drawdown from backtest results."""
        # Implementation depends on available data
        return 0.0  # Placeholder
        
    def _calculate_trading_days(self, results: Dict[str, Any]) -> int:
        """Calculate the number of trading days in the backtest."""
        # Implementation depends on available data
        return 0  # Placeholder
        
    def _calculate_annual_return(self, results: Dict[str, Any]) -> float:
        """Calculate the annualized return from backtest results."""
        # Implementation depends on available data
        return 0.0  # Placeholder

def main():
    """Run the backtest with sample data."""
    # Load stub test data
    provider = TestDataProvider()
    trades_df = provider.read_csv_ticks("binance/ethusdt-trades.csv")

    # Initialize the instrument which matches the data
    ETHUSDT_BINANCE = TestInstrumentProvider.ethusdt_binance()

    # Process into Nautilus objects
    wrangler = TradeTickDataWrangler(instrument=ETHUSDT_BINANCE)
    ticks = wrangler.process(trades_df)

    # Configure backtest engine
    config = BacktestEngineConfig(trader_id=TraderId("BACKTESTER-001"))

    # Build the backtest engine
    engine = BacktestEngine(config=config)

    # Add a trading venue (multiple venues possible)
    BINANCE = Venue("BINANCE")
    engine.add_venue(
        venue=BINANCE,
        oms_type=OmsType.NETTING,
        account_type=AccountType.CASH,  # Spot CASH account (not for perpetuals or futures)
        base_currency=None,  # Multi-currency account
        starting_balances=[Money(1_000_000.0, USDT), Money(10.0, ETH)],
    )

    # Add instrument(s)
    engine.add_instrument(ETHUSDT_BINANCE)

    # Add data
    engine.add_data(ticks)

    # Configure your strategy
    strategy_config = EMACrossTWAPConfig(
        instrument_id=ETHUSDT_BINANCE.id,
        bar_type=BarType.from_str("ETHUSDT.BINANCE-250-TICK-LAST-INTERNAL"),
        trade_size=Decimal("0.10"),
        fast_ema_period=10,
        slow_ema_period=20,
        twap_horizon_secs=10.0,
        twap_interval_secs=2.5,
    )

    # Instantiate and add your strategy
    strategy = EMACrossTWAP(config=strategy_config)
    engine.add_strategy(strategy=strategy)

    # Instantiate and add your execution algorithm
    exec_algorithm = TWAPExecAlgorithm()  # Using defaults
    engine.add_exec_algorithm(exec_algorithm)

    # Run the engine (from start to end of data)
    engine.run()

    # Generate reports
    engine.trader.generate_account_report(BINANCE)
    engine.trader.generate_order_fills_report()
    engine.trader.generate_positions_report()

    # Once done, good practice to dispose of the object if the script continues
    engine.dispose()

if __name__ == "__main__":
    main() 