"""
src/database/models.py
------------------------------------------------------------------
Typed dataclasses mirroring the exact schema created by db.py's
init_db(). These are NOT an ORM layer — db.py uses raw sqlite3 with
a Row factory, not SQLAlchemy, and this file does not change that.
Their job is narrower: give the rest of the app (Streamlit pages,
tests, future FastAPI endpoints) a typed shape to reference instead
of passing raw dicts around and hoping the keys are spelled right.

Every field name below matches a real column in db.py, checked
against init_db() directly:
    users              -> id, username, email, password_hash, created_at
    portfolios         -> id, user_id, name, description, currency, created_at
    holdings           -> id, portfolio_id, ticker, display_name, exchange,
                           quantity, buy_price, buy_currency, buy_date, created_at
    optimization_runs  -> id, portfolio_id, run_date, alpha_used, sharpe_ratio,
                           expected_return, volatility, tickers_json,
                           opt_result_json, sentiment_scores_json,
                           recommendations_json, risk_report_json

Note on optimization_runs: db.py stores four JSON blobs as TEXT
columns and get_portfolio_history() already deserializes them before
returning. OptimizationRun.from_dict() below expects that DESERIALIZED
form (what get_portfolio_history() actually returns), not the raw TEXT
column. If you build one from a raw DB row instead, json.loads() the
*_json fields first.

There is no "final_weights" column — it isn't persisted. 3_Analysis.py
computes it at runtime as CombinedSignal.combine() output, and only
sharpe_ratio / expected_return / volatility / opt_result /
sentiment_scores / recommendations / risk_report survive into the
database. Wanting final_weights in History later means changing
db.py + init_db(), not something this file can paper over.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────────────────────────
# User
# ─────────────────────────────────────────────────────────────────
@dataclass
class User:
    id: int
    username: str
    email: str
    created_at: str
    # password_hash intentionally excluded — db.py's own SELECTs for
    # get_user()/create_user() never return it either. Keep it that way;
    # there's no reason a hash needs to travel further than db.py.

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> Optional["User"]:
        if d is None:
            return None
        return cls(
            id=d["id"],
            username=d["username"],
            email=d.get("email") or "",
            created_at=d.get("created_at", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────
# Portfolio
# ─────────────────────────────────────────────────────────────────
@dataclass
class Portfolio:
    id: int
    user_id: int
    name: str
    description: str
    currency: str  # "USD" | "INR"
    created_at: str

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> Optional["Portfolio"]:
        if d is None:
            return None
        return cls(
            id=d["id"],
            user_id=d["user_id"],
            name=d["name"],
            description=d.get("description") or "",
            currency=d.get("currency", "USD"),
            created_at=d.get("created_at", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────
# Holding
# ─────────────────────────────────────────────────────────────────
@dataclass
class Holding:
    id: int
    portfolio_id: int
    ticker: str          # yfinance ticker, e.g. "TCS.NS"
    display_name: str    # e.g. "TCS"
    exchange: str          # "US" | "IN"
    quantity: float
    buy_price: float
    buy_currency: str    # "USD" | "INR"
    buy_date: str          # "YYYY-MM-DD"
    created_at: str

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> Optional["Holding"]:
        if d is None:
            return None
        return cls(
            id=d["id"],
            portfolio_id=d["portfolio_id"],
            ticker=d["ticker"],
            display_name=d.get("display_name") or d["ticker"],
            exchange=d.get("exchange", "US"),
            quantity=float(d["quantity"]),
            buy_price=float(d["buy_price"]),
            buy_currency=d.get("buy_currency", "USD"),
            buy_date=d.get("buy_date", ""),
            created_at=d.get("created_at", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def invested_value(self) -> float:
        return self.quantity * self.buy_price


# ─────────────────────────────────────────────────────────────────
# OptimizationRun
# ─────────────────────────────────────────────────────────────────
@dataclass
class OptimizationRun:
    id: int
    portfolio_id: int
    run_date: str
    alpha_used: Optional[float]
    sharpe_ratio: Optional[float]
    expected_return: Optional[float]
    volatility: Optional[float]
    tickers: List[str] = field(default_factory=list)
    opt_result: Dict[str, Any] = field(default_factory=dict)
    sentiment_scores: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    risk_report: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> Optional["OptimizationRun"]:
        """
        Expects the ALREADY-DESERIALIZED shape returned by
        db.get_portfolio_history() — tickers/opt_result/sentiment_scores/
        recommendations/risk_report as Python objects, not JSON strings.
        """
        if d is None:
            return None
        return cls(
            id=d["id"],
            portfolio_id=d["portfolio_id"],
            run_date=d.get("run_date", ""),
            alpha_used=d.get("alpha_used"),
            sharpe_ratio=d.get("sharpe_ratio"),
            expected_return=d.get("expected_return"),
            volatility=d.get("volatility"),
            tickers=d.get("tickers") or [],
            opt_result=d.get("opt_result") or {},
            sentiment_scores=d.get("sentiment_scores") or {},
            recommendations=d.get("recommendations") or [],
            risk_report=d.get("risk_report") or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def run_datetime(self) -> Optional[datetime]:
        """Parsed run_date, or None if it can't be parsed. Use this
        instead of slicing strings when you need to sort/compare dates."""
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(self.run_date[:19], fmt)
            except (ValueError, TypeError):
                continue
        return None
