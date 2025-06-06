#!/usr/bin/env python3
"""
Run a NautilusTrader backtest using yfinance (via market_data_client.py) as the data source.
This script fetches data, saves it as Parquet, loads it into a ParquetDataCatalog, and runs an EMA cross backtest.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import asyncio
import logging
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
from nautilus_trader.test_kit.providers import TestInstrumentProvider

from market_data_client import MarketDataClient, Schema

async def fetch_and_save_yf_data(
    symbols: list[str],
    schema: Schema,
    start: str,
    end: str,
    parquet_path: str | Path,
    instrument_id: str = "AAPL",
) -> Path:
    """
    Fetch data from yfinance and save as Parquet for Nautilus Trader.
    """
    client = MarketDataClient()
    data = client.get_range(symbols=symbols, schema=schema, start=start, end=end)
    df = data.to_df()
    # Nautilus expects a certain format; for demo, just save as Parquet
    df.to_parquet(parquet_path, index=False)
    return Path(parquet_path)

async def run_backtest_with_yf_data():
    # Settings
    symbols = ["AAPL"]
    schema = Schema.OHLCV_1H
    start = "2024-01-01"
    end = "2024-01-10"
    instrument_id = "AAPL"
    parquet_path = "./yf_data.parquet"
    catalog_path = "./yf_catalog"

    # Fetch and save data
    print("Fetching yfinance data and saving as Parquet...")
    await fetch_and_save_yf_data(symbols, schema, start, end, parquet_path, instrument_id)

    # Prepare catalog
    print("Preparing Nautilus Trader ParquetDataCatalog...")
    catalog_path = Path(catalog_path)
    if catalog_path.exists():
        import shutil
        shutil.rmtree(catalog_path)
    catalog_path.mkdir(parents=True)
    catalog = ParquetDataCatalog(catalog_path)

    # Create instrument
    instrument = TestInstrumentProvider.default_equity(instrument_id)
    catalog.write_data([instrument])

    # Load and write ticks (simulate QuoteTicks from OHLCV bars)
    df = pd.read_parquet(parquet_path)
    ticks = []
    for _, row in df.iterrows():
        # Use 'open' as the tick price for simplicity
        tick = QuoteTick(
            instrument_id=instrument.id,
            bid_price=Decimal(str(row['open'])),
            ask_price=Decimal(str(row['open'])),
            bid_size=Decimal("100"),
            ask_size=Decimal("100"),
            ts_event=dt_to_unix_nanos(pd.Timestamp(row['ts_event'], tz="UTC")),
            ts_recv=dt_to_unix_nanos(pd.Timestamp(row['ts_event'], tz="UTC")),
        )
        ticks.append(tick)
    catalog.write_data(ticks)

    # Backtest config
    start_time = dt_to_unix_nanos(pd.Timestamp(start, tz="UTC"))
    end_time = dt_to_unix_nanos(pd.Timestamp(end, tz="UTC"))
    log_level = "INFO"

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

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
        start_time=start_time,
        end_time=end_time,
    )

    # Configure strategy (EMA cross)
    strategy_config = ImportableStrategyConfig(
        strategy_path="nautilus_trader.examples.strategies.ema_cross:EMACross",
        config_path="nautilus_trader.examples.strategies.ema_cross:EMACrossConfig",
        config={
            "instrument_id": instrument.id,
            "bar_type": f"{instrument_id}.SIM-1-HOUR-BID-INTERNAL",
            "fast_ema_period": 10,
            "slow_ema_period": 20,
            "trade_size": Decimal(100),
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

if __name__ == "__main__":
    asyncio.run(run_backtest_with_yf_data()) 