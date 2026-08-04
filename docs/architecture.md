# System Architecture

## Overview

AI-Powered Portfolio Optimizer combines two signals to generate portfolio rebalancing recommendations:

- **Quantitative signal** — Modern Portfolio Theory, Sharpe ratio maximization using scipy
- **Sentiment signal** — FinBERT analysis of real-time financial news via RAG pipeline

Built by Parmod | [GitHub](https://github.com/Parmodk2310/AI-Powered-Portfolio-Optimizer)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER (Browser)                       │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Streamlit Frontend (Port 8501)             │
│                   frontend/app.py                       │
│  - Stock ticker input                                   │
│  - Portfolio weight input                               │
│  - Charts: pie, bar, line (Plotly)                      │
│  - Rebalancing table                                    │
│  - LLM recommendation display                           │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP POST /optimize
                          ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                │
│                  src/api/main.py                        │
│  - Request validation (Pydantic)                        │
│  - Orchestrates all modules                             │
│  - Returns JSON response                                │
│  - Auto docs at /docs                                   │
└──────┬──────────────────┬──────────────────┬────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐  ┌─────────────────┐  ┌────────────────┐
│ Data Layer  │  │   LLM Layer     │  │  Optimization  │
│             │  │                 │  │    Layer       │
│stock_fetcher│  │ sentiment.py    │  │ portfolio.py   │
│news_fetcher │  │ rag_pipeline.py │  │ risk.py        │
│vector_store │  │                 │  │                │
└──────┬──────┘  └────────┬────────┘  └───────┬────────┘
       │                  │                   │
       ▼                  ▼                   ▼
┌─────────────┐  ┌─────────────────┐  ┌────────────────┐
│  yfinance   │  │ FinBERT Model   │  │ scipy.optimize │
│  NewsAPI    │  │ LangChain       │  │ numpy/pandas   │
│  FAISS      │  │ OpenAI GPT-4    │  │                │
└─────────────┘  └─────────────────┘  └────────────────┘
```

---

## Component Details

### 1. Data Layer (`src/data/`)

**stock_fetcher.py**
- Fetches historical OHLCV data using yfinance
- Calculates daily percentage returns
- Fetches company metadata (sector, market cap)
- Input: list of ticker symbols + time period
- Output: pandas DataFrame of closing prices and returns

**news_fetcher.py**
- Fetches recent financial news via NewsAPI
- Rate limited to 1 request/second (free tier limit)
- Filters by ticker + company name for relevance
- Input: ticker symbol
- Output: list of article dicts with title, description, text, source

**vector_store.py**
- Embeds news articles using `all-MiniLM-L6-v2` sentence transformer
- Stores embeddings in FAISS IndexFlatL2
- Enables fast semantic similarity search
- Persists index to disk for reuse
- Input: list of article dicts
- Output: searchable FAISS index

---

### 2. LLM Layer (`src/models/`)

**sentiment.py**
- Uses `ProsusAI/finbert` — BERT fine-tuned on financial text
- Classifies each article as positive / negative / neutral
- Returns confidence scores for each class
- Aggregates multiple articles into single score per ticker
- Score range: -1.0 (very negative) to +1.0 (very positive)

**rag_pipeline.py**
- Retrieves top-K relevant articles from FAISS for each ticker
- Formats prompt with: news context + sentiment score + optimization result
- Calls GPT-4 / Gemini via LangChain
- Returns plain English recommendation per ticker
- Temperature: 0.3 (consistent, not creative)

---

### 3. Optimization Layer (`src/optimization/`)

**portfolio.py**
- Implements Modern Portfolio Theory (Markowitz, 1952)
- Maximizes Sharpe ratio using scipy SLSQP optimizer
- Constraints: weights sum to 1.0, no short selling (weights ≥ 0)
- Annualizes metrics using 252 trading days
- Input: returns DataFrame + risk-free rate
- Output: optimal weights, expected return, volatility, Sharpe ratio

**risk.py**
- **Volatility**: annualized standard deviation of returns per stock
- **Value at Risk (VaR)**: maximum expected daily loss at 95% confidence
- **Max Drawdown**: largest peak-to-trough decline in history
- **Correlation Matrix**: pairwise correlations between all stocks

---

### 4. API Layer (`src/api/`)

**main.py**
- FastAPI application with CORS enabled
- Pydantic models for request/response validation
- Orchestrates full pipeline on `/optimize` endpoint
- Auto-generated OpenAPI docs at `/docs`
- Health check at `/health`

---

### 5. Frontend (`frontend/`)

**app.py**
- Streamlit single-page application
- Sidebar: ticker input, period selector, risk-free rate slider
- Main area: metrics, pie chart, bar chart, line chart
- Rebalancing table with BUY/SELL/HOLD actions
- Sentiment display per ticker
- LLM recommendations section

---

## Data Flow (Request Lifecycle)

```
1. User enters: ["AAPL", "MSFT", "GOOGL"] + current weights
2. Streamlit sends POST /optimize to FastAPI
3. FastAPI receives request, validates with Pydantic
4. stock_fetcher.py → fetches 6-month price history from yfinance
5. calculate_returns() → computes daily % returns
6. news_fetcher.py → fetches last 7 days news per ticker (rate limited)
7. vector_store.py → embeds articles, stores in FAISS
8. sentiment.py → runs FinBERT on each article, aggregates score per ticker
9. portfolio.py → runs Sharpe ratio optimization → returns optimal weights
10. risk.py → calculates VaR, volatility, correlation, max drawdown
11. rag_pipeline.py → retrieves relevant news + calls GPT-4 → recommendation
12. FastAPI returns JSON with: weights, metrics, risk, recommendations
13. Streamlit renders: pie chart, bar chart, price history, rebalancing table
14. User sees: what to buy, what to sell, why
```

---

## Technology Choices — Rationale

| Decision | Choice | Why |
|---|---|---|
| Sentiment model | FinBERT | Fine-tuned on financial text — more accurate than general BERT for finance |
| Vector store | FAISS | In-memory, no server needed, fast for <10K documents |
| Optimization | scipy SLSQP | Handles constraints cleanly, shows math understanding vs black-box libraries |
| LLM framework | LangChain | Internship experience, supports both OpenAI and Gemini interchangeably |
| API framework | FastAPI | Async, auto-docs, Pydantic validation — better than Flask for this use case |
| Frontend | Streamlit | Fast to build, native Python, free deployment on Hugging Face Spaces |
| Containerization | Docker | Reproducible environment, single command deployment |

---

## Deployment Architecture

### Local Development
```
localhost:8000  →  FastAPI backend (uvicorn)
localhost:8501  →  Streamlit frontend
```

### Docker
```
docker-compose up --build
  backend  → container:8000
  frontend → container:8501
```

### Production (Hugging Face Spaces)
```
Streamlit app deployed directly on HF Spaces
API keys stored as Space Secrets
Free tier — public URL
```

---

## Known Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| NewsAPI free: 100 req/day | Limited tickers per day | Cache results, batch requests |
| FinBERT slow on CPU | ~2-3s per article | Cache sentiment scores |
| No short selling | Suboptimal in bear markets | Acceptable for retail investors |
| No transaction costs | Optimization ignores trading fees | Note in output |
| No real-time data | Refreshes on each request | Add scheduled refresh later |
| No authentication | Single-user only | Add JWT auth for production |
| OpenAI API costs | ~$0.01-0.03 per request | Use gpt-3.5-turbo for testing |

---

## Future Improvements

- Add user authentication (JWT)
- Add Redis caching for sentiment scores
- Add support for Indian stocks (NSE/BSE via nsepy)
- Add portfolio backtesting module
- Add email alerts for rebalancing recommendations
- Add support for crypto assets
- Replace OpenAI with local LLM (Ollama) for zero API cost