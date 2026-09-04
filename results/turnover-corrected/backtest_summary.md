# AXIOM Backtest Summary

Evaluation window: `2021-01-04` to `2025-12-31`  
Assets: `AAPL, MSFT, GOOGL, AMZN, META`  
Benchmark: `^GSPC`
Transaction-cost rate: `15.0 bps per traded notional`
Initial portfolio establishment: `excluded from turnover and transaction costs`

| Metric | AXIOM combined | Quantitative only | Equal weight | Benchmark |
| --- | ---: | ---: | ---: | ---: |
| Net CAGR | Not measured* | 16.83% | 20.59% | 13.12% |
| Gross CAGR | Not measured* | 17.42% | 20.68% | 13.12% |
| Net annualized volatility | Not measured* | 26.51% | 26.76% | 16.96% |
| Net Sharpe ratio | Not measured* | 0.536 | 0.653 | 0.526 |
| Net Sortino ratio | Not measured* | 0.787 | 0.942 | 0.749 |
| Net maximum drawdown | Not measured* | -39.63% | -46.55% | -25.43% |
| Annual one-way turnover | Not measured* | 167.46% | 25.03% | N/A |
| CAGR cost drag | Not measured* | 0.59% | 0.09% | 0.00% |
| Transaction costs / initial capital | Not measured* | 3.82% | 0.56% | 0.00% |

## Turnover and cost methodology

One-way turnover is `0.5 * sum(abs(target weight - drifted pre-trade weight))`. Transaction costs apply to complete bought-and-sold notional, `sum(abs(target weight - drifted pre-trade weight))`. Net performance is the primary result; gross performance is shown for cost comparison.

*AXIOM combined is not measured because the repository does not yet contain a point-in-time historical news/sentiment dataset. Current news must not be used to simulate past decisions.*

> Historical performance does not guarantee future results. This report is for research and educational use only.
