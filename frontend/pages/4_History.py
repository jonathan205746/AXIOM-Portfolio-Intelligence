"""
Axiom Performance History v2.1
Optimization run tracking with glassmorphic terminal aesthetic.
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Any
from src.database.db import get_portfolio_history, get_sharpe_trend

st.set_page_config(page_title="History | Axiom", page_icon="◫", layout="wide")

if not st.session_state.get("logged_in"):
    st.warning("Authentication required")
    st.page_link("pages/1_Login.py", label="▶ Go to Login")
    st.stop()

user = st.session_state["user"]
portfolio = st.session_state.get("current_portfolio")
if not portfolio:
    st.warning("Select a portfolio first")
    st.page_link("pages/2_Portfolio.py", label="◫ Go to Portfolio")
    st.stop()

# ── Design System ───────────────────────────────────────────
from frontend.ui.theme import inject_theme, apply_plotly_theme
from frontend.ui.components import (
    page_sidebar, command_bar, section_header, metric_grid,
    glass_container, info_card, badge
)
inject_theme()

# ── Market Data ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def _market_snapshot():
    fallback = {
        "SPX": {"price": 4500.0, "change": 0.45},
        "NIFTY": {"price": 22500.0, "change": -0.12},
        "NDX": {"price": 14000.0, "change": 0.78},
        "BTC": {"price": 67500.0, "change": 1.23},
    }
    out = {}
    try:
        import yfinance as yf
        for t, n in [("^GSPC", "SPX"), ("^NSEI", "NIFTY"), ("^IXIC", "NDX"), ("BTC-USD", "BTC")]:
            try:
                h = yf.Ticker(t).history(period="2d")
                if len(h) >= 2:
                    c, p = h["Close"].iloc[-1], h["Close"].iloc[-2]
                    out[n] = {"price": float(c), "change": float((c - p) / p * 100)}
                else:
                    out[n] = fallback[n]
            except Exception:
                out[n] = fallback[n]
    except Exception:
        return fallback
    return out

market_data = _market_snapshot()

# ── Sidebar & Command Bar ───────────────────────────────────
page_sidebar("pages/4_History.py", user=user, market_data=market_data)
command_bar("AXIOM / HISTORY", f"PORTFOLIO: {portfolio['name'].upper()}")

# ── Header ──────────────────────────────────────────────────
st.markdown("""
<div style="padding: 20px 0 12px;">
    <div style="font-size:1.6rem;font-weight:800;color:#f0f0f5;letter-spacing:-0.03em;font-family:'Inter',sans-serif;">
        Performance History
    </div>
    <div style="font-size:0.85rem;color:#8b8b9e;margin-top:6px;">
        Review optimization run progression and strategy evolution
    </div>
