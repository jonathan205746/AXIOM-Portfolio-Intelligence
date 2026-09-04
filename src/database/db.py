import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import bcrypt

# ── Docker-safe database path ───────────────────────────────────
# Railway/Render: use /tmp/data (always writable)
# Local dev: use ../../data (repo root)
DB_DIR = os.environ.get(
    "DB_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data")),
)
DB_PATH = os.path.join(DB_DIR, "portfolio_optimizer.db")
os.makedirs(DB_DIR, exist_ok=True)


def _connect() -> sqlite3.Connection:
    """Create a SQLite connection with row factory enabled."""
    os.makedirs(DB_DIR, exist_ok=True)  # ensure dir exists before connecting
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _hash_password(password: str) -> str:
    """Return an adaptive bcrypt hash for newly stored passwords."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _legacy_hash_password(password: str) -> str:
    """Hash used by older installations; retained only for login migration."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify bcrypt hashes and legacy SHA-256 hashes safely."""
    if not plain_password or not hashed_password:
        return False
    if hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except ValueError:
            return False
    return hmac.compare_digest(_legacy_hash_password(plain_password), hashed_password)


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

            CREATE TABLE IF NOT EXISTS password_reset_codes (
                user_id INTEGER PRIMARY KEY,
                code_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                used_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        conn.commit()
    return True


def create_user(
    username: str, email: str = "", password: str = ""
) -> Optional[Dict[str, Any]]:
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
    return authenticate_user(username, password)


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a user and transparently upgrade legacy password hashes."""
    username = (username or "").strip()
    if not username or not password:
        return None

    with _connect() as conn:
        row = conn.execute(
            "SELECT id, username, email, password_hash, created_at FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if row is None or not verify_password(password, row["password_hash"]):
            return None
        if not row["password_hash"].startswith(("$2a$", "$2b$", "$2y$")):
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (_hash_password(password), row["id"]),
            )
            conn.commit()
        return {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "created_at": row["created_at"],
        }


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


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, username, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return _row_to_dict(row)


def _reset_code_payload(user_id: int, code: str) -> bytes:
    return f"{user_id}:{code}".encode("utf-8")


def _hash_reset_code(user_id: int, code: str) -> str:
    return bcrypt.hashpw(
        _reset_code_payload(user_id, code),
        bcrypt.gensalt(),
    ).decode("utf-8")


def _verify_reset_code(user_id: int, code: str, stored_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            _reset_code_payload(user_id, code),
            stored_hash.encode("utf-8"),
        )
    except (TypeError, ValueError):
        return False


def create_password_reset_code(
    username: str,
    email: str,
    code: str,
    ttl_minutes: int = 15,
    cooldown_seconds: int = 60,
) -> bool:
    """Store an expiring reset-code hash; never store the plaintext code."""
    username = (username or "").strip()
    email = (email or "").strip().lower()
    if not username or not email or not code or ttl_minutes < 1:
        return False

    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ? AND lower(email) = ?",
            (username, email),
        ).fetchone()
        if row is None:
            return False

        previous = conn.execute(
            "SELECT created_at FROM password_reset_codes WHERE user_id = ?",
            (row["id"],),
        ).fetchone()
        now = datetime.now(timezone.utc)
        if previous is not None:
            created_at = datetime.fromisoformat(previous["created_at"])
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            if (now - created_at).total_seconds() < cooldown_seconds:
                return False

        expires_at = now + timedelta(minutes=ttl_minutes)
        conn.execute(
            """
            INSERT INTO password_reset_codes
                (user_id, code_hash, expires_at, attempts, created_at, used_at)
            VALUES (?, ?, ?, 0, ?, NULL)
            ON CONFLICT(user_id) DO UPDATE SET
                code_hash = excluded.code_hash,
                expires_at = excluded.expires_at,
                attempts = 0,
                created_at = excluded.created_at,
                used_at = NULL
            """,
            (
                row["id"],
                _hash_reset_code(row["id"], code),
                expires_at.isoformat(),
                now.isoformat(),
            ),
        )
        conn.commit()
        return True


def reset_password_with_code(
    username: str,
    email: str,
    code: str,
    new_password: str,
    max_attempts: int = 5,
) -> bool:
    """Consume a valid single-use reset code and replace the password."""
    username = (username or "").strip()
    email = (email or "").strip().lower()
    if not username or not email or not code or len(new_password or "") < 12:
        return False

    with _connect() as conn:
        row = conn.execute(
            """
            SELECT u.id, r.code_hash, r.expires_at, r.attempts, r.used_at
            FROM users AS u
            JOIN password_reset_codes AS r ON r.user_id = u.id
            WHERE u.username = ? AND lower(u.email) = ?
            """,
            (username, email),
        ).fetchone()
        if row is None or row["used_at"] is not None or row["attempts"] >= max_attempts:
            return False

        now = datetime.now(timezone.utc)
        expires_at = datetime.fromisoformat(row["expires_at"])
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if now >= expires_at:
            return False

        valid = _verify_reset_code(
            row["id"],
            code,
            row["code_hash"],
        )
        if not valid:
            conn.execute(
                """
                UPDATE password_reset_codes
                SET attempts = attempts + 1
                WHERE user_id = ?
                """,
                (row["id"],),
            )
            conn.commit()
            return False

        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (_hash_password(new_password), row["id"]),
        )
        conn.execute(
            "UPDATE password_reset_codes SET used_at = ? WHERE user_id = ?",
            (now.isoformat(), row["id"]),
        )
        conn.commit()
        return True


def generate_password_reset_code() -> str:
    """Generate a cryptographically secure six-digit code."""
    return f"{secrets.randbelow(1_000_000):06d}"


def create_portfolio(
    user_id: int, name: str, description: str = "", currency: str = "USD"
) -> Optional[Dict[str, Any]]:
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


def get_portfolio_for_user(portfolio_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT id, user_id, name, description, currency, created_at
            FROM portfolios WHERE id = ? AND user_id = ?
            """,
            (portfolio_id, user_id),
        ).fetchone()
        return _row_to_dict(row)


