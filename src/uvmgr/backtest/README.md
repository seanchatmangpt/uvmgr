# Zen+Nautilus Backtest Implementation

This module implements a robust backtesting framework that combines Zen Engine's DMN-based decision making with NautilusTrader's execution capabilities, following Ernest Chan's methodology.

## Architecture

The implementation follows a clean separation of concerns:

1. **Zen Engine (DMN)**: Handles decision logic through explicit, transparent rules
2. **NautilusTrader**: Manages market data, order execution, and backtesting environment
3. **Integration Layer**: Connects Zen Engine decisions to NautilusTrader execution

## Components

### 1. Strategy Implementation (`zen_chan_strategy.py`)

The `ZenChanStrategy` class implements the core strategy logic:
- Integrates with Zen Engine for decision making
- Calculates features (volatility, gaps, etc.)
- Executes trades based on DMN decisions
- Manages position and risk

### 2. Backtest Runner (`run_chan_zen_backtest.py`)

A robust command-line tool for running backtests:
- Configurable through command-line arguments
- Handles data loading and engine setup
- Generates detailed performance reports
- Saves results for analysis

### 3. DMN Rules (`zen_rules/`)

Contains DMN files defining trading rules:
- `buy_on_gap.dmn`: Implements Ernest Chan's buy-on-gap strategy
- Additional rules can be added following the same pattern

## Usage

### Prerequisites

1. Install dependencies:
```bash
pip install nautilus-trader zen-engine pandas numpy
```

2. Prepare market data in NautilusTrader format

### Running a Backtest

```bash
python -m uvmgr.backtest.run_chan_zen_backtest \
    --data-path /path/to/market/data \
    --instrument AAPL \
    --venue NASDAQ \
    --start-date 2023-01-01 \
    --end-date 2023-12-31 \
    --dmn-path src/uvmgr/backtest/zen_rules/buy_on_gap.dmn \
    --trade-size 100.0 \
    --volatility-lookback 90 \
    --initial-capital 100000.0 \
    --log-level INFO
```

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--data-path` | Path to market data directory | (required) |
| `--instrument` | Instrument symbol to trade | AAPL |
| `--venue` | Trading venue | NASDAQ |
| `--start-date` | Backtest start date (YYYY-MM-DD) | (required) |
| `--end-date` | Backtest end date (YYYY-MM-DD) | (required) |
| `--dmn-path` | Path to DMN rules file | (required) |
| `--trade-size` | Base trade size in units | 100.0 |
| `--volatility-lookback` | Days for volatility calculation | 90 |
| `--initial-capital` | Starting capital in USD | 100000.0 |
| `--log-level` | Logging level | INFO |

### Output

The backtest generates:
1. Console output with key performance metrics
2. Detailed CSV report in `reports/zen_chan_backtest_YYYYMMDD_HHMMSS.csv`

## Creating Custom DMN Rules

1. Create a new `.dmn` file in `zen_rules/`
2. Define decision tables following the DMN specification
3. Use the same input/output structure as `buy_on_gap.dmn`
4. Reference the new DMN file in the backtest command

Example DMN structure:
```xml
<decision id="StrategyDecision" name="Strategy Decision">
  <decisionTable hitPolicy="UNIQUE">
    <input id="Input_1" label="Feature1">
      <inputExpression typeRef="number">
        <text>Feature1</text>
      </inputExpression>
    </input>
    <output id="Output_1" label="Action" typeRef="string"/>
    <rule>
      <inputEntry><text>condition</text></inputEntry>
      <outputEntry><text>"BUY"</text></outputEntry>
    </rule>
  </decisionTable>
</decision>
```

## Best Practices

1. **DMN Rules**:
   - Keep rules simple and explicit
   - Document rule logic in comments
   - Use meaningful names for inputs/outputs
   - Test rules independently before backtesting

2. **Strategy Implementation**:
   - Add proper error handling
   - Log important events
   - Validate inputs and state
   - Follow NautilusTrader best practices

3. **Backtesting**:
   - Start with small date ranges
   - Use appropriate data granularity
   - Monitor memory usage
   - Save and analyze results

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Use type hints and docstrings

## License

This implementation is provided under the MIT License. 