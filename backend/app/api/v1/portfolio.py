"""Portfolio router for /api/v1/portfolios."""

import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.schemas.portfolio import (
    AnalysisRequest,
    AnalysisResponse,
    BenchmarkResponse,
    HistoryResponse,
    HoldingCreate,
    HoldingResponse,
    HoldingUpdate,
    PortfolioCreate,
    PortfolioResponse,
    PortfolioUpdate,
    SharpeTrendResponse,
)
from backend.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/portfolios", tags=["portfolios"])
security = HTTPBearer(auto_error=False)

try:
    from src.data.stock_fetcher import fetch_stock_data
    from src.database.db import (
        add_holding,
        create_portfolio,
        delete_holding,
        delete_portfolio,
        get_portfolio_for_user,
        get_portfolio_history,
        get_portfolio_holdings,
        get_sharpe_trend,
        get_user_portfolios,
        update_holding,
        update_portfolio_currency,
    )
    from src.models.rag_pipeline import RAGPipeline
    from src.models.sentiment import aggregate_sentiment
    from src.optimization.adaptive_optimizer import AdaptiveHealthOptimizer
    from src.optimization.portfolio import PortfolioOptimizer
    from src.optimization.risk import RiskAnalyzer

    SRC_AVAILABLE = True
except Exception as e:
    print(f"Warning: src modules not available: {e}")
    SRC_AVAILABLE = False

