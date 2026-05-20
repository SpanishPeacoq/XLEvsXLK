# XLK/XLE Sector Rotation — Complete Research Log

This document tells the full story of how we built and tested this strategy, step by step, from the simplest question to the final robustness-tested long+short system.

All numbers in this document are from the definitive backtest (`backtest.py`) which:
- Executes all trades at **next-day OPEN** prices (no look-ahead bias)
- Applies **0.05% slippage** to every execution
- Models **explicit rebalancing** (close old positions, open new ones)
- Tracks **margin requirements** for short positions
- Period: Oct 1999 – Mar 2026 (after 200-day SMA warmup from Dec 1998 data)
- Starting capital: $100,000

---

## Step 1: The Starting Question

**"What if I just split 50/50 between tech and energy instead of buying SPY?"**

We had daily OHLCV data for SPY, XLK, and XLE from TradingView (BATS exchange), spanning December 1998 to March 2026 — roughly 27 years and 6,858 common trading days.

First, we cleaned the data. TradingView exports come in overlapping chunks with duplicate rows, so we merged and deduplicated them into clean CSVs: `SPY_clean.csv`, `XLK_clean.csv`, `XLE_clean.csv`.

Then we ran the simplest possible comparison — buy and hold:

| Strategy | Final Value | CAGR | Max Drawdown | Sharpe |
|----------|------------|------|-------------|--------|
| 100% SPY | $477,026 | 6.12% | -56.47% | 0.40 |
| 100% XLK | $604,197 | 7.09% | -82.05% | 0.39 |
| 100% XLE | $469,699 | 6.06% | -76.73% | 0.35 |
| 50/50 XLK+XLE (static) | $536,948 | 6.61% | -59.42% | 0.38 |

**Finding:** The static 50/50 beats SPY by ~0.5% CAGR. The diversification benefit is real — when one crashes, the other often holds up, so the blended portfolio recovers faster. But the drawdowns are brutal (-59%) because when both crash at the same time (2008), there's no protection.

---

## Step 2: Dynamic Rotation (Long Only, No Buffer)

**"What if we don't just hold 50/50 — what if we rotate OUT of whichever sector is breaking down?"**

The idea: use the 200-day Simple Moving Average (SMA) as a trend filter. When one ETF drops below its SMA(200), it's in a downtrend. Move 100% into the other ETF until the broken one recovers.

Rules:
- Both above SMA(200): 50% XLK + 50% XLE
- XLK below SMA(200): 100% XLE
- XLE below SMA(200): 100% XLK
- Both below SMA(200): hold current allocation

Without a buffer, the system switched ~279 times over 27 years (~10/year), with many rapid whipsaws near the SMA crossover. This motivated adding a buffer.

---

## Step 3: Adding a Buffer + Long-Only Dynamic

**"Can we add a buffer so we don't switch every time the price barely touches the SMA?"**

Instead of switching the instant price crosses below SMA(200), we require the price to drop X% below the SMA before triggering a switch. No buffer on the way back up — if the price crosses above SMA(200), the sector is healthy again immediately.

With a 3% buffer, the dynamic long-only rotation produced:

| Strategy | Final Value | CAGR | Max DD | Sharpe | Vol | Trades |
|----------|------------|------|--------|--------|-----|--------|
| 100% SPY | $477,026 | 6.12% | -56.47% | 0.40 | 19.3% | 0 |
| 50/50 Static | $536,948 | 6.61% | -59.42% | 0.38 | 24.6% | 0 |
| **Dynamic Long-Only (3%)** | **$1,107,966** | **9.53%** | **-56.77%** | **0.51** | **23.2%** | **393** |

**Finding:** Dynamic rotation more than doubles SPY's final value. CAGR jumps to 9.53%, Sharpe to 0.51. However, the max drawdown is still -56.77% — almost as bad as SPY. The system catches the big regime shifts but doesn't protect during "both broken" scenarios like 2008.

---

## Step 4: The Long+Short Variant

