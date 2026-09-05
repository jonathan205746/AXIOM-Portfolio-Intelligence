"""
backend/main.py  — FastAPI Backend for AI Portfolio Optimizer Mobile App
=======================================================================
REST API with JWT auth that wraps your existing src.* modules.
Endpoints: Auth, Portfolios, Holdings, Analysis, History, Benchmark
"""

import os
import sys
import logging

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

sys.path.insert(0, PROJECT_ROOT)

from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from jose import JWTError, jwt

from backend.config import get_settings
from src.auth.password_reset import GENERIC_RESPONSE, request_password_reset
logger = logging.getLogger(__name__)
# ── Import your existing src modules ─────────────────────────────────────────
try:
    from src.database.db import (
        init_db,
        authenticate_user,
        create_user,
        get_user_by_id,
        get_user_portfolios,
        create_portfolio,
        delete_portfolio,
        get_portfolio_for_user,
        get_portfolio_holdings,
        add_holding,
        delete_holding,
        get_portfolio_history,
        save_optimization_run,
        reset_password_with_code,
    )
    from src.data.stock_fetcher import fetch_stock_data
    from src.models.sentiment import aggregate_sentiment
    from src.optimization.portfolio import PortfolioOptimizer
    from src.optimization.risk import RiskAnalyzer
    from src.optimization.combined_signal import CombinedSignal
    from src.optimization.health_score import HealthScoreEngine
    from src.optimization.adaptive_optimizer import AdaptiveHealthOptimizer
    from src.models.rag_pipeline import RAGPipeline
    from src.auth.ses_email import (
        EmailDeliveryError,
        send_password_reset_template,
     )
    SRC_AVAILABLE = True
except Exception as e:
    print(f"Warning: src modules not available: {e}")
    SRC_AVAILABLE = False

# ── App init ─────────────────────────────────────────────────────────────────
settings = get_settings()
app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)

# ── DB init ──────────────────────────────────────────────────────────────────
if SRC_AVAILABLE:
    init_db()


# ── JWT helpers ──────────────────────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"iat": now, "exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = get_user_by_id(int(user_id)) if SRC_AVAILABLE else None
        if not user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ── Pydantic Models ───────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=72)


class RegisterRequest(BaseModel):
    username: str = Field(
        ..., min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$"
    )
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class PasswordResetRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    code: str = Field(..., pattern=r"^\d{6}$")
    new_password: str = Field(..., min_length=12, max_length=72)


class PortfolioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)
    currency: Literal["USD", "INR"] = "USD"


class HoldingCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20, pattern=r"^[A-Za-z0-9.^-]+$")
    quantity: float = Field(..., gt=0)
    buy_price: float = Field(..., gt=0)
    buy_currency: Literal["USD", "INR"] = "USD"


class AnalysisRequest(BaseModel):
    portfolio_id: int = Field(..., gt=0)
    alpha: float = Field(0.6, ge=0.0, le=1.0)
    portfolio_value: float = Field(100000, ge=1000)
    use_llm: bool = True


def require_portfolio(portfolio_id: int, user_id: int) -> dict:
    portfolio = get_portfolio_for_user(portfolio_id, user_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


# ── INDIAN STOCKS MAP ─────────────────────────────────────────────────────────
INDIAN_STOCKS = {
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "RELIANCE": "RELIANCE.NS",
    "WIPRO": "WIPRO.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "TATAMOTORS": "TATAMOTORS.NS",
    "BAJFINANCE": "BAJFINANCE.NS",
    "SBIN": "SBIN.NS",
    "AXISBANK": "AXISBANK.NS",
    "BHARTIARTL": "BHARTIARTL.NS",
    "ITC": "ITC.NS",
    "LT": "LT.NS",
    "MARUTI": "MARUTI.NS",
    "NESTLEIND": "NESTLEIND.NS",
    "TITAN": "TITAN.NS",
    "HINDUNILVR": "HINDUNILVR.NS",
    "KOTAKBANK": "KOTAKBANK.NS",
    "ASIANPAINT": "ASIANPAINT.NS",
    "ULTRACEMCO": "ULTRACEMCO.NS",
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

    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": str(user["id"]), "username": user["username"]})
    return {
        "access_token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user.get("email", ""),
        },
    }


@app.post("/auth/register", response_model=TokenResponse)
def register(req: RegisterRequest):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    user = create_user(req.username, req.email, req.password)
    if not user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    create_portfolio(user["id"], "My Portfolio", "Default portfolio", "USD")
    token = create_access_token({"sub": str(user["id"]), "username": user["username"]})
    return {
        "access_token": token,
        "user": {"id": user["id"], "username": user["username"], "email": req.email},
    }


@app.get("/auth/me")
def me(user: dict = Depends(get_current_user)):
    return user


@app.post("/auth/password-reset/request")
def password_reset_request(req: PasswordResetRequest):
    if not SRC_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Backend modules not loaded",
        )

    try:
        request_password_reset(
            req.username,
            str(req.email),
        )

    except EmailDeliveryError:
        logger.exception(
            "Password-reset email delivery failed"
        )
        raise HTTPException(
            status_code=503,
            detail="Password-reset email could not be delivered. Please try again.",
        )

    return {"message": GENERIC_RESPONSE}


