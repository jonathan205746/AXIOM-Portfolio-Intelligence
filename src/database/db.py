import hashlib
import json
import os
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

# Use env var (set by Render) or fallback to local path
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./data/portfolio_optimizer.db")
# Strip sqlite:/// prefix if present
DB_FILE = DB_PATH.replace("sqlite:///", "")

# Ensure directory exists (critical for Render /tmp paths)
Path(DB_FILE).parent.mkdir(parents=True, exist_ok=True)


def _connect() -> sqlite3.Connection:
    """Create a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _normalize_date(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, str):
        return value[:10]
    return date.today().strftime("%Y-%m-%d")


def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    return dict(row)


def _json_safe(value: Any) -> Any:
    """Convert values that are not JSON-native into JSON-safe Python types."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return [_json_safe(v) for v in value.tolist()]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, pd.Series):
        return [_json_safe(v) for v in value.tolist()]
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    if hasattr(value, "tolist"):
        try:
            return _json_safe(value.tolist())
        except Exception:
            pass
    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except Exception:
            pass
    if hasattr(value, "to_dict") and callable(value.to_dict):
        try:
            return _json_safe(value.to_dict())
        except Exception:
            pass
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return str(value)


def init_db() -> bool:
    """Initialize the SQLite schema used by the app."""
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                currency TEXT NOT NULL DEFAULT 'USD',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                display_name TEXT,
                exchange TEXT NOT NULL DEFAULT 'US',
                quantity REAL NOT NULL,
                buy_price REAL NOT NULL,
                buy_currency TEXT NOT NULL DEFAULT 'USD',
                buy_date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS optimization_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                run_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                alpha_used REAL,
                sharpe_ratio REAL,
                expected_return REAL,
                volatility REAL,
                tickers_json TEXT,
                opt_result_json TEXT,
                sentiment_scores_json TEXT,
                recommendations_json TEXT,
                risk_report_json TEXT,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
            );
            """
        )
        conn.commit()
    return True


def create_user(username: str, email: str = "", password: str = "") -> Optional[Dict[str, Any]]:
    username = (username or "").strip()
    email = (email or "").strip()
    if not username or not password:
        return None

    try:
        with _connect() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, _hash_password(password)),
            )
            conn.commit()
            user_id = cursor.lastrowid
            row = conn.execute(
                "SELECT id, username, email, created_at FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            return _row_to_dict(row)
    except sqlite3.IntegrityError:
        return None


def get_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    username = (username or "").strip()
    if not username or not password:
        return None

    with _connect() as conn:
        row = conn.execute(
            "SELECT id, username, email, created_at FROM users WHERE username = ? AND password_hash = ?",
            (username, _hash_password(password)),
        ).fetchone()
        return _row_to_dict(row)

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Fetch a user by username only (no password check). Used for auth flows."""
    username = (username or "").strip()
    if not username:
        return None

    with _connect() as conn:
        row = conn.execute(
            "SELECT id, username, email, created_at FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return _row_to_dict(row)

def verify_identity(username: str, email: str) -> bool:
    """
    Check whether a username + email pair matches an existing account.
    Used as the identity check for the forgot-password flow, since there
    is no email/SMTP service in this stack to send a reset link through.
    Deliberately does not reveal *which* field was wrong — returning a
    single bool avoids leaking whether a username exists at all.
    """
    username = (username or "").strip()
    email = (email or "").strip()
    if not username or not email:
        return False

    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ? AND email = ?",
            (username, email),
        ).fetchone()
        return row is not None


def reset_password(username: str, email: str, new_password: str) -> bool:
    """
    Reset a user's password after verify_identity() confirms the
    username + email pair. Returns False if the identity check fails
    or the new password is empty.
    """
    if not verify_identity(username, email):
        return False
    if not new_password:
        return False

    username = (username or "").strip()
    with _connect() as conn:
        cursor = conn.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (_hash_password(new_password), username),
        )
        conn.commit()
        return cursor.rowcount > 0


