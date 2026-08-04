# AI-Powered Portfolio Optimizer

An investment-analysis application that combines market data, Modern Portfolio Theory, financial-news sentiment, and LLM-generated explanations to help users review and rebalance equity portfolios.

The project supports US equities and a selection of Indian NSE stocks. It includes a Streamlit dashboard, a FastAPI service, and a Flutter mobile client.

> **Disclaimer:** This project is for educational and research use only. It does not provide financial advice or guarantee investment performance.

## Features

- Fetches historical price data with Yahoo Finance (`yfinance`)
- Maximizes risk-adjusted return using Sharpe-ratio optimization with no short selling
- Blends quantitative weights with FinBERT financial-news sentiment
- Calculates volatility, Value at Risk (VaR), maximum drawdown, and correlations
- Retrieves relevant articles through a FAISS vector store
- Generates plain-English portfolio recommendations with Groq LLMs when configured
- Provides portfolio analysis, backtesting, ticker search, and comparison endpoints
- Includes login, portfolio history, and interactive visualizations in the Streamlit UI

## Architecture

```text
Streamlit dashboard / Flutter client
              |
           FastAPI
              |
  +-----------+-------------------+
  |           |                   |
Market data  AI & sentiment   Optimization & risk
yfinance     NewsAPI/FinBERT  Sharpe, VaR, drawdown
FAISS + LLM                  correlations, backtests
```

## Quick start

### Prerequisites

- Python 3.10 or later
- pip
- Docker (optional)

### 1. Clone and create an environment

```bash
git clone https://github.com/Parmodk2310/AI-Powered-Portfolio-Optimizer.git
cd AI-Powered-Portfolio-Optimizer
python -m venv .venv
```

Activate it:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

The first sentiment-analysis run downloads the FinBERT model, which can take several minutes.

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
# Enables financial-news retrieval and sentiment context
NEWS_API_KEY=your_newsapi_key

# Enables LLM recommendations
GROQ_API_KEY=your_groq_api_key

# Optional: location for persisted FAISS data
FAISS_INDEX_PATH=./data/faiss_index

# Optional: set true to use API demo behaviour where supported
DEMO_MODE=false
```

Historical-price analysis works without API keys. `NEWS_API_KEY` and `GROQ_API_KEY` enable the corresponding enrichment features.

### 4. Run the application

Start the API in one terminal:

```bash
uvicorn src.api.main:app --reload --port 8000
```

Then start the dashboard in another:

```bash
streamlit run frontend/app.py
```

Open the dashboard at `http://localhost:8501` and the API documentation at `http://localhost:8000/docs`.

## Docker

With `.env` configured, run both services with:

```bash
docker-compose up --build
```

- Dashboard: `http://localhost:8501`
- API: `http://localhost:8000`

## API highlights

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Service and configuration status |
| `POST /optimize` | Full quant, sentiment, risk, and recommendation pipeline |
| `GET /portfolio/report` | Quantitative portfolio report |
| `POST /portfolio/backtest` | Compare optimized, equal-weight, and SPY strategies |
| `GET /sentiment/{ticker}` | Financial-news sentiment for a ticker |
| `GET /news/{ticker}` | Recent articles for a ticker |
| `GET /tickers/search` | Find a ticker by symbol or name |
| `POST /combine` | Blend quantitative and sentiment signals |

Example optimization request:

```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{"tickers":["AAPL","MSFT","GOOGL"],"alpha":0.6,"period":"1y","use_llm":false}'
```

`alpha` controls the allocation blend: `1.0` uses only the quantitative signal, while `0.0` uses only the sentiment signal.

## Project structure

### Full deep-dive folder structure

The tree below lists the project source, configuration, documentation, notebooks, and checked-in data assets. Local secrets (`.env`), caches (`__pycache__`), IDE settings, dependency directories (`node_modules`), and generated Flutter build artifacts are intentionally excluded; they are machine-specific or recreated by tooling. The `flutter/` directory is a vendored Flutter SDK and is likewise excluded.

