# Setup Guide

Complete installation and configuration guide for the AI-Powered Portfolio Optimizer.

Built by Parmod | [GitHub](https://github.com/Parmodk2310/AI-Powered-Portfolio-Optimizer)

---

## Prerequisites

| Requirement | Version | Check |
|---|---|---|
| Python | 3.9+ | `python --version` |
| pip | Latest | `pip --version` |
| Git | Any | `git --version` |
| Docker (optional) | 20+ | `docker --version` |

---

## Step 1 — Clone the Repository

```bash
git clone https://github.com/Parmodk2310/AI-Powered-Portfolio-Optimizer.git
cd AI-Powered-Portfolio-Optimizer
```

---

## Step 2 — Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt. Always activate before running anything.

---

## Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

This installs all required libraries. First time takes 5-10 minutes.

**Note on PyTorch:** The requirements install CPU-only PyTorch. If you have an NVIDIA GPU:
```bash
pip install torch==2.2.0+cu118 --index-url https://download.pytorch.org/whl/cu118
```

---

## Step 4 — Get API Keys (Free)

You need two API keys. Both have free tiers.

### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key — you won't see it again
5. New accounts get $5 free credit

### NewsAPI Key
1. Go to https://newsapi.org/register
2. Create free account
3. Your API key is shown on the dashboard
4. Free tier: 100 requests/day, 1 month history

---

## Step 5 — Configure Environment

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```bash
# Required
OPENAI_API_KEY=sk-your-openai-key-here
NEWS_API_KEY=your-newsapi-key-here

# Optional — use Gemini instead of OpenAI
GOOGLE_API_KEY=your-gemini-key-here

# Storage path for FAISS index
FAISS_INDEX_PATH=./data/faiss_index

# Logging level
LOG_LEVEL=INFO
```

**Important:** Never commit your `.env` file to GitHub. It is already in `.gitignore`.

---

## Step 6 — Verify Installation

Test each module individually before running the full pipeline.

### Test 1 — Stock Data (no API key needed)
```bash
python src/data/stock_fetcher.py
```
Expected output:
```
Fetching stock data...
              AAPL        MSFT       GOOGL        AMZN
Date
2024-11-07  227.48  415.00  176.16  202.88
...
Daily returns:
              AAPL      MSFT     GOOGL      AMZN
Date
...
```

### Test 2 — News Fetcher (NewsAPI key required)
```bash
python src/data/news_fetcher.py
```
Expected output:
```
Fetching news for AAPL...
  Found 8 articles
Fetching news for MSFT...
  Found 6 articles

AAPL: 8 articles
  - Apple beats Q4 earnings expectations with record iPhone sales
  - Apple Vision Pro sales disappoint analysts in first full quarter
```

### Test 3 — Sentiment Analysis (downloads ~500MB on first run)
```bash
python src/models/sentiment.py
```
Expected output:
```
Loading FinBERT model... (first run downloads ~500MB)
Apple beats earnings expectations with record iPhone sales
  → positive (positive: 0.9123, negative: 0.0312)
...
```

### Test 4 — Portfolio Optimization (no API key needed)
```bash
python src/optimization/portfolio.py
```
Expected output:
```
Optimizing portfolio...

Optimal Portfolio:
  AAPL: 35.2%
  MSFT: 44.8%
  GOOGL: 12.1%
  AMZN: 7.9%

Expected Annual Return: 14.2%
Annual Volatility: 18.5%
Sharpe Ratio: 1.43
```

---

## Step 7 — Run the Application

### Option A — Run Backend + Frontend Separately

**Terminal 1 — Backend:**
```bash
uvicorn src.api.main:app --reload --port 8000
```
Visit: http://localhost:8000/docs

**Terminal 2 — Frontend:**
```bash
streamlit run frontend/app.py
```
Visit: http://localhost:8501

### Option B — Run with Make
```bash
make install      # Install dependencies
make run-backend  # Start FastAPI
make run-frontend # Start Streamlit
make test         # Run all tests
```

### Option C — Run with Docker
```bash
docker-compose up --build
```
- Backend: http://localhost:8000
- Frontend: http://localhost:8501

---

## Step 8 — Run Tests

```bash
pytest tests/ -v
```

Expected output:
```
tests/test_data.py::TestStockFetcher::test_fetch_stock_data_returns_dataframe PASSED
tests/test_data.py::TestStockFetcher::test_fetch_stock_data_has_correct_columns PASSED
tests/test_data.py::TestStockFetcher::test_calculate_returns_no_nan PASSED
tests/test_data.py::TestPortfolioOptimization::test_weights_sum_to_one PASSED
tests/test_data.py::TestPortfolioOptimization::test_weights_non_negative PASSED
tests/test_data.py::TestPortfolioOptimization::test_sharpe_ratio_positive PASSED
```

---

## Common Errors & Fixes

### "ModuleNotFoundError: No module named 'yfinance'"
```bash
pip install -r requirements.txt
```

### "yfinance error: No data found for ticker"
- Check ticker symbol is correct (US stocks: AAPL, MSFT not Apple, Microsoft)
- Check internet connection
- Try: `pip install --upgrade yfinance`

### "NEWS_API_KEY not set"
- Make sure you created `.env` from `.env.example`
- Make sure your NewsAPI key is in `.env`
- Restart your terminal after editing `.env`

### "FinBERT download stuck or slow"
- First run downloads ~500MB — normal, wait for it
- After first run it caches locally
- If stuck: delete `~/.cache/huggingface/` and retry

### "FAISS index not found"
```bash
mkdir data
```
Then run `vector_store.py` first to create the index

### "OpenAI API error: insufficient quota"
- Your $5 free credit is used up
- Switch to `gpt-3.5-turbo` in `rag_pipeline.py` (much cheaper)
- Or use Google Gemini (set `GOOGLE_API_KEY` in `.env`)

### "Port 8000 already in use"
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Mac/Linux
lsof -i :8000
kill -9 <pid>
```

### Docker build fails
```bash
docker system prune -f
docker-compose up --build
```

---

## Project Structure Reference

```
AI-Powered-Portfolio-Optimizer/
├── src/
│   ├── data/
│   │   ├── stock_fetcher.py     # yfinance stock data
│   │   ├── news_fetcher.py      # NewsAPI financial news
│   │   └── vector_store.py      # FAISS embedding store
│   ├── models/
│   │   ├── sentiment.py         # FinBERT sentiment analysis
│   │   └── rag_pipeline.py      # LangChain RAG recommendations
│   ├── optimization/
│   │   ├── portfolio.py         # Sharpe ratio optimization
│   │   └── risk.py              # VaR, volatility, drawdown
│   └── api/
│       └── main.py              # FastAPI backend
├── frontend/
│   └── app.py                   # Streamlit dashboard
├── tests/
│   └── test_data.py             # pytest test suite
├── notebooks/
│   └── 01_data_exploration.ipynb
├── docs/
│   ├── architecture.md          # This file's companion
│   ├── api_reference.md         # API endpoint documentation
│   └── setup.md                 # This file
├── requirements.txt             # All dependencies
├── Dockerfile                   # Container definition
├── docker-compose.yml           # Multi-service orchestration
├── Makefile                     # Convenience commands
├── .env.example                 # Environment template
└── README.md                    # Project overview
```

---

## Hugging Face Spaces Deployment

1. Create account at https://huggingface.co
2. Go to: https://huggingface.co/new-space
3. Settings: SDK = Streamlit, Visibility = Public
4. Add Secrets (Settings → Variables and Secrets):
   ```
   OPENAI_API_KEY = your_key
   NEWS_API_KEY = your_key
   ```
5. Copy `frontend/app.py` → `app.py` (root of Space)
6. Copy `requirements.txt` to Space
7. Push and wait 5-10 minutes for build