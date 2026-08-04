"""
frontend/pages/4_History.py  (Bloomberg Terminal Edition)
----------------------------------------------------------
History tracking with terminal aesthetic.
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Any
from src.database.db import get_portfolio_history, get_sharpe_trend

st.set_page_config(page_title="HISTORY | AI Portfolio Optimizer", page_icon="📊", layout="wide")

if not st.session_state.get("logged_in"):
    st.warning("AUTHENTICATION REQUIRED")
    st.page_link("pages/1_Login.py", label="▶ GO TO LOGIN")
    st.stop()

user = st.session_state["user"]
portfolio = st.session_state.get("current_portfolio")
if not portfolio:
    st.warning("SELECT PORTFOLIO FIRST")
    st.page_link("pages/2_Portfolio.py", label="◫ GO TO PORTFOLIO")
    st.stop()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700;800&display=swap');
:root {
  --bg: #050505; --bg-panel: #0a0a0a; --bg-hover: #141414; --bg-active: #1a1a1a; --bg-input: #0d0d0d;
  --text: #e5e5e5; --text-dim: #888888; --text-faded: #555555; --text-inverse: #050505;
  --accent: #ff6600; --accent-dim: #cc5200; --accent-glow: rgba(255,102,0,0.25); --accent-soft: rgba(255,102,0,0.1);
  --positive: #00d084; --positive-dim: #00a868; --positive-bg: rgba(0,208,132,0.08);
  --negative: #ff3333; --negative-dim: #cc0000; --negative-bg: rgba(255,51,51,0.08);
  --border: #2a2a2a; --border-bright: #3a3a3a; --grid: #111111;
  --font: 'JetBrains Mono','Courier New',monospace; --radius: 0px; --radius-sm: 2px;
}
<link href="https://fonts.googleapis.com/icon?family=Material+Icons"
      rel="stylesheet">
* { font-family: var(--font) !important; }
.block-container { padding: 0.5rem 1rem 1rem !important; max-width: 100% !important; }
[data-testid="stAppViewContainer"] { background: var(--bg) !important; }
[data-testid="stSidebarNav"] { display: none !important; }
[data-testid="stSidebar"] { background: var(--bg-panel) !important; border-right: 1px solid var(--border) !important; min-width: 280px !important; }
[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }
.bb-sidebar-header { background: linear-gradient(90deg, var(--accent), var(--accent-dim)); padding: 12px 16px; border-bottom: 1px solid var(--border); }
.bb-sidebar-header h1 { color: var(--text-inverse) !important; font-size: 0.85rem !important; font-weight: 800 !important; letter-spacing: 1px; margin: 0; }
.bb-section { padding: 8px 16px; border-bottom: 1px solid var(--border); }
.bb-section-title { font-size: 0.6rem; font-weight: 700; color: var(--accent) !important; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px; }
.bb-ticker-row { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; font-size: 0.75rem; border-bottom: 1px dotted var(--border); }
.bb-ticker-row:last-child { border-bottom: none; }
.bb-ticker-symbol { color: var(--text); font-weight: 600; }
.bb-ticker-price { color: var(--text-dim); }
.bb-ticker-change-pos { color: var(--positive); font-weight: 700; }
.bb-ticker-change-neg { color: var(--negative); font-weight: 700; }
.bb-nav-item { display: flex; align-items: center; gap: 10px; padding: 8px 12px; margin: 2px 0; border-left: 3px solid transparent; color: var(--text-dim) !important; font-size: 0.8rem; font-weight: 500; text-decoration: none !important; transition: all 0.15s; cursor: pointer; }
.bb-nav-item:hover { background: var(--bg-hover); border-left-color: var(--accent-dim); color: var(--text) !important; }
.bb-nav-item.active { background: var(--accent-soft); border-left-color: var(--accent); color: var(--accent) !important; font-weight: 700; }
.bb-user-block { background: var(--bg-hover); border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); padding: 12px 16px; display: flex; align-items: center; gap: 10px; }
.bb-user-avatar { width: 28px; height: 28px; background: var(--accent); color: var(--text-inverse); border-radius: var(--radius-sm); display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 800; }
.bb-user-name { font-size: 0.8rem; font-weight: 600; color: var(--text); }
.bb-user-role { font-size: 0.65rem; color: var(--text-dim); }
.bb-sidebar-footer { padding: 10px 16px; font-size: 0.6rem; color: var(--text-faded); border-top: 1px solid var(--border); text-align: center; }
.bb-cmd-bar { background: var(--bg-panel); border-bottom: 1px solid var(--border); padding: 8px 16px; display: flex; align-items: center; gap: 12px; font-size: 0.8rem; margin-bottom: 1px; }
.bb-cmd-prompt { color: var(--accent); font-weight: 700; }
.bb-panel { background: var(--bg-panel); border: 1px solid var(--border); margin-bottom: 1px; }
.bb-panel-header { background: var(--bg-hover); border-bottom: 1px solid var(--border); padding: 8px 12px; display: flex; align-items: center; justify-content: space-between; }
.bb-panel-title { font-size: 0.75rem; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: 1px; }
.bb-panel-subtitle { font-size: 0.65rem; color: var(--text-faded); }
.bb-panel-body { padding: 12px; }
.bb-panel-accent { border-top: 2px solid var(--accent); }
.stButton > button { background: var(--accent) !important; color: var(--text-inverse) !important; border: none !important; border-radius: var(--radius-sm) !important; font-family: var(--font) !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; font-size: 0.75rem !important; }
.stButton > button:hover { background: var(--accent-dim) !important; box-shadow: 0 0 12px var(--accent-glow) !important; }
[data-testid="stMetric"] { background: var(--bg-panel) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; }
[data-testid="stMetricValue"] { font-family: var(--font) !important; font-weight: 700 !important; color: var(--text) !important; }
[data-testid="stMetricLabel"] { font-family: var(--font) !important; color: var(--text-dim) !important; text-transform: uppercase !important; font-size: 0.6rem !important; letter-spacing: 1px !important; }
.badge-success { background: var(--positive-bg); color: var(--positive); padding: 2px 8px; border-radius: 2px; font-size: 0.7rem; font-weight: 700; }
.badge-warning { background: var(--negative-bg); color: var(--negative); padding: 2px 8px; border-radius: 2px; font-size: 0.7rem; font-weight: 700; }
@media (max-width: 768px) { .block-container { padding: 0.5rem !important; } }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def _market_snapshot():
    try:
        import yfinance as yf
        out = {}
        for t, n in [("^GSPC", "SPX"), ("^NSEI", "NIFTY"), ("^IXIC", "NDX"), ("BTC-USD", "BTC")]:
            h = yf.Ticker(t).history(period="2d")
            if len(h) >= 2:
                c, p = h["Close"].iloc[-1], h["Close"].iloc[-2]
                out[n] = {"price": c, "change": (c - p) / p * 100}
        return out
    except Exception:
        return {"SPX": {"price": 4500.0, "change": 0.45}, "NIFTY": {"price": 22500.0, "change": -0.12}, "NDX": {"price": 14000.0, "change": 0.78}, "BTC": {"price": 67500.0, "change": 1.23}}

market_data = _market_snapshot()

def _render_nav(current_page: str):
    pages = [("app.py", "⌂", "DASHBOARD"), ("pages/2_Portfolio.py", "◫", "PORTFOLIO"), ("pages/3_Analysis.py", "▣", "ANALYSIS"), ("pages/4_History.py", "◫", "HISTORY"), ("pages/5_Compare.py", "⚖", "COMPARE")]
    for page, icon, label in pages:
        active = " active" if page == current_page else ""
        if page == current_page:
            st.markdown(f'<div class="bb-nav-item{active}">{icon}&nbsp;&nbsp;{label}</div>', unsafe_allow_html=True)
        else:
            st.page_link(page, label=f"{icon}  {label}")

with st.sidebar:
    st.markdown('<div class="bb-sidebar-header"><h1>▶ AI PORTFOLIO OPTIMIZER</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="bb-section"><div class="bb-section-title">Market Data</div>', unsafe_allow_html=True)
    for name, data in market_data.items():
        cls = "bb-ticker-change-pos" if data["change"] >= 0 else "bb-ticker-change-neg"
        sign = "+" if data["change"] >= 0 else ""
        st.markdown(f'<div class="bb-ticker-row"><span class="bb-ticker-symbol">{name}</span><div><span class="bb-ticker-price">{data["price"]:,.2f}</span> <span class="{cls}">{sign}{data["change"]:.2f}%</span></div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    uname = user.get("username", "USER")
    st.markdown(f'<div class="bb-user-block"><div class="bb-user-avatar">{uname[:2].upper()}</div><div><div class="bb-user-name">{uname.upper()}</div><div class="bb-user-role">INVESTOR ACCOUNT</div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="bb-section"><div class="bb-section-title">Navigation</div>', unsafe_allow_html=True)
    _render_nav("pages/4_History.py")
    st.markdown('</div>', unsafe_allow_html=True)
    if st.button("◀ LOGOUT", width='stretch'):
        for k in ["logged_in", "user", "current_portfolio", "results"]:
            st.session_state.pop(k, None)
        st.switch_page("app.py")
    st.markdown('<div class="bb-sidebar-footer">TERMINAL EDITION v5.0</div>', unsafe_allow_html=True)

st.markdown(f'<div class="bb-cmd-bar"><span class="bb-cmd-prompt">➜</span><span style="color:var(--text-dim);">HISTORY // PORTFOLIO: {portfolio["name"].upper()}</span></div>', unsafe_allow_html=True)
st.markdown('<div style="padding:12px 0;"><span style="font-size:1.4rem;font-weight:800;color:var(--text);letter-spacing:-1px;">◫ PERFORMANCE HISTORY</span><br><span style="font-size:0.8rem;color:var(--text-dim);">REVIEW OPTIMIZATION RUN PROGRESSION</span></div>', unsafe_allow_html=True)

history = get_portfolio_history(portfolio["id"], limit=30)

if not history:
    st.info("NO OPTIMIZATION RUNS YET")
    st.page_link("pages/3_Analysis.py", label="▣ RUN FIRST ANALYSIS")
    st.stop()

PLOTLY_THEME: dict[str, Any] = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="JetBrains Mono, monospace", color="#e5e5e5", size=11),
    margin=dict(l=10, r=10, t=40, b=10),
    xaxis=dict(gridcolor="#2a2a2a", linecolor="#3a3a3a"),
    yaxis=dict(gridcolor="#2a2a2a", linecolor="#3a3a3a"),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#2a2a2a", borderwidth=1)
)

st.markdown('<div class="bb-panel bb-panel-accent"><div class="bb-panel-header"><span class="bb-panel-title">◈ Sharpe Ratio Over Time</span></div><div class="bb-panel-body">', unsafe_allow_html=True)
trend = get_sharpe_trend(portfolio["id"])
if len(trend) >= 2:
    trend_df = pd.DataFrame(trend)
    trend_df["date"] = pd.to_datetime(trend_df["date"], errors="coerce")
    trend_df = trend_df.dropna(subset=["date"]).sort_values("date")
    fig = go.Figure()

    base_sharpe = trend_df["sharpe_ratio"].iloc[0]
    base_return = trend_df["expected_return"].iloc[0]
    base_vol = trend_df["volatility"].iloc[0]

    sharpe_pct = (trend_df["sharpe_ratio"] / base_sharpe - 1) * 100
    return_pct = (trend_df["expected_return"] / base_return - 1) * 100
    vol_pct = (trend_df["volatility"] / base_vol - 1) * 100

    fig.add_trace(go.Scatter(x=trend_df["date"], y=sharpe_pct, mode='lines+markers',
              name="SHARPE", line=dict(color='#ff6600', width=2), marker=dict(size=5)))
    fig.add_trace(go.Scatter(x=trend_df["date"], y=return_pct, mode='lines+markers',
              name="RETURN", line=dict(color='#00d084', width=2), marker=dict(size=5)))
    fig.add_trace(go.Scatter(x=trend_df["date"], y=vol_pct, mode='lines+markers',
              name="VOLATILITY", line=dict(color='#ff3333', width=2), marker=dict(size=5)))
    fig.update_layout(**PLOTLY_THEME)
    st.plotly_chart(fig, width='stretch')
else:
    st.info("RUN AT LEAST 2 ANALYSES FOR TRENDS")
st.markdown('</div></div>', unsafe_allow_html=True)

st.markdown('<div class="bb-panel"><div class="bb-panel-header"><span class="bb-panel-title">◫ Recommendation Changes</span></div><div class="bb-panel-body">', unsafe_allow_html=True)
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
        badge = '<span class="badge-warning">CHANGED</span>' if changed else '<span class="badge-success">UNCHANGED</span>'
        st.markdown(f"**{ticker}:** {badge}", unsafe_allow_html=True)
        st.markdown(f"- PREVIOUS: {prev if prev != 'N/A' else '—'}")
        st.markdown(f"- CURRENT: {curr if curr != 'N/A' else '—'}")
        st.markdown("---")
else:
    st.info("RUN AT LEAST 2 ANALYSES TO COMPARE")
st.markdown('</div></div>', unsafe_allow_html=True)

st.markdown('<div class="bb-panel bb-panel-green"><div class="bb-panel-header"><span class="bb-panel-title">◫ All Past Runs</span></div><div class="bb-panel-body">', unsafe_allow_html=True)
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
    st.dataframe(pd.DataFrame(rows),   hide_index=True)
st.markdown('</div></div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("AI PORTFOLIO OPTIMIZER | Terminal Edition")
