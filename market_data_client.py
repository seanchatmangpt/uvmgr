"""
Market Data Client - A Databento-like interface using yfinance as the data source.

This module provides a client interface similar to Databento's API but uses yfinance
as the underlying data source. It's designed for development and testing purposes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
import pytz
import yfinance as yf
from pandas import DataFrame

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Schema(str, Enum):
    """Supported data schemas (matching Databento's schemas)."""
    OHLCV_1M = "ohlcv-1m"  # 1-minute bars
    OHLCV_5M = "ohlcv-5m"  # 5-minute bars
    OHLCV_15M = "ohlcv-15m"  # 15-minute bars
    OHLCV_1H = "ohlcv-1h"  # 1-hour bars
    OHLCV_1D = "ohlcv-1d"  # 1-day bars

class SymbolType(str, Enum):
    """Symbology types (matching Databento's stypes)."""
    RAW_SYMBOL = "raw_symbol"  # Original string symbols (e.g., AAPL)
    INSTRUMENT_ID = "instrument_id"  # Unique numeric IDs
    PARENT = "parent"  # Groups related symbols (e.g., ES.FUT)
    CONTINUOUS = "continuous"  # References instruments that change over time
    ALL_SYMBOLS = "ALL_SYMBOLS"  # All symbols in dataset

@dataclass
class Instrument:
    """Represents a trading instrument (similar to Databento's instrument definitions)."""
    symbol: str
    stype: SymbolType
    asset_class: str = "EQUITY"  # EQUITY, FUTURE, OPTION, etc.
    currency: str = "USD"
    price_precision: int = 2
    size_precision: int = 0
    price_increment: Decimal = Decimal("0.01")
    size_increment: Decimal = Decimal("1")
    lot_size: Decimal = Decimal("1")
    max_quantity: Decimal = Decimal("1000000")
    min_quantity: Decimal = Decimal("1")
    margin_init: Decimal = Decimal("0.5")
    margin_maint: Decimal = Decimal("0.5")
    maker_fee: Decimal = Decimal("0.0")
    taker_fee: Decimal = Decimal("0.0")

@dataclass
class DBNStore:
    """A class that mimics Databento's DBNStore for storing market data."""
    
    schema: Schema
    data: DataFrame
    instrument: Optional[Instrument] = None
    
    @classmethod
    def from_dataframe(cls, df: DataFrame, schema: Schema, instrument: Optional[Instrument] = None) -> DBNStore:
        """Create a DBNStore from a pandas DataFrame."""
        return cls(schema=schema, data=df.copy(), instrument=instrument)
    
    def to_df(self) -> DataFrame:
        """Convert to pandas DataFrame."""
        return self.data.copy()
    
    def to_csv(self, path: Union[str, Path]) -> None:
        """Write data to CSV file."""
        self.data.to_csv(path, index=False)
        logger.info(f"Data written to CSV: {path}")
    
    def to_json(self, path: Union[str, Path]) -> None:
        """Write data to JSON file."""
        self.data.to_json(path, orient='records', date_format='iso')
        logger.info(f"Data written to JSON: {path}")
    
    def to_parquet(self, path: Union[str, Path]) -> None:
        """Write data to Parquet file."""
        self.data.to_parquet(path, index=False)
        logger.info(f"Data written to Parquet: {path}")
    
    def to_file(self, path: Union[str, Path]) -> None:
        """Write data to a compressed pickle file (simulating DBN format)."""
        # Store schema and instrument with the data
        data_with_meta = {
            'schema': self.schema.value,
            'instrument': self.instrument,
            'data': self.data
        }
        pd.to_pickle(data_with_meta, path, compression='zstd')
        logger.info(f"Data written to compressed file: {path}")
    
    @classmethod
    def from_file(cls, path: Union[str, Path]) -> DBNStore:
        """Read data from a compressed pickle file."""
        data_with_meta = pd.read_pickle(path, compression='zstd')
        schema = Schema(data_with_meta['schema'])
        instrument = data_with_meta.get('instrument')
        return cls(schema=schema, data=data_with_meta['data'], instrument=instrument)
    
    def __iter__(self):
        """Iterate over records in the store."""
        for _, row in self.data.iterrows():
            yield row

class MarketDataClient:
    """A client that simulates Databento's functionality using yfinance."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the market data client.
        
        Args:
            api_key: Optional API key (not used with yfinance, but kept for API compatibility)
        """
        self.api_key = api_key
        logger.info("MarketDataClient initialized")
    
    def get_range(
        self,
        symbols: List[str],
        schema: Union[str, Schema],
        start: Union[str, datetime],
        end: Union[str, datetime],
        stype_in: Union[str, SymbolType] = SymbolType.RAW_SYMBOL,
        **kwargs: Any
    ) -> DBNStore:
        """
        Get historical market data for the specified symbols and time range.
        
        Args:
            symbols: List of symbols to fetch data for
            schema: Data schema (e.g., "ohlcv-1m", "ohlcv-1h")
            start: Start time (inclusive)
            end: End time (exclusive)
            stype_in: Symbol type (default: raw_symbol)
            **kwargs: Additional arguments passed to yfinance
            
        Returns:
            DBNStore containing the requested data
        """
        if stype_in not in [SymbolType.RAW_SYMBOL, SymbolType.ALL_SYMBOLS]:
            raise ValueError("Only 'raw_symbol' and 'ALL_SYMBOLS' are supported for yfinance data")
        
        schema = Schema(schema) if isinstance(schema, str) else schema
        stype_in = SymbolType(stype_in) if isinstance(stype_in, str) else stype_in
        
        # Convert string dates to datetime if needed
        if isinstance(start, str):
            start = pd.to_datetime(start)
        if isinstance(end, str):
            end = pd.to_datetime(end)
        
        # Map schema to yfinance interval
        interval_map = {
            Schema.OHLCV_1M: "1m",
            Schema.OHLCV_5M: "5m",
            Schema.OHLCV_15M: "15m",
            Schema.OHLCV_1H: "1h",
            Schema.OHLCV_1D: "1d"
        }
        
        interval = interval_map[schema]
        
        try:
            # Fetch data from yfinance
            data = yf.download(
                symbols,
                start=start,
                end=end,
                interval=interval,
                group_by='ticker',
                **kwargs
            )
            
            # Process the data to match Databento's format
            if len(symbols) == 1:
                # Single symbol case
                if isinstance(data.columns, pd.MultiIndex):
                    # Flatten MultiIndex columns: ('AAPL', 'Open') -> 'AAPL_Open'
                    data.columns = [f"{c[0]}_{c[1]}" if c[1] else c[0] for c in data.columns.values]
                df = data.reset_index()
                # Rename columns like 'AAPL_Open' to 'open', etc.
                symbol = symbols[0]
                rename_map = {
                    f"{symbol}_Open": "open",
                    f"{symbol}_High": "high",
                    f"{symbol}_Low": "low",
                    f"{symbol}_Close": "close",
                    f"{symbol}_Volume": "volume",
                    'Datetime': 'ts_event',
                    'Date': 'ts_event',
                }
                df = df.rename(columns=rename_map)
                df['symbol'] = symbol
            else:
                # Multiple symbols case
                dfs = []
                for symbol in symbols:
                    if isinstance(data.columns, pd.MultiIndex):
                        symbol_data = data[symbol].reset_index()
                        # Rename columns to match Databento format
                        rename_map = {
                            'Open': 'open',
                            'High': 'high',
                            'Low': 'low',
                            'Close': 'close',
                            'Volume': 'volume',
                            'Datetime': 'ts_event',
                            'Date': 'ts_event',
                        }
                        symbol_data = symbol_data.rename(columns=rename_map)
                        symbol_data['symbol'] = symbol
                        dfs.append(symbol_data)
                df = pd.concat(dfs, ignore_index=True)
            
            logger.info(f"Fetched DataFrame shape: {df.shape}, columns: {list(df.columns)}")
            if df.empty:
                logger.error("Fetched DataFrame is empty. No data returned from yfinance.")
                raise ValueError("No data returned from yfinance for the given symbol and date range.")
            
            # Ensure ts_event is datetime
            df['ts_event'] = pd.to_datetime(df['ts_event'])
            
            # Add required Databento-like columns
            df['rtype'] = 34  # Simulating Databento's rtype for OHLCV
            df['publisher_id'] = 1  # Simulating Databento's publisher_id
            df['instrument_id'] = range(1, len(df) + 1)  # Simulating instrument_id
            
            # Create instrument definition
            instrument = Instrument(
                symbol=symbols[0] if len(symbols) == 1 else "MULTI",
                stype=stype_in,
                asset_class="EQUITY",
                currency="USD"
            )
            
            # Reorder columns to match Databento's format
            columns = ['ts_event', 'rtype', 'publisher_id', 'instrument_id', 
                      'open', 'high', 'low', 'close', 'volume', 'symbol']
            df = df[columns]
            
            return DBNStore(schema=schema, data=df, instrument=instrument)
            
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            raise
    
    def get_cost(
        self,
        symbols: List[str],
        schema: Union[str, Schema],
        start: Union[str, datetime],
        end: Union[str, datetime],
        **kwargs: Any
    ) -> float:
        """
        Simulate getting the cost of data (always returns 0 for yfinance).
        
        Args:
            symbols: List of symbols
            schema: Data schema
            start: Start time
            end: End time
            **kwargs: Additional arguments
            
        Returns:
            float: Always returns 0 since yfinance is free
        """
        return 0.0

def main():
    """Example usage of the MarketDataClient."""
    # Initialize client
    client = MarketDataClient()
    
    # Example parameters
    symbols = ["AAPL", "MSFT"]
    schema = Schema.OHLCV_1H
    start = "2024-01-01"
    end = "2024-01-05"
    
    try:
        # Get data
        data = client.get_range(
            symbols=symbols,
            schema=schema,
            start=start,
            end=end
        )
        
        # Convert to DataFrame and display
        df = data.to_df()
        print(f"\nRetrieved {len(df)} records")
        print("\nFirst few records:")
        print(df.head())
        
        # Save to different formats
        base_path = f"market_data_{start}_{end}"
        data.to_csv(f"{base_path}.csv")
        data.to_json(f"{base_path}.json")
        data.to_parquet(f"{base_path}.parquet")
        data.to_file(f"{base_path}.dbn.zst")
        
        # Load from saved file
        loaded_data = DBNStore.from_file(f"{base_path}.dbn.zst")
        print("\nLoaded data from file:")
        print(loaded_data.to_df().head())
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main() 