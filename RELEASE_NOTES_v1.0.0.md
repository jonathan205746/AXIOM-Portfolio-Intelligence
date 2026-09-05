# AXIOM Portfolio Intelligence v1.0.0

AXIOM v1.0.0 is the first production release of an end-to-end portfolio research platform combining constrained portfolio optimization, financial risk analysis, relevant-news sentiment, semantic retrieval, and evidence-grounded AI commentary.

## Product capabilities

- Create portfolios, manage holdings, and retain analysis history.
- Compare optimized and equal-weight allocations.
- Inspect volatility, Value at Risk, maximum drawdown, and correlations.
- Classify relevant financial news with FinBERT.
- Retrieve supporting context with FAISS.
- Generate portfolio commentary using LangChain and Groq.
- Export a self-contained HTML report.
- Continue core analysis when optional news or LLM services are unavailable.

## Engineering highlights

- Dockerized Streamlit runtime with persistent SQLite and FAISS data.
- AWS infrastructure defined with CloudFormation.
- GitHub Actions test and compile gates.
- Temporary AWS authentication through IAM OIDC—no static AWS keys in GitHub.
- Immutable Amazon ECR images tagged with the Git commit SHA.
- EC2 deployment through AWS Systems Manager instead of CI-managed SSH keys.
- Post-deployment Streamlit health checks.
- Automatic restoration of the previous container image when a deployment is unhealthy.

## Quantitative evaluation

The price-only walk-forward evaluation spans 4 January 2021–31 December 2025 and includes transaction costs and drift-aware turnover. The quantitative strategy produced 16.83% net CAGR, a 0.536 Sharpe ratio, and a -39.63% maximum drawdown. Equal weight delivered higher return and Sharpe ratio in this concentrated technology universe, while the optimizer reduced drawdown relative to equal weight at the cost of materially higher turnover.

The combined sentiment strategy is not presented as historically validated because a point-in-time news dataset is not yet included. See [`backtesting.md`](backtesting.md).

## Release checklist

Complete every item against the exact commit that will receive the tag:

- [ ] Python compilation passes.
- [ ] Full automated test suite passes.
- [ ] Production GitHub Actions run succeeds.
- [ ] OIDC assumes the intended AWS deployment role.
- [ ] Commit-SHA image exists in ECR.
- [ ] EC2 is running that exact image.
- [ ] `/_stcore/health` returns `ok`.
- [ ] Desktop workflow passes.
- [ ] Real-phone workflow passes.
- [ ] Deliberate rollback drill restores the previous healthy image.
- [ ] Final release image is redeployed after the drill.
- [ ] Screenshots and demo GIF are sanitized and committed.
- [ ] No credentials, account IDs, private portfolio data, or tokens are visible.

## Known limitations

- Single-instance EC2 and SQLite are not highly available or horizontally scalable.
- The public demo currently uses HTTP and a changeable EC2 address.
- Financial NLP and generated commentary can be incomplete or incorrect.
- Application rollback does not automatically reverse database schema migrations.

## Upgrade and rollback

Deployment is triggered by a push to `main`. For exact verification and recovery instructions, see [`docs/production-release-guide.md`](docs/production-release-guide.md).

## Responsible use

AXIOM is an educational and research project. It is not financial advice, and historical performance does not guarantee future results.