**"What if, instead of just avoiding the broken sector, we also SHORT it?"**

This is the key insight. When tech breaks below its SMA(200), we don't just move to 100% energy — we go 50% long energy + 50% short tech. Now we profit from energy going up AND tech going down.

Rules (with 3% buffer):
- Both healthy: 50% long XLK + 50% long XLE
- XLK broken (3%+ below SMA200): 50% long XLE + 50% short XLK
- XLE broken (3%+ below SMA200): 50% long XLK + 50% short XLE
- Both broken: hold current allocation
- Recovery: when the broken sector crosses back ABOVE SMA(200), return to 50/50 long

| Strategy | Final Value | CAGR | Max DD | Sharpe | Vol | CAR/MDD | Trades |
|----------|------------|------|--------|--------|-----|---------|--------|
| 100% SPY | $477,026 | 6.12% | -56.47% | 0.40 | 19.3% | 0.11 | 0 |
| 50/50 Static | $536,948 | 6.61% | -59.42% | 0.38 | 24.6% | 0.11 | 0 |
| Dynamic Long-Only (3%) | $1,107,966 | 9.53% | -56.77% | 0.51 | 23.2% | 0.17 | 393 |
| **Long+Short (3%)** | **$719,562** | **7.76%** | **-36.18%** | **0.54** | **16.1%** | **0.21** | **606** |

