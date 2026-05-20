# XLEvsXLK

A simple two-ETF sector rotation strategy: **XLK (Technology) + XLE (Energy)**, filtered by the 200-day SMA.

- **Default:** 50% XLK + 50% XLE
- **When one ETF closes below its 200-day SMA:** rotate 100% into the other
- **Both above SMA(200):** return to 50/50
- **Both below SMA(200):** hold current allocation

No leverage, no options, no shorting. About 10 trades per year.

## Headline result (Dec 1998 – Mar 2026, 27.3 years)

| Metric | 100% SPY | 50/50 Static | **50/50 Dynamic** |
|---|---|---|---|
| Final equity ($100K start) | $525,398 | $674,295 | **$1,434,901** |
| CAGR | 6.27% | 7.25% | **10.26%** |
| Max drawdown | -56.47% | -61.50% | **-58.49%** |
| Sharpe | 0.17 | 0.17 | **0.29** |
| CAR/MDD | 0.11 | 0.12 | **0.18** |

See [`STRATEGY_BRIEF.md`](STRATEGY_BRIEF.md) for the full evidence brief, [`STRATEGY_EXPLAINER.md`](STRATEGY_EXPLAINER.md) for the long-form narrative, and [`FULL_RESEARCH_LOG.md`](FULL_RESEARCH_LOG.md) for chronological research notes.

## Repo layout

| File | Purpose |
|---|---|
| `backtest.py` | Definitive backtest engine. Next-day-open execution, slippage modeled. |
| `pairs_scan.py` | Scans all sector-ETF pairs (50/50 buy-and-hold) over a shorter window. |
| `STRATEGY_BRIEF.md` | Short evidence brief. |
| `STRATEGY_EXPLAINER.md` | Long-form explainer. |
| `FULL_RESEARCH_LOG.md` | Research log. |
| `comparison_*.png`, `test*_*.png` | Result plots. |
| `CLAUDE.md` | Notes for AI-assisted development in this repo. |

Raw and cleaned CSV data are **not** included in the repo (see `.gitignore`).

## Running

Requires Python with `pandas`, `numpy`, and `matplotlib`. The scripts read `<TICKER>_clean.csv` files from the repo root.

```bash
python backtest.py                    # run all tests
python backtest.py --test main        # main comparison only
python backtest.py --test sensitivity # buffer sensitivity
python backtest.py --test bothbroken  # alternative "both below SMA" rules
python backtest.py --test borrow      # borrow-cost impact
python backtest.py --test margin      # margin variant
python pairs_scan.py                  # scan all sector pairs
```

Data sources used in the original research: TradingView BATS daily OHLCV for SPY/XLK/XLE/XLP/GLD/TLT, plus a Databento multi-symbol export for the broader sector scan.

## Caveats

- Sector ETF composition has changed over 27 years (survivorship/reconstitution effects).
- Whipsaw risk near SMA crossovers — a confirmation filter would reduce this but add lag.
- Transaction costs not modeled (negligible at ~10 trades/year on highly liquid ETFs, but not zero).
- Past performance does not guarantee future results.

## License

No license specified — all rights reserved by default.