</div>
""", unsafe_allow_html=True)

history = get_portfolio_history(portfolio["id"], limit=30)

if not history:
    info_card(
        "No Optimization Runs",
        "Run your first analysis to begin tracking portfolio performance over time.",
        badge("START HERE", "accent"),
        accent="cyan"
    )
    if st.button("▣ Run First Analysis →", type="primary", use_container_width=True):
        st.switch_page("pages/3_Analysis.py")
    st.stop()

# ── Summary Metrics ─────────────────────────────────────────
latest = history[0] if history else None
if latest:
    section_header("Latest Run Summary", f"Recorded {latest.get('run_date', 'N/A')[:10]}", accent="green")
    metrics = [
        {"label": "Sharpe Ratio", "value": f"{latest.get('sharpe_ratio', 0):.3f}", "tone": "cyan", "icon": "◉"},
        {"label": "Expected Return", "value": f"{latest.get('expected_return', 0)*100:.2f}%", "tone": "positive" if latest.get("expected_return", 0) > 0 else "negative", "icon": "▲"},
        {"label": "Volatility", "value": f"{latest.get('volatility', 0)*100:.2f}%", "tone": "negative", "icon": "◊"},
        {"label": "Alpha Used", "value": f"{latest.get('alpha_used', 0):.2f}", "tone": "accent", "icon": "◈"},
    ]
    metric_grid(metrics, columns=4)

# ── Sharpe Trend Chart ──────────────────────────────────────
section_header("Sharpe Ratio Over Time", "Performance trajectory", accent="primary")
glass_container(accent="primary")

trend = get_sharpe_trend(portfolio["id"])
if len(trend) >= 2:
    trend_df = pd.DataFrame(trend)
    trend_df["date"] = pd.to_datetime(trend_df["date"], errors="coerce")
    trend_df = trend_df.dropna(subset=["date"]).sort_values("date")

    base_sharpe = trend_df["sharpe_ratio"].iloc[0]
    base_return = trend_df["expected_return"].iloc[0]
    base_vol = trend_df["volatility"].iloc[0]

    sharpe_pct = (trend_df["sharpe_ratio"] / base_sharpe - 1) * 100
    return_pct = (trend_df["expected_return"] / base_return - 1) * 100
    vol_pct = (trend_df["volatility"] / base_vol - 1) * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend_df["date"], y=sharpe_pct, mode='lines+markers',
        name="Sharpe", line=dict(color='#FF6B35', width=2.5),
        marker=dict(size=6, color='#FF6B35', line=dict(color='#fff', width=1))
    ))
    fig.add_trace(go.Scatter(
        x=trend_df["date"], y=return_pct, mode='lines+markers',
        name="Return", line=dict(color='#10B981', width=2),
        marker=dict(size=5, color='#10B981')
    ))
    fig.add_trace(go.Scatter(
        x=trend_df["date"], y=vol_pct, mode='lines+markers',
        name="Volatility", line=dict(color='#F43F5E', width=2),
        marker=dict(size=5, color='#F43F5E')
    ))
    fig.add_hline(y=0, line_color="rgba(255,255,255,0.1)", line_width=1)
    fig.update_layout(
        title="Relative Change from First Run (%)",
        xaxis_title="Date", yaxis_title="Change (%)",
        height=420, hovermode="x unified"
    )
    fig = apply_plotly_theme(fig)
    st.plotly_chart(fig, width='stretch')
else:
    snapshot = pd.DataFrame({
        "Metric": ["Sharpe Ratio", "Expected Return (%)", "Volatility (%)"],
        "Value": [
            latest.get("sharpe_ratio", 0) if latest else 0,
            latest.get("expected_return", 0) * 100 if latest else 0,
            latest.get("volatility", 0) * 100 if latest else 0,
        ],
        "Color": ["#00D9FF", "#10B981", "#F43F5E"],
    })
    fig = go.Figure(go.Bar(
        x=snapshot["Metric"], y=snapshot["Value"],
        marker_color=snapshot["Color"], text=snapshot["Value"].map(lambda value: f"{value:.2f}"),
        textposition="outside",
    ))
    fig.update_layout(
        title="Latest Run Performance Snapshot",
        yaxis_title="Metric Value",
        height=420,
        showlegend=False,
    )
    st.plotly_chart(apply_plotly_theme(fig), width="stretch")

# ── Recommendation Changes ──────────────────────────────────
section_header("Recommendation Changes", "AI guidance evolution", accent="violet")
glass_container(accent="violet")

def _normalize_recommendations(items):
    normalized = {}
    for item in items or []:
        if isinstance(item, dict):
            ticker = item.get("ticker") or item.get("symbol") or item.get("name") or "N/A"
            text = item.get("recommendation") or item.get("text") or item.get("reason") or item.get("message") or ""
        elif isinstance(item, str):
            ticker, text = "N/A", item
        else:
            continue
        normalized[str(ticker)] = str(text).strip()
    return normalized

if len(history) >= 2:
    latest = history[0]
    previous = history[1]
    latest_recs = _normalize_recommendations(latest.get("recommendations", []))
    previous_recs = _normalize_recommendations(previous.get("recommendations", []))

    for ticker in sorted(set(latest_recs) | set(previous_recs)):
        curr = latest_recs.get(ticker, "") or "N/A"
        prev = previous_recs.get(ticker, "") or "N/A"
        changed = str(curr).strip() != str(prev).strip()
        badge_html = badge("CHANGED", "warning") if changed else badge("UNCHANGED", "positive")

        st.markdown(f'''
        <div style="
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.04);
            border-radius: 10px;
            padding: 12px 14px;
            margin-bottom: 8px;
            transition: all 0.15s ease;
        " onmouseover="this.style.background='rgba(255,255,255,0.04)'" onmouseout="this.style.background='rgba(255,255,255,0.02)'">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                <strong style="color:#f0f0f5;font-size:0.85rem;font-family:'Inter',sans-serif;">{ticker}</strong>
                {badge_html}
            </div>
            <div style="font-size:0.75rem;color:#4a4a5e;margin-bottom:2px;">PREVIOUS: <span style="color:#8b8b9e;">{prev if prev != 'N/A' else '—'}</span></div>
            <div style="font-size:0.75rem;color:#4a4a5e;">CURRENT: <span style="color:#f0f0f5;">{curr if curr != 'N/A' else '—'}</span></div>
        </div>
        ''', unsafe_allow_html=True)
else:
    info_card(
        "No Comparison Available",
        "Run at least 2 analyses to compare recommendation changes between runs.",
        badge("NEED 2+ RUNS", "warning"),
        accent="amber"
    )


# ── All Past Runs Table ─────────────────────────────────────
section_header("All Past Runs", f"{len(history)} records", accent="green")
glass_container(accent="green")

rows = []
for run in history:
    tickers = run.get("tickers") or []
    rows.append({
        "Date": run.get("run_date"),
        "Tickers": ", ".join(tickers[:4]) + ("..." if len(tickers) > 4 else ""),
        "Alpha": run.get("alpha_used"),
        "Sharpe": f"{run['sharpe_ratio']:.4f}" if run.get("sharpe_ratio") else "N/A",
        "Return": f"{run['expected_return']*100:.2f}%" if run.get("expected_return") else "N/A",
        "Volatility": f"{run['volatility']*100:.2f}%" if run.get("volatility") else "N/A",
    })

if rows:
    st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch')
else:
    st.info("No runs recorded yet")


st.markdown("""
<div style="border-top:1px solid rgba(255,255,255,0.06);margin-top:32px;padding-top:20px;">
    <div style="font-size:0.65rem;color:#4a4a5e;text-align:center;letter-spacing:0.05em;">
        AXIOM Portfolio Intelligence · Terminal Edition
    </div>
</div>
""", unsafe_allow_html=True)
