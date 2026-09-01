# AXIOM Backtest Summary

Evaluation window: `2021-01-04` to `2025-12-31`  
Assets: `AAPL, MSFT, GOOGL, AMZN, META`  
Benchmark: `^GSPC`

| Metric | AXIOM combined | Quantitative only | Equal weight | Benchmark |
| --- | ---: | ---: | ---: | ---: |
| CAGR | Not measured* | 16.83% | 20.59% | 13.12% |
| Annualized volatility | Not measured* | 26.51% | 26.76% | 16.96% |
| Sharpe ratio | Not measured* | 0.531 | 0.648 | 0.519 |
| Sortino ratio | Not measured* | 0.790 | 0.909 | 0.712 |
| Maximum drawdown | Not measured* | -39.63% | -46.55% | -25.43% |
| Annual turnover | Not measured* | 348.54% | 50.08% | N/A |
| Transaction-cost drag | Not measured* | 3.84% | 0.55% | 0.00% |


### Turnover methodology

Annual turnover uses the standard one-way definition:

`turnover = 0.5 × Σ |target weight − pre-trade weight|`

Transaction costs use the complete traded notional across both purchases and
sales:

`traded notional = Σ |target weight − pre-trade weight|`

`transaction cost = portfolio value × traded notional × cost rate`


## Results analysis

During the evaluation period from January 2021 through December 2025, the
monthly rebalanced equal-weight strategy produced the highest CAGR and the
highest Sharpe ratio among the tested portfolio strategies.

The quantitative-only optimizer generated a 16.83% CAGR compared with 20.59%
for equal weight. Its Sharpe ratio was 0.531 compared with 0.648 for equal
weight. This indicates that historical mean-variance optimization did not
provide better risk-adjusted performance for this concentrated large-cap
technology universe.

The quantitative optimizer did, however, reduce maximum drawdown relative to
equal weight:

- Quantitative-only maximum drawdown: -39.63%
- Equal-weight maximum drawdown: -46.55%

The quantitative strategy's main weakness was turnover. Annual turnover reached
348.54%, creating an estimated transaction-cost drag of 3.84%. Equal weight
generated only 50.08% annual turnover and approximately 0.55% transaction-cost
drag.

The S&P 500 benchmark produced a lower CAGR of 13.12%, but it also had
substantially lower volatility and drawdown. Its 16.96% annualized volatility
and -25.43% maximum drawdown demonstrate the diversification advantage of the
broader market index.

These findings do not establish that one strategy will perform better in the
future. They show that:

1. simple baselines are essential when evaluating optimization systems;
2. expected-return and covariance estimates can create unstable allocations;
3. turnover and transaction costs can remove theoretical optimization benefits;
4. higher returns must be evaluated alongside volatility and drawdown;
5. a concentrated technology universe is not directly comparable with the
   diversified S&P 500 without acknowledging the universe difference.



*AXIOM combined is not measured because the repository does not yet contain a point-in-time historical news/sentiment dataset. Current news must not be used to simulate past decisions.*

> Historical performance does not guarantee future results. This report is for research and educational use only.
