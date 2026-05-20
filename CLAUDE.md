# XLEvsXLK

Backtest research for a simple sector-rotation strategy: 50/50 XLK (Technology) + XLE (Energy) with a 200-day SMA regime filter. When one ETF closes below its SMA(200), the system rotates 100% into the other. See `STRATEGY_BRIEF.md` for the full thesis and headline results.

## Layout

- `backtest.py` — definitive backtest engine. Loads `*_clean.csv` files, runs rotation/static/buy-and-hold variants, prints metrics, and writes PNG comparison plots. Uses next-day-open execution and applies slippage.
- `pairs_scan.py` — scans all sector-ETF pairs (50/50 buy-and-hold) over the shorter Databento window to check whether the XLK/XLE result is special.
- `STRATEGY_BRIEF.md` — short evidence brief (results table, "why it works", caveats).
- `STRATEGY_EXPLAINER.md` — longer narrative explainer.
- `FULL_RESEARCH_LOG.md` — chronological notes from the research process.
- `*_clean.csv` — cleaned per-ticker OHLCV used by `backtest.py` (date, open, high, low, close, volume).
- `BATS_*.csv` — raw TradingView exports; not consumed directly by the scripts.
- `xnas-itch-*.csv` — Databento multi-symbol export consumed by `pairs_scan.py`.
- `comparison_*.png`, `test*_*.png` — generated plots from backtest runs.

All CSV data is gitignored — the repo ships code and write-ups only.

## Running

Requires the local `.venv` (pandas, numpy, matplotlib).

```
python backtest.py                    # all tests
python backtest.py --test main        # main comparison only
python backtest.py --test sensitivity # buffer sensitivity
python backtest.py --test bothbroken  # alternative both-below-SMA rules
python backtest.py --test borrow      # borrow-cost impact
python backtest.py --test margin      # margin variant
python pairs_scan.py                  # scan all sector pairs
```

## Conventions

- Data files use lowercase column names (`date, open, high, low, close, volume`); the loader coerces numerics and aligns multi-ticker frames on common dates.
- Backtests start with `INITIAL_CAPITAL = 100_000` and apply `SLIPPAGE_PCT = 0.0005` per trade.
- The SMA period (200) is treated as fixed, not tuned — keep it that way unless explicitly testing sensitivity.
- New data files should be added as `<TICKER>_clean.csv` so `load_etf("XYZ")` picks them up automatically.