settings = get_settings()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        from jose import JWTError, jwt
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        if not SRC_AVAILABLE:
            raise HTTPException(status_code=503, detail="Backend modules not loaded")
        from src.database.db import get_user_by_id
        user = get_user_by_id(int(user_id))
        if not user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_portfolio(portfolio_id: int, user_id: int) -> dict:
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    portfolio = get_portfolio_for_user(portfolio_id, user_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


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


@router.get("", response_model=List[PortfolioResponse])
def list_portfolios(user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    return get_user_portfolios(user["id"])


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio_endpoint(req: PortfolioCreate, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    p = create_portfolio(user["id"], req.name, req.description, req.currency)
    if not p:
        raise HTTPException(status_code=400, detail="Failed to create portfolio")
    return p


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(portfolio_id: int, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    portfolio = get_portfolio_for_user(portfolio_id, user["id"])
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.patch("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(portfolio_id: int, req: PortfolioUpdate, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    require_portfolio(portfolio_id, user["id"])
    updates = []
    values: list = []
    if req.name is not None:
        updates.append("name = ?")
        values.append(req.name)
    if req.description is not None:
        updates.append("description = ?")
        values.append(req.description)
    if updates:
        values.append(portfolio_id)
        values.append(user["id"])
        from src.database.db import _connect
        with _connect() as conn:
            conn.execute(f"UPDATE portfolios SET {', '.join(updates)} WHERE id = ? AND user_id = ?", values)
            conn.commit()
    if req.currency is not None:
        update_portfolio_currency(portfolio_id, req.currency)
    portfolio = get_portfolio_for_user(portfolio_id, user["id"])
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_endpoint(portfolio_id: int, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    if not delete_portfolio(portfolio_id, user_id=user["id"]):
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return None


@router.get("/{portfolio_id}/holdings", response_model=List[HoldingResponse])
def list_holdings(portfolio_id: int, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    require_portfolio(portfolio_id, user["id"])
    return get_portfolio_holdings(portfolio_id, user_id=user["id"])


@router.post("/{portfolio_id}/holdings", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
def add_holding_endpoint(portfolio_id: int, req: HoldingCreate, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    require_portfolio(portfolio_id, user["id"])
    yf_ticker, display, exchange = normalize_ticker(req.ticker)
    buy_date = datetime.fromisoformat(req.buy_date) if req.buy_date else datetime.now()
    result = add_holding(
        portfolio_id=portfolio_id,
        ticker=yf_ticker,
        display_name=display,
        exchange=exchange,
        quantity=req.quantity,
        buy_price=req.buy_price,
        buy_currency=req.buy_currency,
        buy_date=buy_date,
    )
    if not result:
        raise HTTPException(status_code=400, detail="Failed to add holding")
    return result


@router.patch("/holdings/{holding_id}", response_model=HoldingResponse)
def update_holding_endpoint(holding_id: int, req: HoldingUpdate, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    updates: dict[str, float | str] = {}
    if req.quantity is not None:
        updates["quantity"] = req.quantity
    if req.buy_price is not None:
        updates["buy_price"] = req.buy_price
    if req.buy_currency is not None:
        updates["buy_currency"] = str(req.buy_currency)
    if req.buy_date is not None:
        updates["buy_date"] = str(req.buy_date)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = update_holding(holding_id, **updates)
    if not result:
        raise HTTPException(status_code=404, detail="Holding not found or not owned by user")
    return result


@router.delete("/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_holding(holding_id: int, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    if not delete_holding(holding_id, user_id=user["id"]):
        raise HTTPException(status_code=404, detail="Holding not found")
    return None


@router.post("/{portfolio_id}/analysis", response_model=AnalysisResponse)
def run_analysis(portfolio_id: int, req: AnalysisRequest, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")

    import numpy as np
    import pandas as pd

    require_portfolio(portfolio_id, user["id"])
    holdings = get_portfolio_holdings(portfolio_id, user_id=user["id"])
    if len(holdings) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 holdings")

    tickers = [h["ticker"] for h in holdings]
    display_names = {h["ticker"]: h["display_name"] for h in holdings}

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price fetch failed: {str(e)}")

    try:
        optimizer = PortfolioOptimizer(prices)
        baseline = optimizer.equal_weight_baseline()
        frontier_df = optimizer.efficient_frontier(n_points=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization setup failed: {str(e)}")

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

    try:
        risk_analyzer = RiskAnalyzer(prices)
        news_counts = {t: len(all_news.get(t, [])) for t in available}
        adaptive = AdaptiveHealthOptimizer(optimizer, risk_analyzer, sentiment_scores, news_counts)
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
        raise HTTPException(status_code=500, detail=f"Adaptive optimization failed: {str(e)}")

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

    from src.database.db import save_optimization_run
    safe_opt = {
        k: (v.tolist() if isinstance(v, np.ndarray) else v)
        for k, v in opt_result.items()
    }
    safe_opt["baseline_sharpe"] = baseline["sharpe_ratio"]
    safe_opt["final_sharpe_ratio"] = final_stats["sharpe_ratio"]
    safe_opt["health_score"] = health_score["score"]
    save_optimization_run(
        portfolio_id=portfolio_id,
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


@router.get("/{portfolio_id}/history", response_model=List[HistoryResponse])
def get_history(
    portfolio_id: int,
    limit: int = Query(30, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    require_portfolio(portfolio_id, user["id"])
    return get_portfolio_history(portfolio_id, limit, user_id=user["id"])


@router.get("/{portfolio_id}/sharpe-trend", response_model=List[SharpeTrendResponse])
def get_sharpe_trend_endpoint(portfolio_id: int, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")
    require_portfolio(portfolio_id, user["id"])
    return get_sharpe_trend(portfolio_id)


@router.get("/{portfolio_id}/benchmark", response_model=BenchmarkResponse)
def benchmark_spy(portfolio_id: int, user: dict = Depends(get_current_user)):
    if not SRC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Backend modules not loaded")

    import numpy as np
    import pandas as pd

    require_portfolio(portfolio_id, user["id"])
    holdings = get_portfolio_holdings(portfolio_id, user_id=user["id"])
    tickers = [h["ticker"] for h in holdings]

    try:
        prices = fetch_stock_data(tickers + ["SPY"], period="1y")
        if isinstance(prices.columns, pd.MultiIndex):
            prices = prices["Close"]

        returns = prices.pct_change(fill_method=None).dropna()
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