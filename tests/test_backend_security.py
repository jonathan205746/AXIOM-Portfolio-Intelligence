import hashlib

import pytest

from src.database import db


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_DIR", str(tmp_path))
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "security.db"))
    db.init_db()
    return db


def test_new_passwords_use_bcrypt(isolated_db):
    user = isolated_db.create_user(
        "alice", "alice@example.com", "correct horse battery"
    )
    assert user is not None

    with isolated_db._connect() as conn:
        stored = conn.execute(
            "SELECT password_hash FROM users WHERE id = ?", (user["id"],)
        ).fetchone()["password_hash"]

    assert stored.startswith(("$2a$", "$2b$", "$2y$"))
    assert isolated_db.verify_password("correct horse battery", stored)
    assert not isolated_db.verify_password("wrong password", stored)


def test_legacy_sha256_hash_is_upgraded_after_login(isolated_db):
    legacy_hash = hashlib.sha256(b"legacy password").hexdigest()
    with isolated_db._connect() as conn:
        conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            ("legacy", "legacy@example.com", legacy_hash),
        )
        conn.commit()

    user = isolated_db.authenticate_user("legacy", "legacy password")
    assert user is not None
    assert "password_hash" not in user

    with isolated_db._connect() as conn:
        upgraded = conn.execute(
            "SELECT password_hash FROM users WHERE username = 'legacy'"
        ).fetchone()["password_hash"]
    assert upgraded.startswith(("$2a$", "$2b$", "$2y$"))


def test_portfolio_reads_are_scoped_to_owner(isolated_db):
    alice = isolated_db.create_user("alice", "a@example.com", "alice secure password")
    bob = isolated_db.create_user("bob", "b@example.com", "bob secure password!!")
    portfolio = isolated_db.create_portfolio(alice["id"], "Private")
    isolated_db.add_holding(portfolio["id"], "AAPL", quantity=1, buy_price=100)

    assert len(isolated_db.get_portfolio_holdings(portfolio["id"], alice["id"])) == 1
    assert isolated_db.get_portfolio_holdings(portfolio["id"], bob["id"]) == []
    assert isolated_db.get_portfolio_for_user(portfolio["id"], bob["id"]) is None


def test_non_owner_cannot_delete_portfolio_or_holding(isolated_db):
    alice = isolated_db.create_user("alice", "a@example.com", "alice secure password")
    bob = isolated_db.create_user("bob", "b@example.com", "bob secure password!!")
    portfolio = isolated_db.create_portfolio(alice["id"], "Private")
    holding = isolated_db.add_holding(
        portfolio["id"], "MSFT", quantity=2, buy_price=200
    )

    assert not isolated_db.delete_holding(holding["id"], user_id=bob["id"])
    assert not isolated_db.delete_portfolio(portfolio["id"], user_id=bob["id"])
    assert isolated_db.get_portfolio_for_user(portfolio["id"], alice["id"]) is not None
    assert isolated_db.delete_holding(holding["id"], user_id=alice["id"])
    assert isolated_db.delete_portfolio(portfolio["id"], user_id=alice["id"])
