#!/usr/bin/env python3
"""Run a NautilusTrader backtest with EMA cross strategy using the high-level API."""

import asyncio
import logging
import shutil
from decimal import Decimal
from datetime import datetime
from pathlib import Path

import pandas as pd

from nautilus_trader.backtest.node import (
    BacktestDataConfig,
    BacktestEngineConfig,
    BacktestNode,
    BacktestRunConfig,
    BacktestVenueConfig,
)
from nautilus_trader.config import ImportableStrategyConfig, LoggingConfig
from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.model import QuoteTick, Venue
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.persistence.wranglers import QuoteTickDataWrangler
from nautilus_trader.test_kit.providers import CSVTickDataLoader, TestInstrumentProvider


async def load_data_to_catalog(
    data_dir: str | Path,
    catalog_path: str | Path,
    instrument_id: str = "EUR/USD",
) -> ParquetDataCatalog:
    """
    Load FX data from CSV files into a Parquet data catalog.

    Args:
        data_dir: Directory containing the CSV data files
        catalog_path: Path where the catalog will be created
        instrument_id: The instrument ID to use

    Returns:
        The created ParquetDataCatalog instance
    """
    logger = logging.getLogger(__name__)
    path = Path(data_dir).expanduser()
    raw_files = list(path.glob("DAT_ASCII_*.csv"))
    
    if not raw_files:
        raise ValueError(f"No histdata files found in {path}")

    # Clear existing catalog if it exists
    catalog_path = Path(catalog_path)
    if catalog_path.exists():
        shutil.rmtree(catalog_path)
    catalog_path.mkdir(parents=True)

    # Create catalog instance
    catalog = ParquetDataCatalog(catalog_path)
    
    # Create instrument
    instrument = TestInstrumentProvider.default_fx_ccy(instrument_id)
    catalog.write_data([instrument])
    
    # Process and write each file
    wrangler = QuoteTickDataWrangler(instrument)
    total_ticks = 0
    
    for file_path in raw_files:
        logger.info(f"Processing {file_path.name}")
        
        # Load CSV data
        df = CSVTickDataLoader.load(
            file_path=file_path,
            index_col=0,
            header=None,
            names=["timestamp", "bid_price", "ask_price", "volume"],
            usecols=["timestamp", "bid_price", "ask_price"],
            parse_dates=["timestamp"],
            date_format="%Y%m%d %H%M%S%f",
        )
        
        # Sort by timestamp
        df = df.sort_index()
        
        # Process quotes
        ticks = wrangler.process(df)
        catalog.write_data(ticks)
        total_ticks += len(ticks)
        
        logger.info(f"Loaded {len(ticks)} ticks from {file_path.name}")
    
    logger.info(f"Total ticks loaded: {total_ticks}")
    return catalog


async def run_backtest(
    catalog_path: str | Path,
    instrument_id: str = "EUR/USD",
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    log_level: str = "INFO",
) -> BacktestNode:
    """
    Run a backtest with the EMA cross strategy.

    Args:
        catalog_path: Path to the Parquet data catalog
        instrument_id: The instrument ID to trade
        start_time: Optional start time for the backtest
        end_time: Optional end time for the backtest
        log_level: Logging level for the backtest

    Returns:
        The backtest node instance containing the results
    """
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    try:
        # Load catalog
        catalog = ParquetDataCatalog(catalog_path)
        instruments = catalog.instruments()
        
        if not instruments:
            raise ValueError("No instruments found in catalog")

        # Find the requested instrument
        instrument = next((i for i in instruments if str(i.id) == f"{instrument_id}.SIM"), None)
        if not instrument:
            raise ValueError(f"Instrument {instrument_id} not found in catalog")

        # Convert times to nanos if provided
        start_nanos = dt_to_unix_nanos(pd.Timestamp(start_time, tz="UTC")) if start_time else None
        end_nanos = dt_to_unix_nanos(pd.Timestamp(end_time, tz="UTC")) if end_time else None

        # Configure venue
        venue_config = BacktestVenueConfig(
            name="SIM",
            oms_type="HEDGING",
            account_type="MARGIN",
            base_currency="USD",
            starting_balances=["1_000_000 USD"],
        )

        # Configure data
        data_config = BacktestDataConfig(
            catalog_path=str(catalog.path),
            data_cls=QuoteTick,
            instrument_id=instrument.id,
            start_time=start_nanos,
            end_time=end_nanos,
        )

        # Configure strategy
        strategy_config = ImportableStrategyConfig(
            strategy_path="nautilus_trader.examples.strategies.ema_cross:EMACross",
            config_path="nautilus_trader.examples.strategies.ema_cross:EMACrossConfig",
            config={
                "instrument_id": instrument.id,
                "bar_type": f"{instrument_id}.SIM-15-MINUTE-BID-INTERNAL",
                "fast_ema_period": 10,
                "slow_ema_period": 20,
                "trade_size": Decimal(1_000_000),
            },
        )

        # Configure engine
        engine_config = BacktestEngineConfig(
            strategies=[strategy_config],
            logging=LoggingConfig(log_level=log_level),
        )

        # Configure and run backtest
        config = BacktestRunConfig(
            engine=engine_config,
            venues=[venue_config],
            data=[data_config],
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
        logger.info(engine.trader.generate_account_report(Venue(venue_config.name)))

        return node

    except Exception as e:
        logger.error(f"Error running backtest: {e}", exc_info=True)
        raise


async def main():
    """Run the EMA cross strategy backtest with sample data."""
    # First, load data into catalog
    catalog = await load_data_to_catalog(
        data_dir="~/Downloads/Data/HISTDATA_COM_ASCII_EURUSD_T202410",
        catalog_path="./catalog",
        instrument_id="EUR/USD",
    )
    
    # Then run the backtest
    await run_backtest(
        catalog_path="./catalog",
        instrument_id="EUR/USD",
        start_time=datetime(2024, 10, 1),
        end_time=datetime(2024, 10, 15),
        log_level="INFO",
    )


if __name__ == "__main__":
    asyncio.run(main()) 