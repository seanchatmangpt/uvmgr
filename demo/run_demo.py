#!/usr/bin/env python3
"""
Nautilus Trader Nanosecond Performance Demo - Real API Version
Perfect for Y Combinator Demo Day!

Uses actual Nautilus Trader components like the official examples.
"""

import time
from decimal import Decimal
from typing import List

import numpy as np
import pandas as pd


def main():
    print("🚀 Nautilus Trader Nanosecond Performance Demo")
    print("Using REAL Nautilus components (not simulated)")
    print("=" * 50)

    # Import real Nautilus components
    try:
        from nautilus_trader.core.datetime import dt_to_unix_nanos
        from nautilus_trader.model.data import QuoteTick
        from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
        from nautilus_trader.model.objects import Price, Quantity
        from nautilus_trader.test_kit.providers import TestInstrumentProvider
        print("✅ Real Nautilus Trader components imported!")
    except ImportError:
        print("❌ Nautilus Trader not found. Installing...")
        import subprocess
        subprocess.run(["pip", "install", "nautilus_trader"], check=True)
        print("✅ Installation complete! Please run again.")
        return

    # Configuration using real instruments
    NUM_ITERATIONS = 1000
    BTCUSDT = TestInstrumentProvider.btcusdt_binance()

    print("📊 Configuration:")
    print(f"   • Iterations: {NUM_ITERATIONS:,}")
    print(f"   • Instrument: {BTCUSDT.id}")
    print("   • Using: QuoteTick, Price, Quantity, dt_to_unix_nanos")

    # Run benchmark with real components
    latencies = benchmark_real_nautilus(NUM_ITERATIONS, BTCUSDT)

    # Calculate stats
    stats = calculate_stats(latencies)

    # Display results
    print("\n🏆 REAL NAUTILUS COMPONENT PERFORMANCE")
    print("=" * 50)
    print(f"⚡ Minimum Latency:     {stats['min_ns']:.0f} ns")
    print(f"📊 Average Latency:     {stats['mean_ns']:.0f} ns")
    print(f"📈 Maximum Latency:     {stats['max_ns']:.0f} ns")
    print(f"🎯 95th Percentile:     {stats['p95_ns']:.0f} ns")
    print(f"🚀 Operations/Second:   {stats['operations_per_second']:,.0f}")

    print("\n💎 REAL Components Used:")
    print("   • TestInstrumentProvider.btcusdt_binance()")
    print("   • Price.from_str() with nanosecond precision")
    print("   • Quantity.from_str() for position sizing")
    print("   • QuoteTick with real timestamps")
    print("   • dt_to_unix_nanos() for time conversion")

    print("\n🎉 Demo complete! Real Nautilus performance!")

def benchmark_real_nautilus(num_iterations: int, instrument) -> list[float]:
    """Benchmark using REAL Nautilus Trader components"""
    from nautilus_trader.core.datetime import dt_to_unix_nanos
    from nautilus_trader.model.data import QuoteTick
    from nautilus_trader.model.objects import Price, Quantity

    latencies = []
    print("🔥 Benchmarking REAL Nautilus components...")

    for i in range(num_iterations):
        start_ns = time.perf_counter_ns()

        # REAL Nautilus component usage (matching the Binance example pattern)
        bid_price = Price.from_str("20145.50")  # Real Price object
        ask_price = Price.from_str("20146.00")  # Real Price object
        bid_size = Quantity.from_str("1.250")   # Real Quantity object
        ask_size = Quantity.from_str("0.875")   # Real Quantity object

        # Create REAL QuoteTick (like Binance example)
        current_time_ns = time.time_ns()
        quote_tick = QuoteTick(
            instrument_id=instrument.id,  # Real instrument ID
            bid_price=bid_price,
            ask_price=ask_price,
            bid_size=bid_size,
            ask_size=ask_size,
            ts_event=current_time_ns,
            ts_init=current_time_ns
        )

        # Real trading calculations
        spread = float(ask_price) - float(bid_price)
        mid_price = (float(bid_price) + float(ask_price)) / 2

        # Order book imbalance (like OrderBookImbalance strategy)
        total_bid = float(bid_size)
        total_ask = float(ask_size)
        imbalance = (total_bid - total_ask) / (total_bid + total_ask)

        # Real timestamp conversion
        event_time = dt_to_unix_nanos(pd.Timestamp.now(tz="UTC"))

        end_ns = time.perf_counter_ns()
        latencies.append(end_ns - start_ns)

        if (i + 1) % 200 == 0:
            print(f"   ⚡ Completed {i+1:,} iterations with real components")

    return latencies

def calculate_stats(latencies: list[float]) -> dict:
    """Calculate performance statistics"""
    latencies_array = np.array(latencies)
    return {
        "min_ns": np.min(latencies_array),
        "max_ns": np.max(latencies_array),
        "mean_ns": np.mean(latencies_array),
        "p95_ns": np.percentile(latencies_array, 95),
        "operations_per_second": 1_000_000_000 / np.mean(latencies_array)
    }

if __name__ == "__main__":
    main()
