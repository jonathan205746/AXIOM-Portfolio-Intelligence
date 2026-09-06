# AXIOM Portfolio Intelligence v1.0.0

The first public release combines portfolio optimization, risk analytics,
financial-news sentiment, retrieval-augmented AI research, persistence,
reporting, and a production-oriented AWS delivery path.

## Highlights

- Constrained optimization, efficient frontier, and risk diagnostics
- FinBERT sentiment with ticker-relevant supporting news
- FAISS retrieval and LangChain/Groq evidence-grounded commentary
- SQLite persistence and sanitized HTML report export
- Dockerized Streamlit on CloudFormation-managed Amazon EC2
- Amazon SES templated password recovery through the EC2 instance role
- GitHub Actions delivery with IAM OIDC temporary credentials
- Immutable commit-SHA images in Amazon ECR
- SSM deployment, health verification, and deterministic rollback

## Verified quantitative evaluation

Price-only walk-forward evaluation, 4 January 2021–31 December 2025:

| Metric | Quantitative only | Equal weight | Benchmark |
| --- | ---: | ---: | ---: |
| Net CAGR | 16.83% | 20.59% | 13.12% |
| Net volatility | 26.51% | 26.76% | 16.96% |
| Net Sharpe | 0.536 | 0.653 | 0.526 |
| Net Sortino | 0.787 | 0.942 | 0.749 |
| Net maximum drawdown | -39.63% | -46.55% | -25.43% |
| Annual one-way turnover | 167.46% | 25.03% | N/A |
| CAGR cost drag | 0.59% | 0.09% | 0.00% |

Sentiment-adjusted historical performance is intentionally not reported because
the repository has no point-in-time historical news dataset.

## Release evidence

Replace placeholders and check every item before publication:

- [ ] Tests: `<ACTUAL_COUNT> passed` on `<RELEASE_SHA>`
- [ ] Python compilation and documentation checks passed
- [ ] ECR digest: `<ECR_IMAGE_DIGEST>`
- [ ] OIDC-authenticated Actions run: `<RUN_URL>`
- [ ] SSM command completed: `<COMMAND_ID>`
- [ ] Production health check passed: `<UTC_TIMESTAMP>`
- [ ] Desktop, mobile Wi-Fi, and mobile-data smoke tests passed
- [ ] SES reset-email smoke test passed with private details redacted
- [ ] Rollback from `<RELEASE_SHA>` to `<PREVIOUS_SHA>` passed
- [ ] Final `<RELEASE_SHA>` redeployed after the rollback drill
- [ ] Screenshots and GIF reviewed for secrets and personal information

Do not publish while any required box remains unchecked.

## Architecture

```text
GitHub Actions -> IAM OIDC -> ECR -> SSM -> EC2 -> Streamlit health check
Streamlit on EC2 -> EC2 instance role -> Amazon SES
```

## Upgrade and rollback

Deploy the immutable ECR tag matching the release commit SHA. To roll back,
redeploy the previous successful SHA, verify the exact running image and health
endpoint, test the core workflow, and preserve `/data`.

Container rollback does not undo database migrations. A backward-incompatible
schema change requires a separately tested backup/restore or forward fix.

See [the production release guide](docs/production-release-guide.md).

## Known limitations

- Educational and research software; not financial advice
- Single-host deployment is not highly available
- SQLite is intended for the current single-instance usage model
- External providers can be unavailable or rate-limited
- Current HTTP/IP demo is not a stable HTTPS production endpoint
- Historical results do not guarantee future performance
