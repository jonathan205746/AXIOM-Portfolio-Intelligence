# AXIOM Portfolio Intelligence v1.0.0

AXIOM v1.0.0 is the first stable engineering release of the portfolio-intelligence platform.

It packages the current portfolio optimization, risk analytics, financial NLP, retrieval-augmented commentary, reproducible evaluation, security hardening, and AWS delivery workflow into a versioned milestone.

## Highlights

- Constrained Modern Portfolio Theory with allocation bounds and portfolio-risk analytics.
- Walk-forward evaluation with transaction costs, turnover, equal-weight comparison, and S&P 500 benchmark.
- FinBERT financial-news sentiment with ticker-aware relevance filtering.
- FAISS retrieval and LangChain/Groq commentary grounded in available evidence.
- Interactive Streamlit analysis workflow and downloadable HTML reporting.
- Dockerized non-root runtime with persistent SQLite and FAISS state.
- GitHub Actions quality, CodeQL, secret, dependency, and container security checks.
- AWS delivery using IAM OIDC, immutable ECR image tags, Systems Manager, and EC2.
- Documented residual dependency risk rather than scanner suppression.

## Verified repository evidence

The v1.0 release line is based on the hardened `main` branch after Issues and pull requests completing the dependency-security modernization work.

Repository verification includes:

- **84 automated tests**
- Python compilation check
- Black formatting verification
- Ruff linting
- mypy static type checking
- CodeQL analysis
- Gitleaks history scan
- Trivy filesystem dependency scan
- Trivy runtime-container scan
- non-root runtime user: **UID/GID 10001**

### Security-hardening result

| Scope | Before | v1.0 documented state |
|---|---:|---:|
| Repository dependency scan | 22 HIGH / 0 CRITICAL | 16 HIGH / 0 CRITICAL |
| Runtime container scan | 15 HIGH / 0 CRITICAL | 2 HIGH / 0 CRITICAL |

No global scanner exclusion was introduced to obtain these results.

The two remaining runtime HIGH findings are recorded with their advisory, exposure path, mitigation, and decision in [`security/dependency-risk-register.md`](security/dependency-risk-register.md).

## Core dependency modernization

The v1.0 runtime includes:

- `transformers==5.17.0`
- `sentence-transformers==6.1.0`
- `python-jose[cryptography]==3.5.0`
- `cryptography==50.0.0`
- `pyasn1==0.6.4`
- `huggingface-hub==1.32.0`
- `tokenizers==0.23.2`
- `setuptools==84.0.0`
- `wheel==0.48.0`

FinBERT/RAG regression coverage verifies the compatibility path used by the application.

## Verified quantitative evaluation

The price-only walk-forward evaluation covers **4 January 2021–31 December 2025** with AAPL, MSFT, GOOGL, AMZN, and META.

Configuration:

- 252-trading-day lookback
- monthly rebalancing
- 2–35% asset bounds
- 5% annual risk-free rate
- 15 bps transaction costs

| Metric | Quantitative strategy | Equal weight | S&P 500 |
|---|---:|---:|---:|
| Net CAGR | 16.83% | 20.59% | 13.12% |
| Annualized volatility | 26.51% | 26.76% | 16.96% |
| Sharpe ratio | 0.536 | 0.653 | 0.526 |
| Maximum drawdown | -39.63% | -46.55% | -25.43% |
| Annual one-way turnover | 167.46% | 25.03% | N/A |
| CAGR cost drag | 0.59% | 0.09% | 0.00% |

The equal-weight portfolio outperformed the optimized strategy on return and Sharpe ratio in this test universe. AXIOM keeps that result visible rather than presenting optimization as automatically superior.

Historical sentiment performance is not claimed because the repository does not include a point-in-time news dataset.

## Architecture and delivery

```text
Browser
  ↓
Streamlit
  ↓
Analysis orchestrator
  ├─ market/news data
  ├─ optimization + risk
  ├─ FinBERT + FAISS + LLM
  └─ SQLite + FAISS persistence

GitHub Actions
  ↓ IAM OIDC
Amazon ECR
  ↓
AWS Systems Manager
  ↓
Docker on EC2
```

Production images use immutable Git-commit tags. The deployment path avoids long-lived AWS credentials in GitHub and does not require CI-held SSH credentials.

## Upgrade notes

For a clean v1.0 environment:

```bash
python -m pip install -r requirements-frontend.txt
python -m pip check
```

For Docker:

```bash
docker compose build --no-cache
docker compose up -d
curl --fail http://localhost:8501/_stcore/health
```

Existing persistent volumes created by older root-running images may require ownership migration to UID/GID `10001`. The production deployment script includes that migration path.

## Known limitations

- This is educational and research software, not financial advice.
- Historical estimates do not predict future performance.
- FinBERT can misclassify ambiguous or context-poor headlines.
- Retrieved context reduces but cannot eliminate LLM hallucination.
- The current single-EC2/SQLite architecture is not highly available.
- The operator-restricted HTTP demo is not a stable public HTTPS endpoint.
- Point-in-time news data is not yet available for historical sentiment validation.
- Residual HIGH dependency findings remain documented and monitored.

## Release integrity

The public `v1.0.0` tag must point to a verified commit on protected `main`.

Do not move or recreate the public tag after publication. Subsequent changes should use a new semantic version.

For production deployment evidence, rollback validation, and the publication procedure, follow [`AXIOM_PRODUCTION_RELEASE_GUIDE.md`](AXIOM_PRODUCTION_RELEASE_GUIDE.md).

## Responsible use

AXIOM outputs may be incomplete or incorrect and should not be used as the sole basis for investment decisions.
