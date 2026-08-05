"""
backend/main.py  — FastAPI Backend for AI Portfolio Optimizer Mobile App
=======================================================================
REST API with JWT auth that wraps your existing src.* modules.
Endpoints: Auth, Portfolios, Holdings, Analysis, History, Benchmark
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..")
)

sys.path.insert(0, PROJECT_ROOT)

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.config import get_settings

# ── Import your existing src modules ─────────────────────────────────────────
try:
    from src.database.db import (
        init_db, get_user_by_username, create_user, verify_password,
        get_user_portfolios, create_portfolio, delete_portfolio,
        get_portfolio_holdings, add_holding, delete_holding,
        get_portfolio_history, save_optimization_run,
        verify_identity, reset_password
    )
    from src.data.stock_fetcher import fetch_stock_data
    from src.models.sentiment import aggregate_sentiment
    from src.optimization.portfolio import PortfolioOptimizer
    from src.optimization.risk import RiskAnalyzer
    from src.optimization.combined_signal import CombinedSignal
    from src.models.rag_pipeline import RAGPipeline
    SRC_AVAILABLE = True
except Exception as e:
    print(f"Warning: src modules not available: {e}")
    SRC_AVAILABLE = False

# ── App init ─────────────────────────────────────────────────────────────────
settings = get_settings()
app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# ── DB init ──────────────────────────────────────────────────────────────────
if SRC_AVAILABLE:
    init_db()

# ── JWT helpers ──────────────────────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        username = payload.get("username")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"id": int(user_id), "username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# ── Pydantic Models ───────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3)
    email: str
    password: str = Field(..., min_length=6)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class PortfolioCreate(BaseModel):
    name: str
    description: str = ""
    currency: str = "USD"

class HoldingCreate(BaseModel):
    ticker: str
    quantity: float = Field(..., gt=0)
    buy_price: float = Field(..., gt=0)
    buy_currency: str = "USD"

class AnalysisRequest(BaseModel):
    portfolio_id: int
    alpha: float = Field(0.6, ge=0.0, le=1.0)
    portfolio_value: float = Field(100000, ge=1000)
    use_llm: bool = True

class ForgotPasswordRequest(BaseModel):
    username: str
    email: str
    new_password: str = Field(..., min_length=6)

# ── INDIAN STOCKS MAP ─────────────────────────────────────────────────────────
INDIAN_STOCKS = {
    "TCS": "TCS.NS", "INFY": "INFY.NS", "RELIANCE": "RELIANCE.NS",
    "WIPRO": "WIPRO.NS", "HDFCBANK": "HDFCBANK.NS", "ICICIBANK": "ICICIBANK.NS",
    "TATAMOTORS": "TATAMOTORS.NS", "BAJFINANCE": "BAJFINANCE.NS",
    "SBIN": "SBIN.NS", "AXISBANK": "AXISBANK.NS", "BHARTIARTL": "BHARTIARTL.NS",
    "ITC": "ITC.NS", "LT": "LT.NS", "MARUTI": "MARUTI.NS",
    "NESTLEIND": "NESTLEIND.NS", "TITAN": "TITAN.NS", "HINDUNILVR": "HINDUNILVR.NS",
    "KOTAKBANK": "KOTAKBANK.NS", "ASIANPAINT": "ASIANPAINT.NS", "ULTRACEMCO": "ULTRACEMCO.NS"
}

def normalize_ticker(ticker: str) -> tuple:
    t = ticker.strip().upper()
    if t in INDIAN_STOCKS:
        return INDIAN_STOCKS[t], t, "IN"
    if t.endswith(".NS"):
        return t, t.replace(".NS", ""), "IN"
    return t, t, "US"

# ═══════════════════════════════════════════════════════════════════════════════
# AUTH ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    user = get_user_by_username(req.username)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token({"sub": str(user["id"]), "username": user["username"]})
    return {"access_token": token, "user": {"id": user["id"], "username": user["username"], "email": user.get("email", "")}}

@app.post("/auth/register", response_model=TokenResponse)
def register(req: RegisterRequest):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    user = create_user(req.username, req.email, req.password)
    if not user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    create_portfolio(user["id"], "My Portfolio", "Default portfolio", "USD")
    token = create_access_token({"sub": str(user["id"]), "username": user["username"]})
    return {"access_token": token, "user": {"id": user["id"], "username": user["username"], "email": req.email}}

@app.post("/auth/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    if not verify_identity(req.username, req.email):
        raise HTTPException(status_code=400, detail="No account matches that username and email")
    ok = reset_password(req.username, req.email, req.new_password)
    if not ok:
        raise HTTPException(status_code=500, detail="Password reset failed")
    return {"message": "Password reset successfully"}

@app.get("/auth/me")
def me(user: dict = Depends(get_current_user)):
    return user

# ═══════════════════════════════════════════════════════════════════════════════
# PORTFOLIO ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/portfolios")
def list_portfolios(user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    return get_user_portfolios(user["id"])

@app.post("/portfolios")
def create_portfolio_endpoint(req: PortfolioCreate, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    p = create_portfolio(user["id"], req.name, req.description, req.currency)
    if not p:
        raise HTTPException(status_code=400, detail="Failed to create portfolio")
    return p

@app.delete("/portfolios/{portfolio_id}")
def delete_portfolio_endpoint(portfolio_id: int, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    delete_portfolio(portfolio_id)
    return {"message": "Portfolio deleted"}

# ═══════════════════════════════════════════════════════════════════════════════
# HOLDING ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/portfolios/{portfolio_id}/holdings")
def list_holdings(portfolio_id: int, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    return get_portfolio_holdings(portfolio_id)

@app.post("/portfolios/{portfolio_id}/holdings")
def add_holding_endpoint(portfolio_id: int, req: HoldingCreate, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    yf_ticker, display, exchange = normalize_ticker(req.ticker)
    result = add_holding(
        portfolio_id=portfolio_id,
        ticker=yf_ticker,
        display_name=display,
        exchange=exchange,
        quantity=req.quantity,
        buy_price=req.buy_price,
        buy_currency=req.buy_currency,
        buy_date=datetime.now()
    )
    if not result:
        raise HTTPException(status_code=400, detail="Failed to add holding")
    return result

@app.delete("/holdings/{holding_id}")
def remove_holding(holding_id: int, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    delete_holding(holding_id)
    return {"message": "Holding deleted"}

# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/analysis/run")
def run_analysis(req: AnalysisRequest, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")

    import pandas as pd
    import numpy as np

    holdings = get_portfolio_holdings(req.portfolio_id)
    if len(holdings) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 holdings")

    tickers = [h["ticker"] for h in holdings]
    display_names = {h["ticker"]: h["display_name"] for h in holdings}

    # Fetch prices
    try:
        prices = fetch_stock_data(tickers, period="1y")
        if isinstance(prices.columns, pd.MultiIndex):
            if "Close" in prices.columns.get_level_values(0):
                prices = prices["Close"]
        if isinstance(prices, pd.Series):
            prices = prices.to_frame()
        available = [t for t in tickers if t in prices.columns]
        if not available:
            raise ValueError("No valid tickers returned")
        prices = prices[available]
        if isinstance(prices, pd.Series):
            prices = prices.to_frame()
        returns = prices.pct_change().dropna()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price fetch failed: {str(e)}")

    # Optimize
    try:
        optimizer = PortfolioOptimizer(prices)
        opt_result = optimizer.optimize()
        baseline = optimizer.equal_weight_baseline()
        frontier_df = optimizer.efficient_frontier(n_points=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

    # Sentiment
    sentiment_scores = {}
    all_news = {}
    for ticker in available:
        try:
            from src.data.news_fetcher import fetch_news
            news = fetch_news(ticker)
            all_news[ticker] = news
            headlines = [a.get("title", "") for a in news if a.get("title")]
            sentiment_scores[ticker] = aggregate_sentiment(headlines) if headlines else 0.0
        except Exception:
            sentiment_scores[ticker] = 0.0
            all_news[ticker] = []

    # Combine
    try:
        combiner = CombinedSignal(opt_result, sentiment_scores)
        combined = combiner.combine(alpha=req.alpha)
        final_weights = combined["final_weights"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signal combination failed: {str(e)}")

    # Risk
    try:
        risk_analyzer = RiskAnalyzer(prices)
        risk_report = risk_analyzer.full_risk_report(final_weights, req.portfolio_value)
    except Exception as e:
        risk_report = {}

    # LLM
    recommendations = []
    if req.use_llm:
        try:
            rag = RAGPipeline()
            for ticker in available:
                articles_text = [a.get("title", "") for a in all_news.get(ticker, []) if a.get("title")]
                rec = rag.generate_recommendation(
                    ticker=ticker,
                    sentiment_score=sentiment_scores.get(ticker, 0.0),
                    portfolio_weight=final_weights.get(ticker, 0.0),
                    retrieved_articles=articles_text
                )
                recommendations.append(rec)
        except Exception:
            pass

    # Save to history
    safe_opt = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in opt_result.items()}
    safe_opt["baseline_sharpe"] = baseline["sharpe_ratio"]
    save_optimization_run(
        portfolio_id=req.portfolio_id,
        alpha=req.alpha,
        opt_result=safe_opt,
        sentiment_scores=sentiment_scores,
        recommendations=recommendations,
        risk_report=risk_report
    )

    return {
        "tickers": available,
        "display_names": display_names,
        "opt_result": {
            "sharpe_ratio": float(opt_result["sharpe_ratio"]),
            "expected_return": float(opt_result["expected_return"]),
            "volatility": float(opt_result["volatility"]),
            "weights": {k: float(v) for k, v in opt_result["weights"].items()},
        },
        "baseline": {
            "sharpe_ratio": float(baseline["sharpe_ratio"]),
            "expected_return": float(baseline["expected_return"]),
            "volatility": float(baseline["volatility"]),
        },
        "final_weights": {k: float(v) for k, v in final_weights.items()},
        "weight_changes": {k: {"change": float(v["change"])} for k, v in combined["weight_changes"].items()},
        "sentiment_scores": sentiment_scores,
        "risk_report": risk_report,
        "recommendations": recommendations,
        "frontier": {
            "volatility": frontier_df["volatility"].tolist(),
            "return": frontier_df["return"].tolist(),
            "sharpe": frontier_df["sharpe"].tolist(),
        }
    }

@app.get("/portfolios/{portfolio_id}/history")
def get_history(portfolio_id: int, limit: int = 30, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    return get_portfolio_history(portfolio_id, limit)

# ═══════════════════════════════════════════════════════════════════════════════
# BENCHMARK ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/benchmark/spy")
def benchmark_spy(portfolio_id: int, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")

    import pandas as pd
    import numpy as np

    results = {}  # In real impl, fetch from session or re-run analysis
    holdings = get_portfolio_holdings(portfolio_id)
    tickers = [h["ticker"] for h in holdings]

    try:
        prices = fetch_stock_data(tickers + ["SPY"], period="1y")
        if isinstance(prices.columns, pd.MultiIndex):
            prices = prices["Close"]

        returns = prices.pct_change().dropna()
        if isinstance(returns, pd.Series):
            returns = returns.to_frame(name=prices.columns[0] if hasattr(prices, "columns") else "price")

        spy_returns = returns["SPY"] if "SPY" in returns.columns else None
        if spy_returns is None:
            raise HTTPException(status_code=500, detail="SPY data not available")

        available_tickers = [ticker for ticker in tickers if ticker in returns.columns]
        if not available_tickers:
            raise HTTPException(status_code=500, detail="No portfolio data available")

        portfolio_returns = returns.loc[:, available_tickers].mean(axis=1).astype(float)
        spy_returns = pd.Series(spy_returns, index=returns.index, dtype=float)

        cum_portfolio = pd.Series(
            np.cumprod(1 + portfolio_returns.to_numpy()),
            index=portfolio_returns.index,
            dtype=float,
        )
        cum_spy = pd.Series(
            np.cumprod(1 + spy_returns.to_numpy()),
            index=spy_returns.index,
            dtype=float,
        )

        return {
            "dates": [d.strftime("%Y-%m-%d") for d in cum_portfolio.index],
            "portfolio": cum_portfolio.tolist(),
            "spy": cum_spy.tolist(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {str(e)}")
    
@app.get("/")
def root():
    return {"message": "AI Portfolio Optimizer API", "docs": "/docs", "health": "/health"}
# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
def health():
    return {"status": "ok", "version": settings.VERSION, "src_available": SRC_AVAILABLE}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)