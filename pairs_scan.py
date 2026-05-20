#!/usr/bin/env python3
"""
Sector Pairs Scanner — 50/50 Buy-and-Hold vs SPY

Tests all possible pairs of sector ETFs with a simple 50/50 static allocation
vs SPY over the common data period (May 2018 – Mar 2026).

Sectors from Databento: XLB, XLC, XLF, XLI, XLP, XLRE, XLU, XLV, XLY
Plus from existing clean data: XLK, XLE
"""

import numpy as np
import pandas as pd
from pathlib import Path
from itertools import combinations

DATA_DIR = Path(__file__).parent
INITIAL_CAPITAL = 100_000.0


def load_databento() -> dict[str, pd.DataFrame]:
    """Load all sector ETFs from the Databento CSV."""
    path = DATA_DIR / "xnas-itch-20180501-20260327.ohlcv-1d.csv"
    raw = pd.read_csv(path)
    raw["date"] = pd.to_datetime(raw["ts_event"]).dt.tz_localize(None).dt.normalize()

    etfs = {}
    for sym in raw["symbol"].unique():
        df = raw[raw["symbol"] == sym][["date", "open", "high", "low", "close", "volume"]].copy()
        df = df.sort_values("date").drop_duplicates("date").set_index("date")
        for col in ["open", "high", "low", "close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        etfs[sym] = df

    return etfs


def load_clean_etf(ticker: str) -> pd.DataFrame:
    """Load from existing clean CSVs."""
    path = DATA_DIR / f"{ticker}_clean.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.sort_values("date").set_index("date")
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def calc_metrics(equity: pd.Series) -> dict:
    """Calculate CAGR, max drawdown, Sharpe, volatility."""
    years = len(equity) / 252
    if years <= 0 or equity.iloc[0] <= 0:
        return {"cagr": 0, "max_dd": 0, "sharpe": 0, "vol": 0, "final": 0}

    final = equity.iloc[-1]
    cagr = (final / equity.iloc[0]) ** (1 / years) - 1

    peak = equity.cummax()
    dd = (equity - peak) / peak
    max_dd = dd.min()

    rets = equity.pct_change().dropna()
    vol = rets.std() * np.sqrt(252)
    sharpe = (rets.mean() / rets.std() * np.sqrt(252)) if rets.std() > 0 else 0

    return {"cagr": cagr, "max_dd": max_dd, "sharpe": sharpe, "vol": vol, "final": final}


def run_5050_buyhold(df_a: pd.DataFrame, df_b: pd.DataFrame) -> pd.Series:
    """50/50 buy-and-hold, no rebalancing."""
    alloc = INITIAL_CAPITAL / 2
    shares_a = alloc / df_a.iloc[0]["close"]
    shares_b = alloc / df_b.iloc[0]["close"]
    return shares_a * df_a["close"] + shares_b * df_b["close"]


def main():
    # Load all ETFs
    print("Loading data...")
    etfs = load_databento()

    # Add XLK and XLE from clean CSVs (trim to Databento period)
    for ticker in ["XLK", "XLE", "SPY"]:
        clean = load_clean_etf(ticker)
        if clean is not None:
            # Ensure index is datetime without timezone
            clean.index = pd.to_datetime(clean.index).normalize()
            etfs[ticker] = clean

    all_sectors = sorted([s for s in etfs.keys() if s != "SPY"])
    print(f"Sectors: {', '.join(all_sectors)} ({len(all_sectors)} total)")

    # Find common date range across ALL sectors + SPY
    common_dates = etfs["SPY"].index
    for sym in all_sectors:
        common_dates = common_dates.intersection(etfs[sym].index)
    common_dates = common_dates.sort_values()

    print(f"Common period: {common_dates[0].date()} to {common_dates[-1].date()}")
    print(f"Trading days: {len(common_dates)}")

    # Trim all to common dates
    spy = etfs["SPY"].loc[common_dates]
    sector_data = {sym: etfs[sym].loc[common_dates] for sym in all_sectors}

    # SPY benchmark
    spy_shares = INITIAL_CAPITAL / spy.iloc[0]["close"]
    spy_equity = spy_shares * spy["close"]
    spy_m = calc_metrics(spy_equity)

    print(f"\n{'='*90}")
    print(f"  ALL SECTOR PAIRS — 50/50 Buy-and-Hold vs SPY")
    print(f"  Period: {common_dates[0].date()} to {common_dates[-1].date()}")
    print(f"{'='*90}")
    print(f"\n{'Pair':<12} {'Final($)':<12} {'CAGR':<8} {'MaxDD':<9} {'Sharpe':<8} {'Vol':<8} {'vs SPY CAGR':<12}")
    print("-" * 75)

    # SPY baseline
    print(f"{'SPY':<12} ${spy_m['final']:>9,.0f}  {spy_m['cagr']:>6.2%}  {spy_m['max_dd']:>7.2%}  {spy_m['sharpe']:>6.2f}  {spy_m['vol']:>6.2%}  {'baseline':<12}")
    print("-" * 75)

    results = []
    for a, b in combinations(all_sectors, 2):
        equity = run_5050_buyhold(sector_data[a], sector_data[b])
        m = calc_metrics(equity)
        excess = m["cagr"] - spy_m["cagr"]
        results.append((a, b, m, excess))

    # Sort by CAGR descending
    results.sort(key=lambda x: x[2]["cagr"], reverse=True)

    for a, b, m, excess in results:
        sign = "+" if excess >= 0 else ""
        pair = f"{a}/{b}"
        print(f"{pair:<12} ${m['final']:>9,.0f}  {m['cagr']:>6.2%}  {m['max_dd']:>7.2%}  {m['sharpe']:>6.2f}  {m['vol']:>6.2%}  {sign}{excess:>5.2%}")

    # Highlight key findings
    print(f"\n{'='*90}")
    print(f"  TOP 10 PAIRS BY SHARPE RATIO")
    print(f"{'='*90}")

    by_sharpe = sorted(results, key=lambda x: x[2]["sharpe"], reverse=True)
    print(f"\n{'Pair':<12} {'CAGR':<8} {'MaxDD':<9} {'Sharpe':<8} {'Vol':<8}")
    print("-" * 45)
    for a, b, m, _ in by_sharpe[:10]:
        pair = f"{a}/{b}"
        print(f"{pair:<12} {m['cagr']:>6.2%}  {m['max_dd']:>7.2%}  {m['sharpe']:>6.2f}  {m['vol']:>6.2%}")

    # How does XLK/XLE rank?
    print(f"\n{'='*90}")
    print(f"  WHERE DOES XLK/XLE RANK?")
    print(f"{'='*90}")

    by_cagr = sorted(results, key=lambda x: x[2]["cagr"], reverse=True)
    for rank, (a, b, m, _) in enumerate(by_cagr, 1):
        if (a == "XLE" and b == "XLK") or (a == "XLK" and b == "XLE"):
            print(f"  By CAGR: #{rank} of {len(results)}")
            break

    by_sharpe_rank = sorted(results, key=lambda x: x[2]["sharpe"], reverse=True)
    for rank, (a, b, m, _) in enumerate(by_sharpe_rank, 1):
        if (a == "XLE" and b == "XLK") or (a == "XLK" and b == "XLE"):
            print(f"  By Sharpe: #{rank} of {len(results)}")
            break

    by_dd = sorted(results, key=lambda x: x[2]["max_dd"], reverse=False)
    for rank, (a, b, m, _) in enumerate(by_dd, 1):
        if (a == "XLE" and b == "XLK") or (a == "XLK" and b == "XLE"):
            print(f"  By Max DD (best = smallest): #{rank} of {len(results)}")
            break

    # Count how many pairs beat SPY
    beat_spy = sum(1 for _, _, m, _ in results if m["cagr"] > spy_m["cagr"])
    total = len(results)
    print(f"\n  Pairs that beat SPY on CAGR: {beat_spy}/{total} ({beat_spy/total:.0%})")

    beat_spy_sharpe = sum(1 for _, _, m, _ in results if m["sharpe"] > spy_m["sharpe"])
    print(f"  Pairs that beat SPY on Sharpe: {beat_spy_sharpe}/{total} ({beat_spy_sharpe/total:.0%})")


if __name__ == "__main__":
    main()
