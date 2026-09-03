# AXIOM Backtesting Methodology

AXIOM includes a leakage-aware, price-only walk-forward backtest for the
quantitative optimizer. It compares:

1. the quantitative-only optimizer;
2. monthly rebalanced equal weight; and
3. a buy-and-hold market benchmark.

The sentiment-adjusted AXIOM strategy is not historically measured because the
repository does not contain a point-in-time historical news and sentiment
dataset. Current news must not be used to simulate past decisions.

## Evaluation configuration

- Evaluation window: 2021-01-04 through 2025-12-31
- Asset universe: AAPL, MSFT, GOOGL, AMZN, META
- Benchmark: S&P 500 (`^GSPC`)
- Rebalance frequency: monthly, on the first shared trading observation
- Optimization lookback: 252 observations
- Risk-free rate: 5% annually
- Weight constraints: 2% minimum and 35% maximum per asset
- Transaction-cost rate: 15 bps per traded notional
- Initial capital: 100,000 currency units

## Leakage controls

At each rebalance, the optimizer receives only observations strictly preceding
the rebalance date. The selected weights are then used for subsequent strategy
returns. No future price, current-period return, or current news is supplied to
the optimizer.

All compared series use common dates. Missing benchmark observations are not
forward-filled.

## Initial portfolio convention

The first target portfolio is treated as the common initial establishment. It
starts at the configured initial capital and is excluded from reported turnover
and transaction costs. Turnover and modeled costs begin with the next monthly
rebalance.

## Turnover and transaction costs

Weights drift with individual asset returns between rebalances. Turnover is
therefore calculated against the drifted pre-trade portfolio rather than the
previous target weights.

Standard one-way turnover is:

```text
0.5 * sum(abs(target weight - drifted pre-trade weight))
```

Complete traded notional across purchases and sales is:

```text
sum(abs(target weight - drifted pre-trade weight))
```

Modeled transaction cost is deducted once on each rebalance:

```text
net portfolio value * complete traded notional * transaction-cost rate
```

The backtest records separate gross and net NAV series. Net performance is the
primary result, while gross performance shows the effect before modeled costs.

## Corrected results

| Metric | Quantitative only | Equal weight | Benchmark |
| --- | ---: | ---: | ---: |
| Net CAGR | 16.83% | 20.59% | 13.12% |
| Gross CAGR | 17.42% | 20.68% | 13.12% |
| Net annualized volatility | 26.51% | 26.76% | 16.96% |
| Net Sharpe ratio | 0.536 | 0.653 | 0.526 |
| Net Sortino ratio | 0.787 | 0.942 | 0.749 |
| Net maximum drawdown | -39.63% | -46.55% | -25.43% |
| Annual one-way turnover | 167.46% | 25.03% | N/A |
| CAGR cost drag | 0.59% | 0.09% | 0.00% |
| Transaction costs / initial capital | 3.82% | 0.56% | 0.00% |

For this concentrated large-cap technology universe, equal weight produced the
highest net CAGR and net Sharpe ratio. The quantitative optimizer reduced
maximum drawdown relative to equal weight, but its higher turnover caused a
larger modeled cost drag. The broader S&P 500 benchmark had lower return but
substantially lower volatility and maximum drawdown.

## Output files

Running the backtest writes:

- `daily_nav.csv`: gross and net daily NAV plus the benchmark;
- `monthly_nav.csv`: month-end NAV observations;
- `portfolio_weights.csv`: targets, turnover, traded notional, and costs;
- `backtest_results.json`: configuration and structured metrics; and
- `backtest_summary.md`: generated human-readable summary.

## Reproduction

```powershell
python scripts\backtest.py --output-dir results\turnover-corrected
python scripts\generate_backtest_report.py `
  --input results\turnover-corrected\backtest_results.json `
  --output results\turnover-corrected\backtest_summary.md
```

## Limitations

- Results are historical simulations, not live or out-of-sample guarantees.
- The asset universe is concentrated in US large-cap technology equities.
- Taxes, slippage, bid-ask spread variation, market impact, and partial fills
  are not modeled separately from the constant transaction-cost assumption.
- Delisting and survivorship-bias controls are not implemented.
- The benchmark is not matched to the portfolio's sector concentration.
- Historical AI/sentiment performance is intentionally not claimed.

Historical performance does not guarantee future results. This backtest is for
research and educational use only.