def create_portfolio(user_id: int, name: str, description: str = "", currency: str = "USD") -> Optional[Dict[str, Any]]:
    name = (name or "").strip()
    if not user_id or not name:
        return None

    with _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO portfolios (user_id, name, description, currency) VALUES (?, ?, ?, ?)",
            (user_id, name, description or "", (currency or "USD").upper()),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, user_id, name, description, currency, created_at FROM portfolios WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return _row_to_dict(row)

def update_portfolio_currency(portfolio_id: int, currency: str) -> bool:
    with _connect() as conn:
        cursor = conn.execute(
            "UPDATE portfolios SET currency = ? WHERE id = ?",
            ((currency or "USD").upper(), portfolio_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_portfolio(portfolio_id: int) -> bool:
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM portfolios WHERE id = ?", (portfolio_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_user_portfolios(user_id: int) -> List[Dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, user_id, name, description, currency, created_at FROM portfolios WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        result: List[Dict[str, Any]] = []
        for row in rows:
            row_dict = _row_to_dict(row)
            if row_dict is not None:
                result.append(row_dict)
        return result


def add_holding(
    portfolio_id: int,
    ticker: str,
    display_name: Optional[str] = None,
    exchange: str = "US",
    quantity: float = 1.0,
    buy_price: float = 0.0,
    buy_currency: str = "USD",
    buy_date: Any = None,
) -> Optional[Dict[str, Any]]:

    ticker = (ticker or "").strip().upper()
    if not portfolio_id or not ticker:
        return None

    quantity = float(quantity)
    buy_price = float(buy_price)

    with _connect() as conn:

        # Check if the holding already exists
        existing = conn.execute(
            """
            SELECT *
            FROM holdings
            WHERE portfolio_id = ? AND ticker = ?
            """,
            (portfolio_id, ticker),
        ).fetchone()

        if existing:
            old_qty = float(existing["quantity"])
            old_price = float(existing["buy_price"])

            new_qty = old_qty + quantity

            # Weighted average buy price
            avg_price = (
                old_qty * old_price +
                quantity * buy_price
            ) / new_qty

            conn.execute(
                """
                UPDATE holdings
                SET quantity = ?,
                    buy_price = ?,
                    buy_currency = ?,
                    buy_date = ?
                WHERE id = ?
                """,
                (
                    new_qty,
                    avg_price,
                    (buy_currency or "USD").upper(),
                    _normalize_date(buy_date),
                    existing["id"],
                ),
            )

            conn.commit()

            row = conn.execute(
                """
                SELECT id, portfolio_id, ticker, display_name,
                       exchange, quantity, buy_price,
                       buy_currency, buy_date, created_at
                FROM holdings
                WHERE id = ?
                """,
                (existing["id"],),
            ).fetchone()

            return _row_to_dict(row)

        # Insert new holding
        cursor = conn.execute(
            """
            INSERT INTO holdings (
                portfolio_id,
                ticker,
                display_name,
                exchange,
                quantity,
                buy_price,
                buy_currency,
                buy_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                portfolio_id,
                ticker,
                display_name or ticker,
                (exchange or "US").upper(),
                quantity,
                buy_price,
                (buy_currency or "USD").upper(),
                _normalize_date(buy_date),
            ),
        )

        conn.commit()

        row = conn.execute(
            """
            SELECT id, portfolio_id, ticker, display_name,
                   exchange, quantity, buy_price,
                   buy_currency, buy_date, created_at
            FROM holdings
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

        return _row_to_dict(row)


def get_portfolio_holdings(portfolio_id: int) -> List[Dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, portfolio_id, ticker, display_name, exchange, quantity, buy_price, buy_currency, buy_date, created_at FROM holdings WHERE portfolio_id = ? ORDER BY created_at DESC",
            (portfolio_id,),
        ).fetchall()
        result: List[Dict[str, Any]] = []
        for row in rows:
            row_dict = _row_to_dict(row)
            if row_dict is not None:
                result.append(row_dict)
        return result


def delete_holding(holding_id: int) -> bool:
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM holdings WHERE id = ?", (holding_id,))
        conn.commit()
        return cursor.rowcount > 0


def update_holding(holding_id: int, **kwargs: Any) -> Optional[Dict[str, Any]]:
    if not holding_id:
        return None

    allowed_fields = {"ticker", "display_name", "exchange", "quantity", "buy_price", "buy_currency", "buy_date"}
    updates = []
    values: List[Any] = []
    for key, value in kwargs.items():
        if key not in allowed_fields:
            continue
        if key == "buy_date":
            value = _normalize_date(value)
        updates.append(f"{key} = ?")
        values.append(value)

    if not updates:
        return None

    values.append(holding_id)
    with _connect() as conn:
        conn.execute(f"UPDATE holdings SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()
        row = conn.execute(
            "SELECT id, portfolio_id, ticker, display_name, exchange, quantity, buy_price, buy_currency, buy_date, created_at FROM holdings WHERE id = ?",
            (holding_id,),
        ).fetchone()
        return _row_to_dict(row)


def clear_portfolio_holdings(portfolio_id: int) -> bool:
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM holdings WHERE portfolio_id = ?", (portfolio_id,))
        conn.commit()
        return cursor.rowcount >= 0


def save_optimization_run(
    portfolio_id: int,
    alpha: float,
    opt_result: Optional[Dict[str, Any]] = None,
    sentiment_scores: Optional[Dict[str, Any]] = None,
    recommendations: Optional[List[Dict[str, Any]]] = None,
    risk_report: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    if not portfolio_id:
        return None

    opt_result = opt_result or {}
    sentiment_scores = sentiment_scores or {}
    recommendations = recommendations or []
    risk_report = risk_report or {}

    weights = opt_result.get("weights") or {}
    tickers = list(weights.keys()) or list(sentiment_scores.keys()) or []

    sharpe_ratio = opt_result.get("sharpe_ratio")
    expected_return = opt_result.get("expected_return")
    volatility = opt_result.get("volatility")

    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO optimization_runs (
                portfolio_id, alpha_used, sharpe_ratio, expected_return, volatility,
                tickers_json, opt_result_json, sentiment_scores_json, recommendations_json, risk_report_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                portfolio_id,
                float(alpha),
                sharpe_ratio,
                expected_return,
                volatility,
                json.dumps(_json_safe(tickers), default=str),
                json.dumps(_json_safe(opt_result), default=str),
                json.dumps(_json_safe(sentiment_scores), default=str),
                json.dumps(_json_safe(recommendations), default=str),
                json.dumps(_json_safe(risk_report), default=str),
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, portfolio_id, run_date, alpha_used, sharpe_ratio, expected_return, volatility, tickers_json, opt_result_json, sentiment_scores_json, recommendations_json, risk_report_json FROM optimization_runs WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return _row_to_dict(row)


def get_portfolio_history(portfolio_id: int, limit: int = 30) -> List[Dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, portfolio_id, run_date, alpha_used, sharpe_ratio, expected_return, volatility,
                   tickers_json, opt_result_json, sentiment_scores_json, recommendations_json, risk_report_json
            FROM optimization_runs
            WHERE portfolio_id = ?
            ORDER BY run_date DESC, id DESC
            LIMIT ?
            """,
            (portfolio_id, limit),
        ).fetchall()

    history: List[Dict[str, Any]] = []
    for row in rows:
        history.append(
            {
                "id": row["id"],
                "portfolio_id": row["portfolio_id"],
                "run_date": row["run_date"],
                "alpha_used": row["alpha_used"],
                "sharpe_ratio": row["sharpe_ratio"],
                "expected_return": row["expected_return"],
                "volatility": row["volatility"],
                "tickers": json.loads(row["tickers_json"] or "[]"),
                "opt_result": json.loads(row["opt_result_json"] or "{}"),
                "sentiment_scores": json.loads(row["sentiment_scores_json"] or "{}"),
                "recommendations": json.loads(row["recommendations_json"] or "[]"),
                "risk_report": json.loads(row["risk_report_json"] or "{}"),
            }
        )
    return history


def get_sharpe_trend(portfolio_id: int) -> List[Dict[str, Any]]:
    history = get_portfolio_history(portfolio_id, limit=30)
    trend = []
    for item in history:
        trend.append(
            {
                "date": item.get("run_date"),
                "sharpe_ratio": item.get("sharpe_ratio"),
                "expected_return": item.get("expected_return"),
                "volatility": item.get("volatility"),
            }
        )
    return list(reversed(trend))


