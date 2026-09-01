# AXIOM Portfolio Intelligence — API Reference

## Status

The public AWS deployment currently runs the **Streamlit frontend service** on port `8501`. The FastAPI service is an optional local/development interface and is not required for the deployed dashboard workflow.

Before relying on this document, start the API and verify its generated OpenAPI schema:

```bash
docker compose --profile api up --build -d
```

Then open:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

The running OpenAPI schema is the authoritative contract. Routes described below should be published only when they exist in the current backend build.

## Base URLs

| Environment | Base URL |
| --- | --- |
| Local FastAPI | `http://localhost:8000` |
| Docker API profile | `http://localhost:8000` |
| Public Streamlit demo | `http://13.207.84.157:8501` |

## Authentication and security

Do not expose an unauthenticated development API directly to the public internet.

For a production API, add:

- HTTPS
- authenticated users or service credentials
- authorization for user-owned portfolios
- rate limiting
- input-size limits
- CORS allow-listing
- secret management through AWS Secrets Manager or SSM
- structured audit logs without API keys or sensitive holdings

## Health endpoint

### `GET /health`

Returns service availability and safe configuration status.

Example:

```bash
curl -fsS http://localhost:8000/health
```

Example response:

```json
{
  "status": "ok",
  "service": "axiom-api",
  "version": "1.0.0"
}
```

Health responses must not include secret values.

## Portfolio optimization

### `POST /optimize`

Runs the quantitative analysis and, when enabled, news sentiment and grounded recommendation stages.

Example request:

```json
{
  "tickers": ["AAPL", "MSFT", "GOOGL"],
  "current_weights": {
    "AAPL": 0.4,
    "MSFT": 0.35,
    "GOOGL": 0.25
  },
  "period": "1y",
  "risk_free_rate": 0.05,
  "use_news": true,
  "use_llm": true
}
```

Suggested validation rules:

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `tickers` | `string[]` | Yes | Normalized, unique symbols; enforce a safe maximum |
| `current_weights` | object | No | Non-negative values that sum approximately to `1.0` |
| `period` | string | No | Supported historical window such as `6mo` or `1y` |
| `risk_free_rate` | number | No | Annual decimal rate within an allowed range |
| `use_news` | boolean | No | Enables external news retrieval |
| `use_llm` | boolean | No | Enables Groq recommendation generation |

Example response shape:

```json
{
  "tickers": ["AAPL", "MSFT", "GOOGL"],
  "optimal_weights": {
    "AAPL": 0.32,
    "MSFT": 0.38,
    "GOOGL": 0.3
  },
  "expected_annual_return": 0.14,
  "annual_volatility": 0.19,
  "sharpe_ratio": 0.74,
  "sentiment_scores": {
    "AAPL": 0.18,
    "MSFT": 0.11,
    "GOOGL": -0.04
  },
  "recommendations": {},
  "risk_report": {
    "value_at_risk_95": -0.021,
    "maximum_drawdown": -0.24,
    "correlation_matrix": {}
  },
  "warnings": []
}
```

The numeric values above illustrate the schema only. They are not expected returns or investment recommendations.

Python example:

```python
import requests

payload = {
    "tickers": ["AAPL", "MSFT", "GOOGL"],
    "period": "1y",
    "risk_free_rate": 0.05,
    "use_news": True,
    "use_llm": False,
}

response = requests.post(
    "http://localhost:8000/optimize",
    json=payload,
    timeout=120,
)
response.raise_for_status()
print(response.json())
```

## Sentiment endpoint

### `GET /sentiment/{ticker}`

When implemented, returns aggregated FinBERT sentiment for recent relevant articles.

```bash
curl -fsS http://localhost:8000/sentiment/AAPL
```

Example response shape:

```json
{
  "ticker": "AAPL",
  "sentiment_score": 0.18,
  "sentiment_label": "neutral",
  "article_count": 12,
  "generated_at": "2026-09-01T19:10:20Z"
}
```

Sentiment is a model output, not a verified statement about future price movement.

## News endpoint

### `GET /news/{ticker}`

When implemented, returns recent deduplicated news metadata.

```bash
curl -fsS "http://localhost:8000/news/AAPL?days_back=7"
```

Do not return provider API keys, full copyrighted article bodies, or unsafe HTML.

## Error format

FastAPI normally returns validation errors in its standard `detail` field. Application errors should also include a stable machine-readable code.

```json
{
  "detail": "No market data was returned for one or more symbols.",
  "code": "MARKET_DATA_UNAVAILABLE",
  "request_id": "request-id"
}
```

| HTTP status | Meaning |
| --- | --- |
| `400` | Invalid business input |
| `401` | Authentication required or invalid |
| `403` | Authenticated caller lacks access |
| `404` | Portfolio, run, or ticker resource not found |
| `422` | Request schema validation failed |
| `429` | Application or provider rate limit exceeded |
| `502` | Upstream market, news, or LLM provider failed |
| `503` | Optional model/service temporarily unavailable |
| `500` | Unexpected server error |

## Provider failures and fallback

The API should preserve quantitative output when optional services fail:

- market-price failure: stop or exclude affected symbols with a clear warning
- news failure: continue without fresh sentiment
- FinBERT failure: continue with quantitative-only allocation
- FAISS failure: skip retrieval and do not claim grounded generation
- Groq failure: return deterministic fallback text and preserve risk results

## Rate limits

Provider quotas change by account and plan. Do not hard-code public promises such as “100 requests per day” without checking the active provider terms.

Recommended controls:

- cache safe market/news responses
- use request timeouts and bounded retries
- add per-user and global rate limits
- return `Retry-After` when appropriate
- monitor provider error rate, latency, and spend

## Versioning

If the API becomes public, introduce an explicit prefix such as `/api/v1` before clients depend on it. Breaking schema changes should create a new version or a documented migration period.

## Contract verification

Export the real schema from the running service:

```bash
curl -fsS http://localhost:8000/openapi.json -o openapi.json
```

Compare this document with `openapi.json` during CI. Do not document routes or fields that are absent from the generated schema.