**Finding:** The long+short version has lower CAGR than long-only dynamic (7.76% vs 9.53%), but dramatically better risk-adjusted performance:
- **Max drawdown cut by 36%** (-36.18% vs -56.77%)
- **Highest Sharpe ratio** (0.54 vs 0.51)
- **Lowest volatility of all options** (16.1%, even lower than SPY's 19.3%)
- **153 regime switches** over 26.5 years (~6 per year)

The short positions act as a hedge — when the market crashes and even the "strong" sector dips temporarily, the short on the broken sector cushions the blow. This is why the volatility drops so dramatically.

---

## Step 5: Real Historical Examples

To understand why the numbers look the way they do, here are the major regime changes the system caught:

### Dot-Com Crash (September 2000)
- XLK dropped 4% below SMA(200) on Sep 11, 2000
- XLE was 16.3% ABOVE its SMA(200)
- Action: 50% long XLE + 50% short XLK
- Held for **449 days**. XLK crashed from $25.81 to ~$12. The short was a massive winner.

### Oil Crash + Tech Bull Run (October 2014)
- XLE dropped 3.9% below SMA(200) on Oct 1, 2014
- XLK was 5.1% above its SMA(200)
- Action: 50% long XLK + 50% short XLE
- Held for **559 days**. XLE dropped from $44 to $28 (-37%). XLK went from $19.64 to $22+. Profit on both sides.

### COVID Crash (January 2020)
- XLE dropped 3.3% below SMA(200) on Jan 17, 2020 — before anyone knew COVID was coming
- XLK was 19.1% above its SMA(200)
- Action: 50% long XLK + 50% short XLE
- Held for **305 days**. XLE cratered to $11 (-63%). Short was a massive winner. XLK recovered fast.

### 2022 Tech Selloff + Energy Boom
- XLK dropped 3.8% below SMA(200) on Apr 8, 2022 (Fed raising rates aggressively)
- XLE was 35.2% above its SMA(200) (Ukraine war, oil surging)
- Action: 50% long XLE + 50% short XLK
- Held for **129 days**. Right side of both moves.

### Current Position (March 27, 2026)
- XLK at $129.92, **6% below** SMA(200) of $138.23
- XLE at $62.56, **34% above** SMA(200) of $46.82
- Current allocation: **50% long XLE + 50% short XLK**

---

## Step 6: Robustness Testing

Three tests to make sure the strategy isn't fragile or overfit.

### Test 6a: Buffer Sensitivity — Is 3% Overfit?

We tested every buffer from 1% to 5% on the full dataset:

| Buffer | Final Value | CAGR | Sharpe | Max DD | CAR/MDD | Trades |
|--------|------------|------|--------|--------|---------|--------|
| SPY | $477,026 | 6.12% | 0.40 | -56.47% | 0.11 | 0 |
| 1% | $403,315 | 5.42% | 0.42 | -41.51% | 0.13 | 942 |
| 2% | $481,779 | 6.13% | 0.45 | -36.50% | 0.17 | 742 |
| **3%** | **$719,562** | **7.76%** | **0.54** | **-36.18%** | **0.21** | **606** |
| 4% | $602,014 | 7.03% | 0.50 | -32.17% | 0.22 | 514 |
| 5% | $671,525 | 7.48% | 0.52 | -32.72% | 0.23 | 470 |

**Verdict: Not overfit.** Every buffer beats SPY on Sharpe ratio. CAGR ranges 5.4–7.8% across all buffers. The 3% buffer has the highest CAGR and Sharpe, but 4-5% have slightly better max drawdowns and CAR/MDD. The strategy works across the entire range — the exact buffer choice isn't critical.

### Test 6b: "Both Broken" Alternatives

When both XLK and XLE are below their SMA(200) (rare — only in severe crashes like 2008), the original rule was "hold current allocation." We tested going to cash, Treasury bonds (TLT), or gold (GLD).

**Full 27-year dataset (Oct 1999 – Mar 2026):**

| Rule | Final Value | CAGR | Max DD | Sharpe | CAR/MDD |
|------|------------|------|--------|--------|---------|
| SPY | $477,026 | 6.12% | -56.47% | 0.40 | 0.11 |
| Hold (original) | $719,562 | 7.76% | -36.18% | 0.54 | 0.21 |
| **Cash** | **$938,591** | **8.85%** | **-29.91%** | **0.64** | **0.30** |

**Common period with TLT/GLD (Nov 2004 – Mar 2026):**

| Rule | Final Value | CAGR | Max DD | Sharpe | CAR/MDD |
|------|------------|------|--------|--------|---------|
| SPY | $534,875 | 8.18% | -56.47% | 0.51 | 0.14 |
| Hold | $555,011 | 8.37% | -36.18% | 0.60 | 0.23 |
| Cash | $571,946 | 8.53% | -29.91% | 0.63 | 0.29 |
| TLT | $542,974 | 8.26% | -35.22% | 0.57 | 0.23 |
| **GLD** | **$857,863** | **10.61%** | **-27.53%** | **0.68** | **0.39** |

**Verdict:** Going to cash when both are broken is a clear improvement over holding — better CAGR (8.85% vs 7.76%), better Sharpe (0.64 vs 0.54), and lower max drawdown (-29.91% vs -36.18%). On the common period, GLD was the best alternative (10.61% CAGR, -27.53% max DD, 0.39 CAR/MDD).

**This also answers Claude's concern #4:** The cash-when-both-broken variant has now been tested on the full 27-year dataset, including the 2000-2004 dot-com recovery period. It works.

### Test 6c: Short Borrow Cost Impact

XLK and XLE are among the most liquid ETFs on the planet. Borrow fees are tiny. But we tested anyway:

| Annual Borrow Cost | Final Value | CAGR | Sharpe |
|--------------------|------------|------|--------|
| 0% (theoretical) | $719,562 | 7.76% | 0.54 |
| 0.3% (typical) | $708,035 | 7.69% | 0.54 |
| 0.5% (conservative) | $700,451 | 7.65% | 0.54 |
| 1.0% (high) | $681,835 | 7.54% | 0.53 |
| 2.0% (extreme) | $646,040 | 7.32% | 0.52 |

**Verdict: Negligible.** Even at an extreme 2% annual borrow cost, CAGR drops by only 0.44% and Sharpe barely moves.

---

## Step 7: Responding to Peer Review

After presenting the initial results, we received detailed feedback raising several concerns. Here's how we addressed each:

### Concern 1: "Independent signal count is small"

**Valid.** The system's returns are driven by catching a handful of large sector divergences (dot-com, oil crash, COVID, 2022). There are ~153 switches over 26.5 years, but many cluster around the same regime. The real number of independent regime calls is maybe 20-25. This is inherent to trend-following systems — they make money on the fat tails, not on average.

**Our response:** We acknowledge this. The buffer sensitivity test shows the edge isn't dependent on a single parameter, and the structural tech/energy divergence logic is economically motivated (not data-mined). But the small independent sample size means we should size the allocation conservatively.

### Concern 2: "Long+short reduces CAGR vs long-only"

**Confirmed.** Long-only dynamic with 3% buffer returns 9.53% CAGR vs 7.76% for long+short. The shorting component costs ~1.8% CAGR in exchange for cutting max drawdown from -56.8% to -36.2% and volatility from 23.2% to 16.1%.

**Our response:** This is a conscious tradeoff. The long+short version has a higher Sharpe (0.54 vs 0.51) and much better CAR/MDD (0.21 vs 0.17). For a portfolio allocation — not the whole portfolio — the risk-adjusted version is more useful.

### Concern 3: "Perfect 27-year window for tech/energy divergence"

**Valid.** 1998-2026 includes dot-com, shale revolution, QE era, COVID, and the energy/inflation shock. This may be the best possible period for this strategy.

**Our response:** We can't test forward, but we can note that the tech/energy structural divergence is driven by fundamental economic forces (rates, inflation, innovation cycles) that have existed for decades and aren't likely to disappear. The risk is green energy blurring the line — worth monitoring.

### Concern 4: "Both-broken cash rule needs full dataset test"

**Fixed.** We ran the cash-when-both-broken variant on the full 27-year dataset (Oct 1999 – Mar 2026). Results: CAGR 8.85%, Max DD -29.91%, Sharpe 0.64. Better than the "hold" variant on every metric.

### Concern 5: "Rebalancing mechanics and execution prices"

**Confirmed correct.** The backtest (`backtest.py`):
- Detects signals at close on day T
- Executes all trades at open on day T+1
- Applies 0.05% slippage to every execution
- Explicitly closes old positions and opens new ones (no phantom rebalancing)

### Concern 6: "Margin requirements"

**Not binding.** With 50% of capital deployed as margin collateral against 50% short, we have 2x the Reg T initial margin requirement (50%) and 3.3x the maintenance margin (30%). The SMA recovery rule closes shorts well before any margin call scenario. Analysis in `backtest.py --test margin`.

### Suggestion: "Test other sector pairs"

**Not yet implemented.** This requires downloading XLP, XLU, and other sector ETF data. It's a valid robustness test and would strengthen the thesis significantly if the same logic works on other structurally divergent pairs. Queued for future work.

---

## Summary: The Evolution

| Step | Strategy | CAGR | Max DD | Sharpe | Vol | CAR/MDD | Key Insight |
|------|----------|------|--------|--------|-----|---------|-------------|
| 1 | 100% SPY (benchmark) | 6.12% | -56.5% | 0.40 | 19.3% | 0.11 | Baseline |
| 1 | 50/50 Static XLK+XLE | 6.61% | -59.4% | 0.38 | 24.6% | 0.11 | Diversification helps returns but not drawdowns |
| 3 | Dynamic Long-Only (3% buffer) | 9.53% | -56.8% | 0.51 | 23.2% | 0.17 | SMA(200) rotation captures regime changes |
| 4 | **Long+Short (3% buffer)** | **7.76%** | **-36.2%** | **0.54** | **16.1%** | **0.21** | Shorting hedges risk, cuts drawdown 36% |
| 6b | **L+S + cash when both broken** | **8.85%** | **-29.9%** | **0.64** | ~15% | **0.30** | Best risk-adjusted: highest Sharpe, lowest DD |

---

## Final Strategy Rules (Recommended Configuration)

1. Calculate the 200-day SMA for both XLK and XLE daily
2. **Both healthy** (above SMA200): 50% long XLK + 50% long XLE
3. **One broken** (3%+ below SMA200): 50% long the strong one + 50% short the broken one
4. **Both broken** (both 3%+ below SMA200): go to 100% cash
5. **Recovery**: when a broken sector crosses back above SMA(200) (no buffer on the way up), return to 50/50 long
6. Check at close, trade at next open. ~6 switches per year.

**Expected performance (based on 26.5-year backtest):**
- CAGR: ~8.9%
- Max Drawdown: ~-30%
- Sharpe Ratio: ~0.64
- Volatility: ~15%

**Degrade expectations by 20-30% for live trading** (implementation friction, regime changes, unexpected correlations).

---

## Implementation Notes

### Execution Model
- Signals computed from close prices at end of day
- All trades execute at next day's open price
- 0.05% slippage applied (conservative for ETFs with $1B+ daily volume)
- No leverage required — the 50/50 L+S uses exactly 100% of capital
- Short positions require margin account but margin is not binding (2x Reg T)

### Tax Efficiency
- ~6 switches/year creates short-term capital gains events
- Best run in a tax-advantaged account (IRA, 401k)
- If taxable, consider the long-only variant (fewer trades, similar edge without shorts)

### Broker Requirements
- Must support short selling (Fidelity, Schwab, Interactive Brokers all work)
- XLK and XLE are easy-to-borrow, no locate needed
- Two ETFs + cash — extremely simple to implement

---

## What We Tested But Did NOT Include

- **Individual ETF buy-and-hold** (XLK alone, XLE alone): XLK beats SPY, XLE doesn't
- **No-buffer dynamic rotation**: works but ~279 switches = too much whipsaw
- **TLT as "both broken" hedge**: works but worse than cash on risk-adjusted basis
- **GLD as "both broken" hedge**: best on common period, but adds a third instrument and shorter track record
- **Other sector pairs** (XLK/XLP, XLE/XLU): not yet tested — future work

---

## Data

- Source: TradingView BATS exchange exports
- Period: December 22, 1998 – March 27, 2026
- Common trading days: 6,658 (after SMA warmup)
- ETFs: SPY, XLK, XLE, TLT, GLD
- All data cleaned, merged, and deduplicated into `*_clean.csv` files
- Backtest code: `backtest.py` (single-file, reproducible)

---

## Charts

| File | What It Shows |
|------|--------------|
| `comparison.png` | SPY vs static 50/50 |
| `comparison_4way.png` | SPY vs XLK vs XLE vs static 50/50 |
| `comparison_dynamic.png` | Static vs dynamic rotation |
| `comparison_all_switches.png` | Dynamic rotation with all switch points marked |
| `comparison_buffers.png` | Buffer sensitivity (1-3%) |
| `comparison_buffers_all.png` | Buffer sensitivity (1-5%) |
| `comparison_long_short.png` | Long-only vs long+short |
| `test1_sensitivity.png` | Robustness: buffer sensitivity across all values |
| `test2_both_broken.png` | Robustness: "both broken" alternatives (cash, TLT, GLD) |

---

## Honest Caveats

1. **Backtested, not live-traded.** 26.5 years of evidence with proper next-open execution, slippage, and borrow costs. But backtests always look better than reality. Degrade expectations by 20-30%.
2. **Small independent sample.** ~20-25 truly independent regime calls drive most of the returns. Statistical confidence is moderate, not high.
3. **Survivorship bias.** We tested XLK/XLE because they exist today and worked. Other sector pairs might not show this relationship. Testing additional pairs would strengthen the thesis.
4. **Structural change risk.** If the tech/energy negative correlation weakens (e.g., green energy becomes correlated with tech), the edge could erode.
5. **Tax drag.** ~6 switches/year in a taxable account creates short-term capital gains. Best in an IRA/401k.
6. **Short selling mechanics.** Borrow fees negligible (tested up to 2%), margin not binding (2x Reg T). But shorts carry theoretical unlimited loss risk. The SMA recovery rule mitigates this.
7. **Best-case backtest window?** 1998-2026 includes extreme tech/energy divergence events. Future decades may not produce the same magnitude of divergence.