def delete_portfolio(portfolio_id: int, user_id: Optional[int] = None) -> bool:
    with _connect() as conn:
        if user_id is None:
            cursor = conn.execute(
                "DELETE FROM portfolios WHERE id = ?", (portfolio_id,)
            )
        else:
            cursor = conn.execute(
                "DELETE FROM portfolios WHERE id = ? AND user_id = ?",
                (portfolio_id, user_id),
            )
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
            avg_price = (old_qty * old_price + quantity * buy_price) / new_qty

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


def get_portfolio_holdings(
    portfolio_id: int, user_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    with _connect() as conn:
        if user_id is None:
            rows = conn.execute(
                "SELECT id, portfolio_id, ticker, display_name, exchange, quantity, buy_price, buy_currency, buy_date, created_at FROM holdings WHERE portfolio_id = ? ORDER BY created_at DESC",
                (portfolio_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT h.id, h.portfolio_id, h.ticker, h.display_name,
                       h.exchange, h.quantity, h.buy_price, h.buy_currency,
                       h.buy_date, h.created_at
                FROM holdings h
                JOIN portfolios p ON p.id = h.portfolio_id
                WHERE h.portfolio_id = ? AND p.user_id = ?
                ORDER BY h.created_at DESC
                """,
                (portfolio_id, user_id),
            ).fetchall()
        result: List[Dict[str, Any]] = []
        for row in rows:
            row_dict = _row_to_dict(row)
            if row_dict is not None:
                result.append(row_dict)
        return result


def delete_holding(holding_id: int, user_id: Optional[int] = None) -> bool:
    with _connect() as conn:
        if user_id is None:
            cursor = conn.execute("DELETE FROM holdings WHERE id = ?", (holding_id,))
        else:
            cursor = conn.execute(
                """
                DELETE FROM holdings
                WHERE id = ? AND portfolio_id IN (
                    SELECT id FROM portfolios WHERE user_id = ?
                )
                """,
                (holding_id, user_id),
            )
        conn.commit()
        return cursor.rowcount > 0


def update_holding(holding_id: int, **kwargs: Any) -> Optional[Dict[str, Any]]:
    if not holding_id:
        return None

    allowed_fields = {
        "ticker",
        "display_name",
        "exchange",
        "quantity",
        "buy_price",
        "buy_currency",
        "buy_date",
    }
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
        cursor = conn.execute(
            "DELETE FROM holdings WHERE portfolio_id = ?", (portfolio_id,)
        )
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


def get_portfolio_history(
    portfolio_id: int, limit: int = 30, user_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    with _connect() as conn:
        ownership_clause = ""
        parameters: List[Any] = [portfolio_id]
        if user_id is not None:
            ownership_clause = (
                "AND portfolio_id IN (SELECT id FROM portfolios WHERE user_id = ?)"
            )
            parameters.append(user_id)
        parameters.append(max(1, min(int(limit), 100)))
        rows = conn.execute(
            f"""
            SELECT id, portfolio_id, run_date, alpha_used, sharpe_ratio, expected_return, volatility,
                   tickers_json, opt_result_json, sentiment_scores_json, recommendations_json, risk_report_json
            FROM optimization_runs
            WHERE portfolio_id = ?
              {ownership_clause}
            ORDER BY run_date DESC, id DESC
            LIMIT ?
            """,
            parameters,
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