```text
AI-Powered-Portfolio-Optimizer/
├── .dockerignore                         # Docker build exclusions
├── .env.example                          # Environment-variable template
├── .gitignore                            # Git exclusions
├── Dockerfile                            # Streamlit container image
├── Dockerfile.api                        # FastAPI container image
├── docker-compose.yml                    # Local frontend + API services
├── LICENSE                               # MIT license
├── Makefile                              # Development shortcuts
├── package.json                          # JavaScript tooling metadata
├── package-lock.json                     # Locked JavaScript dependencies
├── requirements.txt                      # Full Python environment
├── requirements-backend.txt              # Backend-focused Python dependencies
├── requirements-frontend.txt             # Frontend-focused Python dependencies
├── requirements-dev.txt                  # Development/test dependencies
├── JPM_2025_AI_Portfolio_Optimizer_v2.pptx # Project presentation
├── README.md                             # Project overview (this file)
│
├── src/                                  # Core Python application modules
│   ├── api/
│   │   └── main.py                       # Analysis API and public endpoints
│   ├── data/
│   │   ├── news_fetcher.py               # NewsAPI retrieval utilities
│   │   ├── pipeline_test.py              # End-to-end pipeline exercise
│   │   ├── stock_fetcher.py              # Yahoo Finance market-data retrieval
│   │   └── vector_store.py               # FAISS indexing and similarity search
│   ├── database/
│   │   ├── db.py                         # SQLite access and persistence helpers
│   │   └── models.py                     # Database models
│   ├── models/
│   │   ├── rag_pipeline.py               # Retrieval-augmented LLM recommendations
│   │   └── sentiment.py                  # FinBERT sentiment scoring
│   └── optimization/
│       ├── combined_signal.py             # Quantitative/sentiment signal blending
│       ├── portfolio.py                   # Sharpe-ratio portfolio optimizer
│       └── risk.py                        # VaR, drawdown, volatility, correlation
│
├── frontend/                             # Streamlit web application
│   ├── app.py                            # Dashboard entry point
│   ├── logo.png                          # Dashboard logo asset
│   ├── style.css                         # Dashboard styling
│   ├── pages/
│   │   ├── 1_Login.py                    # Authentication page
│   │   ├── 2_Portfolio.py                # Portfolio management page
│   │   ├── 3_Analysis.py                 # Portfolio analysis page
│   │   ├── 4_History.py                  # Saved-analysis history page
│   │   ├── 5_Compare.py                  # Portfolio comparison page
│   │   ├── clear_history.py              # History cleanup action
│   │   └── report_generator.py           # Export/report generation utilities
│   
│
├── backend/                              # Authenticated/mobile-oriented API layer
│   ├── .env.example                      # Backend configuration template
│   ├── Dockerfile                        # Backend container image
│   ├── requirements.txt                  # Backend dependencies
│   └── app/
│       ├── __Init__.py                   # Python package marker
│       ├── config.py                     # Application configuration
│       ├── dependencies.py               # Shared API dependencies
│       ├── main.py                       # JWT auth, portfolios, analysis API
│       └── routers/
│           ├── __init__.py
│           ├── analysis.py               # Analysis routes
│           ├── auth.py                   # Authentication routes
│           ├── benchmark.py              # Benchmark routes
│           ├── holdings.py               # Holdings routes
│           └── portfolio.py              # Portfolio routes
│
│
├── data/                                 # Persisted local application data
│   ├── portfolio_optimizer.db             # SQLite database
│   ├── faiss_index/
│   │   ├── documents.pkl                  # Indexed article metadata
│   │   └── index.faiss                    # FAISS vector index
│   └── plots/
│       ├── 01_correlation_matrix.png
│       ├── 01_news_counts.png
│       ├── 01_price_history.png
│       ├── 01_rolling_volatility.png
│       ├── 02_score_distributions.png
│       ├── 02_sentiment_distribution.png
│       ├── 02_sentiment_scores.png
│       ├── 02_sentiment_vs_return.png
│       ├── 03_alpha_sensitivity.png
│       ├── 03_correlation_heatmap.png
│       ├── 03_drawdown.png
│       ├── 03_efficient_frontier.png
│       └── 03_weight_comparison.png
│
├── docs/
│   ├── api_reference.md                   # Endpoint reference
│   ├── architecture.md                    # System design documentation
│   └── setup.md                           # Detailed setup guide
├── notebooks/
│   ├── 01_data_exploration.ipynb          # Market-data exploration
│   ├── 02_sentiment_analysis.ipynb        # Sentiment experiments
│   └── 03_optimization_experiments.ipynb  # Optimization experiments
└── tests/
    └── test_data.py                       # Data and optimization test suite
```

### How the folders work together

| Area | Responsibility | Main entry points |
| --- | --- | --- |
| `src/data` | Retrieves prices and news, then persists semantic news embeddings. | `stock_fetcher.py`, `news_fetcher.py`, `vector_store.py` |
| `src/models` | Scores financial-news sentiment and produces grounded natural-language recommendations. | `sentiment.py`, `rag_pipeline.py` |
| `src/optimization` | Calculates optimized weights, blends signals, and measures portfolio risk. | `portfolio.py`, `combined_signal.py`, `risk.py` |
| `src/api` | Exposes the analysis pipeline through the public FastAPI interface. | `src/api/main.py` |
| `src/database` | Stores users, portfolios, holdings, and analysis history in SQLite. | `db.py`, `models.py` |
| `frontend` | Provides the Streamlit web dashboard for authentication, input, analysis, history, and comparison. | `app.py`, `pages/` |
| `backend/app` | Adds authenticated portfolio-management APIs for the mobile-oriented experience. | `main.py`, `routers/` |
| `data` | Holds local, persisted runtime outputs: the SQLite database, FAISS index, and charts. | `portfolio_optimizer.db`, `faiss_index/`, `plots/` |

### Analysis request flow

```text
User selects holdings and analysis settings
                  |
                  v
Streamlit dashboard or Flutter client
                  |
                  v
FastAPI validates request and normalizes tickers
                  |
      +-----------+-----------+----------------+
      |                       |                |
      v                       v                v
Historical prices        Recent news      Saved holdings
(yfinance)               (NewsAPI)        (SQLite)
      |                       |
      v                       v
Portfolio optimizer      FinBERT + FAISS retrieval
      |                       |
      +-----------+-----------+
                  |
                  v
Signal blending, VaR, drawdown, correlations, and optional LLM rationale
                  |
                  v
Weights, charts, risk report, and BUY/HOLD/REDUCE guidance
```

## Tests

```bash
pytest tests -v
```

## Documentation

- [Setup guide](docs/setup.md)
- [Architecture](docs/architecture.md)
- [API reference](docs/api_reference.md)

## License

Released under the [MIT License](LICENSE).
