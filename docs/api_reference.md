# AXIOM Portfolio Intelligence — API Reference

## Status

The public AWS deployment currently runs Streamlit on port `8501`. FastAPI is
an optional local or Docker-profile interface. Start it and inspect its schema:

```powershell
uvicorn backend.app.main:app --reload --port 8000
```

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

The running OpenAPI document is the authoritative contract.

## Configuration

FastAPI rejects an empty, short, or placeholder signing key.

```env
SECRET_KEY=replace_with_a_random_value_of_at_least_32_characters
CORS_ORIGINS=http://localhost:8501
```

`CORS_ORIGINS` accepts a comma-separated list. Never commit `.env` or expose
the signing key.

## Authentication

Except for `/`, `/health`, `/auth/register`, and `/auth/login`, routes require:

```http
Authorization: Bearer <access_token>
```

JWT subjects are checked against the current database user on each protected
request. A missing, invalid, expired, or deleted-user token returns `401`.

New passwords use bcrypt. Successful login transparently replaces a legacy
SHA-256 password hash with bcrypt. Password hashes never appear in responses.

### `POST /auth/register`

Creates a user and default portfolio.

```json
{
  "username": "parmod01",
  "email": "user@example.com",
  "password": "a-long-password"
}
```

- username: 3–50 characters; letters, numbers, `_`, `.`, and `-`
- email: syntactically valid
- password: 12–72 characters

Duplicate registration returns `400`; validation failures return `422`.

### `POST /auth/login`

```json
{
  "username": "parmod01",
  "password": "a-long-password"
}
```

Successful response:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "parmod01",
    "email": "user@example.com"
  }
}
```

Invalid credentials return a generic `401`. Password reset by username and
email alone is disabled. A future recovery flow must use signed, single-use,
expiring tokens delivered to a verified address.

### `GET /auth/me`

Returns the current safe user record.

## Portfolios

Portfolio access is restricted to the authenticated owner. An unknown or
inaccessible resource returns `404` to avoid disclosing its existence.

### `GET /portfolios`

Returns the current user's portfolios.

### `POST /portfolios`

```json
{
  "name": "Long Term",
  "description": "Core holdings",
  "currency": "USD"
}
```

- name: 1–100 characters
- description: maximum 500 characters
- currency: `USD` or `INR`

### `DELETE /portfolios/{portfolio_id}`

Deletes an owned portfolio. SQLite foreign keys cascade to its holdings and
saved runs. Returns `404` if absent or owned by another user.

## Holdings

### `GET /portfolios/{portfolio_id}/holdings`

Returns holdings only after verifying portfolio ownership.

### `POST /portfolios/{portfolio_id}/holdings`

```json
{
  "ticker": "AAPL",
  "quantity": 5,
  "buy_price": 195.5,
  "buy_currency": "USD"
}
```

- ticker: 1–20 safe symbol characters
- quantity and buy price: greater than zero
- buy currency: `USD` or `INR`

Known Indian symbols are normalized to Yahoo Finance `.NS` symbols. Adding an
existing ticker updates quantity and weighted-average purchase price.

### `DELETE /holdings/{holding_id}`

Deletes a holding only when its parent portfolio belongs to the caller.

## Analysis

### `POST /analysis/run`

Runs analysis for an owned portfolio with at least two usable holdings.

```json
{
  "portfolio_id": 1,
  "alpha": 0.6,
  "portfolio_value": 100000,
  "use_llm": true
}
```

- portfolio ID: positive integer
- alpha: `0.0`–`1.0`
- portfolio value: at least `1000`

The response contains tickers, optimized and final weights, baseline metrics,
risk output, sentiment, adaptive candidates, recommendations, and efficient-
frontier arrays. Successful runs are saved in `optimization_runs`.

Market data uses `pct_change(fill_method=None)` so missing prices are not
silently forward-filled.

## History

### `GET /portfolios/{portfolio_id}/history?limit=30`

Returns saved runs for an owned portfolio. `limit` must be 1–100.

## Benchmark

### `GET /benchmark/spy?portfolio_id={id}`

Returns aligned dates, equal-weight holding-universe growth, and SPY growth for
an owned portfolio. It does not reconstruct a saved final target. Use the
Streamlit Compare page or saved run data for final-target comparison.

## Service endpoints

### `GET /`

Returns API discovery links.

### `GET /health`

Returns the version and whether shared `src` modules loaded. It returns no
secret values.

## Error behavior

| Status | Meaning |
| --- | --- |
| `400` | Business input cannot be processed |
| `401` | Missing, invalid, or expired authentication |
| `404` | Resource absent or not owned by the caller |
| `422` | Request validation failed |
| `500` | Analysis or upstream processing failed |
| `503` | Required shared modules are unavailable |

Do not expose exception traces, provider credentials, password hashes, private
holdings, or copyrighted article bodies in responses or logs.

## Contract verification

```powershell
Invoke-WebRequest http://localhost:8000/openapi.json -OutFile openapi.json
```

Compare this document with the generated schema in CI. Before making the API a
public contract, add a prefix such as `/api/v1`, rate limits, HTTPS, request
IDs, structured audit logs, and managed secrets.
