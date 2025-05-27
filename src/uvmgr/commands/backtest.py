"""Backtesting command for uvmgr."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.node import (
    BacktestDataConfig,
    BacktestEngineConfig,
    BacktestNode,
    BacktestRunConfig,
    BacktestVenueConfig,
)
from nautilus_trader.config import ImportableStrategyConfig, LoggingConfig
from nautilus_trader.core.message import Event
from nautilus_trader.indicators.macd import MovingAverageConvergenceDivergence
from nautilus_trader.model import InstrumentId, Position, Quantity, QuoteTick, Venue
from nautilus_trader.model.enums import OrderSide, PositionSide, PriceType
from nautilus_trader.model.events import PositionOpened
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.trading.strategy import Strategy, StrategyConfig


class MACDConfig(StrategyConfig):
    """Configuration for the MACD strategy."""
    
    instrument_id: InstrumentId
    fast_period: int = 12
    slow_period: int = 26
    trade_size: int = 1_000_000
    entry_threshold: float = 0.00010


class MACDStrategy(Strategy):
    """A simple MACD-based trading strategy."""
    
    def __init__(self, config: MACDConfig):
        super().__init__(config=config)
        self.macd = MovingAverageConvergenceDivergence(
            fast_period=config.fast_period,
            slow_period=config.slow_period,
            price_type=PriceType.MID,
        )
        self.trade_size = Quantity.from_int(config.trade_size)
        self.position: Optional[Position] = None
        self._logger = logging.getLogger(__name__)

    def on_start(self):
        """Actions to be performed on strategy start."""
        self.subscribe_quote_ticks(instrument_id=self.config.instrument_id)
        self._logger.info("Strategy started")

    def on_stop(self):
        """Actions to be performed on strategy stop."""
        self.close_all_positions(self.config.instrument_id)
        self.unsubscribe_quote_ticks(instrument_id=self.config.instrument_id)
        self._logger.info("Strategy stopped")

    def on_quote_tick(self, tick: QuoteTick):
        """Actions to be performed on receiving a quote tick."""
        self.macd.handle_quote_tick(tick)

        if not self.macd.initialized:
            return

        self.check_for_entry()
        self.check_for_exit()

    def on_event(self, event: Event):
        """Actions to be performed on receiving an event."""
        if isinstance(event, PositionOpened):
            self.position = self.cache.position(event.position_id)
            self._logger.info(f"Position opened: {self.position}")

    def check_for_entry(self):
        """Check for entry conditions and submit orders if met."""
        if self.macd.value > self.config.entry_threshold:
            if self.position and self.position.side == PositionSide.LONG:
                return

            order = self.order_factory.market(
                instrument_id=self.config.instrument_id,
                order_side=OrderSide.BUY,
                quantity=self.trade_size,
            )
            self.submit_order(order)
            self._logger.info("Submitted BUY order")
        elif self.macd.value < -self.config.entry_threshold:
            if self.position and self.position.side == PositionSide.SHORT:
                return

            order = self.order_factory.market(
                instrument_id=self.config.instrument_id,
                order_side=OrderSide.SELL,
                quantity=self.trade_size,
            )
            self.submit_order(order)
            self._logger.info("Submitted SELL order")

    def check_for_exit(self):
        """Check for exit conditions and close positions if met."""
        if self.macd.value >= 0.0:
            if self.position and self.position.side == PositionSide.SHORT:
                self.close_position(self.position)
                self._logger.info("Closed SHORT position")
        else:
            if self.position and self.position.side == PositionSide.LONG:
                self.close_position(self.position)
                self._logger.info("Closed LONG position")


async def run_backtest(
    catalog_path: str,
    instrument_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    log_level: str = "INFO",
) -> BacktestEngine:
    """
    Run a backtest with the MACD strategy.

    Args:
        catalog_path: Path to the Parquet data catalog
        instrument_id: The instrument ID to trade
        start_time: Optional start time for the backtest
        end_time: Optional end time for the backtest
        log_level: Logging level for the backtest

    Returns:
        The backtest engine instance containing the results
    """
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    try:
        # Load data catalog
        catalog = ParquetDataCatalog(catalog_path)
        instruments = catalog.instruments()
        
        if not instruments:
            raise ValueError("No instruments found in catalog")

        # Find the requested instrument
        instrument = next((i for i in instruments if str(i.id) == instrument_id), None)
        if not instrument:
            raise ValueError(f"Instrument {instrument_id} not found in catalog")

        # Configure venue
        venue = BacktestVenueConfig(
            name="SIM",
            oms_type="NETTING",
            account_type="MARGIN",
            base_currency="USD",
            starting_balances=["1_000_000 USD"],
        )

        # Configure data
        data = BacktestDataConfig(
            catalog_path=str(catalog.path),
            data_cls=QuoteTick,
            instrument_id=instrument.id,
            start_time=start_time,
            end_time=end_time,
        )

        # Configure engine
        engine = BacktestEngineConfig(
            strategies=[
                ImportableStrategyConfig(
                    strategy_path="__main__:MACDStrategy",
                    config_path="__main__:MACDConfig",
                    config={
                        "instrument_id": instrument.id,
                        "fast_period": 12,
                        "slow_period": 26,
                    },
                )
            ],
            logging=LoggingConfig(log_level=log_level),
        )

        # Configure and run backtest
        config = BacktestRunConfig(
            engine=engine,
            venues=[venue],
            data=[data],
        )

        node = BacktestNode(configs=[config])
        results = node.run()

        if not results:
            raise RuntimeError("Backtest produced no results")

        # Get the engine for analysis
        engine = node.get_engine(config.id)
        
        # Generate reports
        logger.info("\nOrder Fills Report:")
        logger.info(engine.trader.generate_order_fills_report())
        
        logger.info("\nPositions Report:")
        logger.info(engine.trader.generate_positions_report())
        
        logger.info("\nAccount Report:")
        logger.info(engine.trader.generate_account_report(Venue("SIM")))

        return engine

    except Exception as e:
        logger.error(f"Error running backtest: {e}", exc_info=True)
        raise


app = typer.Typer(help="Run backtests using NautilusTrader.")


@app.command()
def run(
    catalog_path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Path to the Parquet data catalog",
    ),
    instrument_id: str = typer.Argument(
        ...,
        help="Instrument ID to trade (e.g., 'EUR/USD.SIM')",
    ),
    start_time: Optional[datetime] = typer.Option(
        None,
        formats=["%Y-%m-%d"],
        help="Start time for backtest (YYYY-MM-DD)",
    ),
    end_time: Optional[datetime] = typer.Option(
        None,
        formats=["%Y-%m-%d"],
        help="End time for backtest (YYYY-MM-Dd)",
    ),
    log_level: str = typer.Option(
        "INFO",
        help="Logging level",
        case_sensitive=False,
    ),
):
    """Run a backtest with the MACD strategy."""
    try:
        asyncio.run(
            run_backtest(
                catalog_path=str(catalog_path),
                instrument_id=instrument_id,
                start_time=start_time,
                end_time=end_time,
                log_level=log_level,
            )
        )
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) 