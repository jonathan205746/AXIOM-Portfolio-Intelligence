# API Reference

Base URL (local): `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`
ReDoc: `http://localhost:8000/redoc`

Built by Parmod | [GitHub](https://github.com/Parmodk2310/AI-Powered-Portfolio-Optimizer)

---

## Authentication

No authentication required for local development.
For production deployment, add API key header: `X-API-Key: your_key`

---

## Endpoints

---

### GET /health

Health check endpoint.

**Request:**
```
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "author": "Parmod"
}
```

---

### POST /optimize

Main endpoint. Runs the full pipeline:
stock data → news → sentiment → optimization → risk → LLM recommendations.

**Request Body:**
```json
{
  "tickers": ["AAPL", "MSFT", "GOOGL"],
  "current_weights": {
    "AAPL": 0.40,
    "MSFT": 0.40,
    "GOOGL": 0.20
  },
  "period": "6mo",
  "risk_free_rate": 0.05
}
```

**Request Fields:**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| tickers | list[str] | Yes | — | Stock symbols. Min 2, Max 10 |
| current_weights | dict | No | null | Current allocation. Must sum to 1.0 |
| period | str | No | "6mo" | History period: 1mo, 3mo, 6mo, 1y, 2y |
| risk_free_rate | float | No | 0.05 | Annual risk-free rate (5% default) |

**Response:**
```json
{
  "optimal_weights": {
    "AAPL": 0.352,
    "MSFT": 0.448,
    "GOOGL": 0.200
  },
  "expected_annual_return": 14.2,
  "annual_volatility": 18.5,
  "sharpe_ratio": 1.43,
  "rebalancing_actions": [
    {
      "ticker": "AAPL",
      "current_weight": 40.0,
      "optimal_weight": 35.2,
      "change": -4.8,
      "action": "SELL"
    },
    {
      "ticker": "MSFT",
      "current_weight": 40.0,
      "optimal_weight": 44.8,
      "change": 4.8,
      "action": "BUY"
    },
    {
      "ticker": "GOOGL",
      "current_weight": 20.0,
      "optimal_weight": 20.0,
      "change": 0.0,
      "action": "HOLD"
    }
  ],
  "recommendations": {
    "AAPL": "Strong positive sentiment driven by iPhone 15 cycle and services growth. Quantitative optimization suggests slight reduction from current 40% to 35.2%. Recommend REDUCE.",
    "MSFT": "Neutral-to-positive sentiment with Azure cloud growth offsetting AI investment concerns. Optimization suggests increasing weight to 44.8%. Recommend BUY.",
    "GOOGL": "Mixed sentiment around ad revenue recovery and Gemini competition. Current weight of 20% aligns with optimal. Recommend HOLD."
  },
  "risk_report": {
    "volatility_by_stock": {
      "AAPL": 22.1,
      "MSFT": 18.3,
      "GOOGL": 24.7
    },
    "value_at_risk": {
      "var_percentage": 1.83,
      "var_amount": 1830.0,
      "confidence_level": 0.95,
      "interpretation": "With 95% confidence, maximum daily loss is 1.83% (₹1,830 on ₹1,00,000 portfolio)"
    },
    "max_drawdown": {
      "max_drawdown_percentage": 24.5,
      "interpretation": "Worst historical decline from peak: 24.5%"
    },
    "correlation_matrix": {
      "AAPL": {"AAPL": 1.0, "MSFT": 0.82, "GOOGL": 0.75},
      "MSFT": {"AAPL": 0.82, "MSFT": 1.0, "GOOGL": 0.79},
      "GOOGL": {"AAPL": 0.75, "MSFT": 0.79, "GOOGL": 1.0}
    }
  }
}
```

**Response Fields:**

| Field | Type | Description |
|---|---|---|
| optimal_weights | dict | Optimized portfolio weights (sum = 1.0) |
| expected_annual_return | float | Expected annual return % |
| annual_volatility | float | Annualized portfolio volatility % |
| sharpe_ratio | float | Risk-adjusted return metric |
| rebalancing_actions | list | BUY / SELL / HOLD per ticker |
| recommendations | dict | LLM-generated explanation per ticker |
| risk_report | dict | VaR, volatility, drawdown, correlation |

---

### GET /sentiment/{ticker}

Get FinBERT sentiment score for a stock based on recent news.

**Request:**
```
GET /sentiment/AAPL
```

**Response:**
```json
{
  "ticker": "AAPL",
  "sentiment_score": 0.72,
  "sentiment_label": "positive",
  "article_count": 8
}
```

**Sentiment Score Interpretation:**

| Score Range | Label | Meaning |
|---|---|---|
| 0.10 to 1.0 | positive | Majority of news is favorable |
| -0.10 to 0.10 | neutral | Mixed or no clear sentiment |
| -1.0 to -0.10 | negative | Majority of news is unfavorable |

---

### GET /news/{ticker}

Get recent news articles for a stock ticker.

**Request:**
```
GET /news/MSFT?days_back=7
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| days_back | int | 7 | How many days of news to fetch |

**Response:**
```json
[
  {
    "ticker": "MSFT",
    "title": "Microsoft Azure reports 28% revenue growth in Q3",
    "description": "Microsoft's cloud division Azure grew 28% year-over-year, beating analyst estimates of 26% growth.",
    "url": "https://reuters.com/...",
    "published_at": "2025-04-30T10:00:00Z",
    "source": "Reuters",
    "text": "Microsoft Azure reports 28% revenue growth in Q3. Microsoft's cloud division Azure grew 28% year-over-year..."
  },
  {
    "ticker": "MSFT",
    "title": "Microsoft Copilot adoption accelerates among enterprise customers",
    "description": "...",
    "url": "https://...",
    "published_at": "2025-04-29T14:30:00Z",
    "source": "Bloomberg",
    "text": "..."
  }
]
```

---

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error message explaining what went wrong"
}
```

**Error Codes:**

| Code | Meaning | Common Cause |
|---|---|---|
| 200 | Success | — |
| 400 | Bad Request | Invalid ticker, weights don't sum to 1 |
| 404 | Not Found | Ticker not found on Yahoo Finance |
| 429 | Too Many Requests | NewsAPI rate limit hit (100/day free) |
| 500 | Internal Server Error | Check server logs |
| 501 | Not Implemented | Module not yet built |

---

## Example Usage

### Python (requests)
```python
import requests

response = requests.post(
    "http://localhost:8000/optimize",
    json={
        "tickers": ["AAPL", "MSFT", "GOOGL"],
        "current_weights": {"AAPL": 0.4, "MSFT": 0.4, "GOOGL": 0.2},
        "period": "6mo",
        "risk_free_rate": 0.05
    }
)

result = response.json()
print("Optimal weights:", result["optimal_weights"])
print("Sharpe ratio:", result["sharpe_ratio"])
for ticker, rec in result["recommendations"].items():
    print(f"\n{ticker}: {rec}")
```

### curl
```bash
curl -X POST "http://localhost:8000/optimize" \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["AAPL", "MSFT"],
    "period": "6mo"
  }'
```

### JavaScript (fetch)
```javascript
const response = await fetch('http://localhost:8000/optimize', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    tickers: ['AAPL', 'MSFT', 'GOOGL'],
    period: '6mo'
  })
});
const data = await response.json();
console.log(data.optimal_weights);
```

---

## Rate Limits

| Source | Limit | Notes |
|---|---|---|
| NewsAPI (free) | 100 requests/day | 1 request/ticker/call |
| OpenAI GPT-4 | Depends on plan | ~$0.03/1K tokens |
| OpenAI GPT-3.5 | Depends on plan | ~$0.001/1K tokens (use for testing) |
| yfinance | No hard limit | Avoid hammering — cache results |
| This API | No limit | Single-user demo |