@app.post("/auth/password-reset/confirm")
def password_reset_confirm(req: PasswordResetConfirm):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    changed = reset_password_with_code(
        req.username,
        str(req.email),
        req.code,
        req.new_password,
        settings.PASSWORD_RESET_MAX_ATTEMPTS,
    )
    if not changed:
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")
    return {"message": "Password reset complete"}


# ═══════════════════════════════════════════════════════════════════════════════
# PORTFOLIO ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════


@app.get("/portfolios")
def list_portfolios(user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    return get_user_portfolios(user["id"])


@app.post("/portfolios")
def create_portfolio_endpoint(
    req: PortfolioCreate, user: dict = Depends(get_current_user)
):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    p = create_portfolio(user["id"], req.name, req.description, req.currency)
    if not p:
        raise HTTPException(status_code=400, detail="Failed to create portfolio")
    return p


@app.delete("/portfolios/{portfolio_id}")
def delete_portfolio_endpoint(
    portfolio_id: int, user: dict = Depends(get_current_user)
):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    if not delete_portfolio(portfolio_id, user_id=user["id"]):
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return {"message": "Portfolio deleted"}


# ═══════════════════════════════════════════════════════════════════════════════
# HOLDING ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════


@app.get("/portfolios/{portfolio_id}/holdings")
def list_holdings(portfolio_id: int, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    require_portfolio(portfolio_id, user["id"])
    return get_portfolio_holdings(portfolio_id, user_id=user["id"])


@app.post("/portfolios/{portfolio_id}/holdings")
def add_holding_endpoint(
    portfolio_id: int, req: HoldingCreate, user: dict = Depends(get_current_user)
):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    require_portfolio(portfolio_id, user["id"])
    yf_ticker, display, exchange = normalize_ticker(req.ticker)
    result = add_holding(
        portfolio_id=portfolio_id,
        ticker=yf_ticker,
        display_name=display,
        exchange=exchange,
        quantity=req.quantity,
        buy_price=req.buy_price,
        buy_currency=req.buy_currency,
        buy_date=datetime.now(),
    )
    if not result:
        raise HTTPException(status_code=400, detail="Failed to add holding")
    return result


@app.delete("/holdings/{holding_id}")
def remove_holding(holding_id: int, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    if not delete_holding(holding_id, user_id=user["id"]):
        raise HTTPException(status_code=404, detail="Holding not found")
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

    # ── LAZY IMPORT: only load heavy ML libs when this endpoint is hit ──
    from src.data.stock_fetcher import fetch_stock_data
    from src.models.sentiment import aggregate_sentiment
    from src.optimization.portfolio import PortfolioOptimizer
    from src.optimization.risk import RiskAnalyzer
    from src.optimization.combined_signal import CombinedSignal
    from src.optimization.health_score import HealthScoreEngine
    from src.optimization.adaptive_optimizer import AdaptiveHealthOptimizer
    from src.models.rag_pipeline import RAGPipeline

    require_portfolio(req.portfolio_id, user["id"])
    holdings = get_portfolio_holdings(req.portfolio_id, user_id=user["id"])
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
        returns = prices.pct_change(fill_method=None).dropna()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price fetch failed: {str(e)}")

    # Prepare optimizer / baseline / frontier
    try:
        optimizer = PortfolioOptimizer(prices)
        baseline = optimizer.equal_weight_baseline()
        frontier_df = optimizer.efficient_frontier(n_points=200)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Optimization setup failed: {str(e)}"
        )

    # Sentiment
    sentiment_scores = {}
    all_news = {}
    for ticker in available:
        try:
            from src.data.news_fetcher import fetch_news

            news = fetch_news(ticker)
            all_news[ticker] = news
            headlines = [a.get("title", "") for a in news if a.get("title")]
            sentiment_scores[ticker] = (
                aggregate_sentiment(headlines) if headlines else 0.0
            )
        except Exception:
            sentiment_scores[ticker] = 0.0
            all_news[ticker] = []

    # Adaptive health-aware optimization (25-35% caps, feasibility-adjusted)
    try:
        risk_analyzer = RiskAnalyzer(prices)
        news_counts = {t: len(all_news.get(t, [])) for t in available}
        adaptive = AdaptiveHealthOptimizer(
            optimizer, risk_analyzer, sentiment_scores, news_counts
        )
        selected = adaptive.search(alpha=req.alpha, portfolio_value=req.portfolio_value)
        opt_result = selected["opt_result"]
        combined = selected["combined"]
        final_weights = selected["final_weights"]
        final_stats = selected["final_stats"]
        risk_report = selected["risk_report"]
        health_score = selected["health_score"]
        adaptive_candidates = selected["candidates"]
        selected_cap = selected["selected_cap"]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Adaptive optimization failed: {str(e)}"
        )

    # LLM
    recommendations = []
    if req.use_llm:
        try:
            rag = RAGPipeline()
            for ticker in available:
                articles_text = [
                    a.get("title", "")
                    for a in all_news.get(ticker, [])
                    if a.get("title")
                ]
                rec = rag.generate_recommendation(
                    ticker=ticker,
                    sentiment_score=sentiment_scores.get(ticker, 0.0),
                    portfolio_weight=final_weights.get(ticker, 0.0),
                    retrieved_articles=articles_text,
                )
                recommendations.append(rec)
        except Exception:
            pass

    # Save to history
    safe_opt = {
        k: (v.tolist() if isinstance(v, np.ndarray) else v)
        for k, v in opt_result.items()
    }
    safe_opt["baseline_sharpe"] = baseline["sharpe_ratio"]
    safe_opt["final_sharpe_ratio"] = final_stats["sharpe_ratio"]
    safe_opt["health_score"] = health_score["score"]
    save_optimization_run(
        portfolio_id=req.portfolio_id,
        alpha=req.alpha,
        opt_result=safe_opt,
        sentiment_scores=sentiment_scores,
        recommendations=recommendations,
        risk_report=risk_report,
    )

    return {
        "tickers": available,
        "display_names": display_names,
        "opt_result": {
            "sharpe_ratio": float(final_stats["sharpe_ratio"]),
            "expected_return": float(final_stats["expected_return"]),
            "volatility": float(final_stats["volatility"]),
            "weights": {k: float(v) for k, v in opt_result["weights"].items()},
        },
        "baseline": {
            "sharpe_ratio": float(baseline["sharpe_ratio"]),
            "expected_return": float(baseline["expected_return"]),
            "volatility": float(baseline["volatility"]),
        },
        "final_weights": {k: float(v) for k, v in final_weights.items()},
        "weight_changes": {
            k: {"change": float(v["change"])}
            for k, v in combined["weight_changes"].items()
        },
        "sentiment_scores": sentiment_scores,
        "risk_report": risk_report,
        "health_score": health_score,
        "selected_cap": float(selected_cap),
        "adaptive_candidates": adaptive_candidates,
        "recommendations": recommendations,
        "frontier": {
            "volatility": frontier_df["volatility"].tolist(),
            "return": frontier_df["return"].tolist(),
            "sharpe": frontier_df["sharpe"].tolist(),
        },
    }


@app.get("/portfolios/{portfolio_id}/history")
def get_history(
    portfolio_id: int,
    limit: int = Query(30, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    require_portfolio(portfolio_id, user["id"])
    return get_portfolio_history(portfolio_id, limit, user_id=user["id"])


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
    require_portfolio(portfolio_id, user["id"])
    holdings = get_portfolio_holdings(portfolio_id, user_id=user["id"])
    tickers = [h["ticker"] for h in holdings]

    try:
        prices = fetch_stock_data(tickers + ["SPY"], period="1y")
        if isinstance(prices.columns, pd.MultiIndex):
            prices = prices["Close"]

        returns = prices.pct_change(fill_method=None).dropna()
        if isinstance(returns, pd.Series):
            returns = returns.to_frame(
                name=prices.columns[0] if hasattr(prices, "columns") else "price"
            )

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
    return {
        "message": "AI Portfolio Optimizer API",
        "docs": "/docs",
        "health": "/health",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════════


@app.get("/health")
def health():
    return {"status": "ok", "version": settings.VERSION, "src_available": SRC_AVAILABLE}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
