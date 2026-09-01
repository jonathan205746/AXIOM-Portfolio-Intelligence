# AI-Powered Portfolio Optimizer

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](docker-compose.yml)

</div>

An AI-powered investment research and portfolio optimization platform that combines market data, Modern Portfolio Theory, financial-news sentiment, and LLM-generated recommendations to help users analyze and rebalance equity portfolios.

This project supports major US equities and a curated set of Indian NSE stocks, with a Streamlit dashboard, FastAPI APIs, and a backend for authenticated portfolio workflows.

> Disclaimer: This project is intended for educational and research use only. It does not provide financial advice or guarantee investment performance.

## Table of Contents

- [What this project does](#what-this-project-does)
- [Key features](#key-features)
- [System architecture](#system-architecture)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Running with Docker](#running-with-docker)
- [Deployment options](#deployment-options)
- [API overview](#api-overview)
- [Testing](#testing)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## What this project does

The application helps users:

- retrieve and analyze historical stock prices
- build optimized portfolios based on risk-adjusted return
- blend quantitative signals with sentiment signals from financial news
- inspect volatility, drawdowns, VaR, correlations, and benchmark comparisons
- review AI-generated narrative explanations and portfolio recommendations
- save portfolios and historical analysis in a local database
- run the workflow through a dashboard, API, and optional backend service

In short, it is a practical prototype for AI-assisted portfolio analysis and decision support.

## Key features

- Historical market-data acquisition using Yahoo Finance
- Sharpe-ratio portfolio optimization with a no-short-selling constraint
- Risk analysis including volatility, drawdown, correlation, and Value at Risk
- Sentiment analysis using financial-news data and FinBERT-style scoring
- FAISS-based retrieval for relevant financial articles and context
- Optional LLM-powered explanations and recommendation generation via Groq or compatible providers
- Interactive dashboard for login, portfolio management, analysis, benchmarking, and history
- SQLite-backed persistence for users, holdings, portfolios, and analysis results
- Docker support for simple local deployment
- AWS EC2 deployment assets for low-cost demo hosting

## System architecture

```text
User
  │
  ├── Streamlit dashboard
  │      │
  │      └── FastAPI analysis layer
  │               │
  │               ├── Market data (yfinance)
  │               ├── Financial news (NewsAPI)
  │               ├── FAISS vector retrieval
  │               ├── Sentiment models
  │               └── Portfolio optimization + risk engine
  │
  └── Authenticated backend app
        └── SQLite database + saved portfolios
```

The system is organized around three main layers:

1. Data layer: stock prices, news, stored portfolio data, and vector search
2. Intelligence layer: sentiment models, optimization logic, and risk calculations
3. Experience layer: dashboard, REST endpoints, and backend portfolio flows

## Tech stack

- Python 3.10+
- FastAPI for API services
- Streamlit for the dashboard UI
- SQLite for local persistence
- Yahoo Finance for market history
- FAISS for article relevance retrieval
- News APIs for financial-news ingestion
- Sentiment and LLM components for AI-generated analysis
- Docker and Docker Compose for containerized deployment
- AWS CloudFormation for simple EC2 hosting templates

## Project structure

```text
AI-Powered-Portfolio-Optimizer/
├── .env.example                 # Sample environment variables
├── .gitignore
├── .dockerignore
├── Dockerfile                   # Frontend/dashboard container
├── Dockerfile.api               # API container
├── LICENSE
├── Makefile                     # Local dev and automation commands
├── README.md                    # GitHub-facing project documentation
├── docker-compose.yml           # Local multi-service orchestration
├── requirements.txt             # Full Python dependency set
├── requirements-backend.txt     # Backend dependencies
├── requirements-frontend.txt    # Frontend dependencies
├── requirements-dev.txt         # Dev/test dependencies
├── backtesting.md               # Backtesting notes and methodology
├── deploy/
│   ├── aws/
│   │   ├── README.md
│   │   └── ec2-stack.yaml
│   └── ec2/
│       └── README.md
├── docs/
│   ├── api_reference.md
│   ├── architecture.md
│   └── setup.md
├── frontend/
│   ├── app.py
│   ├── pages/
│   ├── ui/
│   └── logo.png
├── backend/
│   ├── app/
│   ├── config.py
│   ├── Dockerfile
│   └── requirements.txt
├── src/
│   ├── data/
│   ├── database/
│   ├── models/
│   ├── optimization/
│   └── utils/
├── data/
│   ├── faiss_index/
│   ├── plots/
│   └── portfolio_optimizer.db
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_sentiment_analysis.ipynb
│   └── 03_optimization_experiments.ipynb
├── tests/
│   └── test_data.py
└── JPM_2025_AI_Portfolio_Optimizer_v2.pptx
```

## Quick start

### Prerequisites

- Python 3.10 or later
- pip
- virtual environment support
- Docker and Docker Compose (optional but recommended for local container deployment)

### 1. Clone the repository

```bash
git clone https://github.com/Parmodk2310/AI-Powered-Portfolio-Optimizer.git
cd AI-Powered-Portfolio-Optimizer
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If you want the backend-only dependencies separately, you can also install:

```bash
pip install -r requirements-backend.txt
pip install -r requirements-frontend.txt
```

### 4. Configure environment variables

Copy the example environment file and fill in the settings you need:

```bash
copy .env.example .env
```

or:

```bash
cp .env.example .env
```

Example configuration:

```env
NEWS_API_KEY=your_newsapi_key
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
GROQ_MODEL=openai/gpt-oss-120b
SECRET_KEY=your-secret-key
```

Notes:

- You can run basic price analysis without external API keys.
- News retrieval and sentiment enrichment require a News API key.
- LLM explanations require a provider key such as Groq or Gemini.
- `SECRET_KEY` is used for backend auth and JWT signing.

### 5. Run the application locally

Start the API in one terminal:

```bash
uvicorn backend.app.main:app --reload --port 8000
```

Start the dashboard in another terminal:

```bash
streamlit run frontend/app.py
```

Then open:

- Streamlit dashboard: http://localhost:8501
- API docs: http://localhost:8000/docs

## Configuration

The repository uses environment variables to control external integrations and secure application behavior. The main values are defined in `.env.example` and should be copied into `.env` before running the project.

| Variable | Purpose |
| --- | --- |
| `NEWS_API_KEY` | Financial-news retrieval and relevant article context |
| `GROQ_API_KEY` | LLM-powered recommendation generation |
| `GEMINI_API_KEY` | Optional alternative provider integration |
| `GROQ_MODEL` | LLM model selection for recommendation pipelines |
| `SECRET_KEY` | Secret used for JWT/token creation and session security |
| `FAISS_INDEX_PATH` | Optional location for persisted semantic index storage |
| `DEMO_MODE` | Optional demo-style behavior for simplified flows |

## Running with Docker

With the environment file configured, start the app using Docker Compose:

```bash
docker compose up --build
```

This starts the dashboard on:

- http://localhost:8501

If you also want the API container running:

```bash
docker compose --profile api up --build
```

The API should then be available at:

- http://localhost:8000

## Deployment options

### Local deployment

Use the project directly with Python virtual environments for development and experimentation.

### Docker deployment

This project includes Docker assets for a simple container-based deployment and is suitable for demos and lightweight hosting.

### AWS EC2 deployment

The repository includes a CloudFormation template for a single-host AWS EC2 deployment.

- CloudFormation stack: [deploy/aws/ec2-stack.yaml](deploy/aws/ec2-stack.yaml)
- AWS deployment guide: [deploy/aws/README.md](deploy/aws/README.md)
- Single-host EC2 reference: [deploy/ec2/README.md](deploy/ec2/README.md)

These deployment files are useful for cost-conscious demo hosting and quick validation of the application on a public VM.

## API overview

The FastAPI services expose analysis endpoints for portfolio optimization, benchmarking, search, and sentiment queries.

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Service health and configuration status |
| `POST /optimize` | Full quant + sentiment + risk workflow |
| `GET /portfolio/report` | Portfolio performance summary |
| `POST /portfolio/backtest` | Compare optimized vs baseline strategies |
| `GET /sentiment/{ticker}` | Sentiment score for a symbol |
| `GET /news/{ticker}` | News articles associated with a ticker |
| `GET /tickers/search` | Search or resolve stock symbols |
| `POST /combine` | Combine quantitative and sentiment signals |
| `POST /auth/login` | Log in an existing user |
| `POST /auth/register` | Register a new user |
| `POST /auth/forgot-password` | Reset password flow |

Example optimization call:

```bash
curl -X POST http://localhost:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{"tickers":["AAPL","MSFT","GOOGL"],"alpha":0.6,"period":"1y","use_llm":false}'
```

The `alpha` parameter controls the blending between quantitative optimization and sentiment influence. An `alpha` of `1.0` emphasizes the quantitative signal, while `0.0` shifts fully toward sentiment.

## Testing

Run the project test suite with:

```bash
pytest tests -v
```

The project also includes a Makefile with development automation for formatting, linting, and packaging tasks:

```bash
make help
```

## Documentation

Detailed documentation is available in the `docs/` folder:

- [Setup guide](docs/setup.md)
- [Architecture overview](docs/architecture.md)
- [API reference](docs/api_reference.md)

## Contributing

Contributions are welcome.

If you want to improve this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes and test them locally
4. Open a pull request with a clear description

Please keep changes focused, document new behavior, and validate with the existing test workflow when possible.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

This project builds on open-source libraries and research tools for portfolio optimization, financial analytics, and machine learning workflows.

If you are using this project for research, learning, or experimentation, we encourage you to cite or reference the repository and its associated documentation.
