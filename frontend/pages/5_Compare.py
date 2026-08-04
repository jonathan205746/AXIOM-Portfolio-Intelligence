"""
frontend/pages/5_Compare.py  (Bloomberg Terminal Edition)
----------------------------------------------------------
Benchmark comparison with terminal aesthetic.
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Any
from src.database.db import get_portfolio_holdings
from src.data.stock_fetcher import fetch_stock_data

st.set_page_config(page_title="COMPARE | AI Portfolio Optimizer", page_icon="⚖", layout="wide")

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

results = st.session_state.get("results")
if not results:
    st.warning("RUN ANALYSIS FIRST")
    if st.button("▣ GO TO ANALYSIS", type="primary"):
        st.switch_page("pages/3_Analysis.py")
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
}<link href="https://fonts.googleapis.com/icon?family=Material+Icons"
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
    _render_nav("pages/5_Compare.py")
    st.markdown('</div>', unsafe_allow_html=True)
    if st.button("◀ LOGOUT", width='stretch'):
        for k in ["logged_in", "user", "current_portfolio", "results"]:
            st.session_state.pop(k, None)
        st.switch_page("app.py")
    st.markdown('<div class="bb-sidebar-footer">TERMINAL EDITION v5.0</div>', unsafe_allow_html=True)

st.markdown(f'<div class="bb-cmd-bar"><span class="bb-cmd-prompt">➜</span><span style="color:var(--text-dim);">BENCHMARK COMPARISON // PORTFOLIO: {portfolio["name"].upper()}</span></div>', unsafe_allow_html=True)
st.markdown('<div style="padding:12px 0;"><span style="font-size:1.4rem;font-weight:800;color:var(--text);letter-spacing:-1px;">⚖ BENCHMARK COMPARISON</span><br><span style="font-size:0.8rem;color:var(--text-dim);">OPTIMIZED VS EQUAL-WEIGHT VS S&P 500 (SPY)</span></div>', unsafe_allow_html=True)

available = results.get("tickers", [])
final_weights = results.get("final_weights", {})
returns_df = results.get("returns", pd.DataFrame())
opt_result = results.get("opt_result", {})
baseline = results.get("baseline", {})

if returns_df.empty or not available:
    st.error("NO RETURN DATA — RE-RUN ANALYSIS")
    st.stop()

def extract_close_series(raw_df: pd.DataFrame, ticker: str) -> pd.Series:
    cols = raw_df.columns
    if isinstance(cols, pd.MultiIndex):
        if "Close" in cols.get_level_values(0):
            level0 = raw_df["Close"]
            if isinstance(level0, pd.DataFrame) and ticker in level0.columns:
                return level0[ticker].dropna()
        first_col = raw_df.iloc[:, 0]
        if isinstance(first_col, pd.Series):
            return first_col.dropna()
        return pd.Series(first_col).dropna()
    if "Close" in cols:
        close_col = raw_df["Close"]
        if isinstance(close_col, pd.DataFrame):
            if ticker in close_col.columns:
                return close_col[ticker].dropna()
            first_series = close_col.iloc[0]
            if isinstance(first_series, pd.Series):
                return first_series.dropna()
            return pd.Series(first_series).dropna()
        else:
            return close_col.dropna()
    if ticker in cols:
        return raw_df[ticker].dropna()
    numeric_cols = raw_df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        return raw_df[numeric_cols[0]].dropna()
    raise ValueError(f"CANNOT EXTRACT CLOSE PRICE FOR {ticker}")

with st.spinner("FETCHING SPY BENCHMARK..."):
    spy_available = False
    try:
        raw_spy = fetch_stock_data(["SPY"])
        spy_returns = extract_close_series(raw_spy, "SPY").pct_change().dropna()
        common_idx = returns_df.index.intersection(spy_returns.index)
        aligned_returns = returns_df.loc[common_idx]
        aligned_spy = pd.Series(spy_returns.loc[common_idx].astype(float).dropna(), name="SPY")
        if len(common_idx) < 10:
            st.warning(f"ONLY {len(common_idx)} OVERLAPPING DAYS WITH SPY")
        spy_available = True
    except Exception as e:
        st.error(f"SPY FETCH FAILED: {e}")

if not spy_available:
    st.stop()

aligned_tickers = [t for t in available if t in aligned_returns.columns]
if not aligned_tickers:
    st.error("NO OVERLAPPING TICKERS")
    st.stop()

w_opt_raw = np.array([final_weights.get(t, 0.0) for t in aligned_tickers])
w_eq_raw = np.array([1.0 / len(aligned_tickers)] * len(aligned_tickers))
w_opt = w_opt_raw / w_opt_raw.sum() if w_opt_raw.sum() > 0 else w_eq_raw
w_eq = w_eq_raw / w_eq_raw.sum()
ret_matrix = aligned_returns[aligned_tickers].fillna(0).values
opt_daily = pd.Series(ret_matrix @ w_opt, index=aligned_returns.index)
eq_daily = pd.Series(ret_matrix @ w_eq, index=aligned_returns.index)
cum_opt = (1 + opt_daily).cumprod()
cum_eq = (1 + eq_daily).cumprod()
cum_spy = (1 + aligned_spy.astype(float)).cumprod()

TRADING_DAYS = 252

def compute_sharpe(ret_series: pd.Series, rf: float = 0.05) -> float:
    s = ret_series.dropna()
    if len(s) < 2:
        return 0.0
    ann_ret = s.mean() * TRADING_DAYS
    ann_vol = s.std() * np.sqrt(TRADING_DAYS)
    return (ann_ret - rf) / ann_vol if ann_vol > 0 else 0.0

def max_drawdown_pct(cum_series: pd.Series) -> float:
    rolling_max = cum_series.cummax()
    drawdown = (cum_series - rolling_max) / rolling_max
    return float(drawdown.min() * 100)

PLOTLY_THEME: dict[str, Any] = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="JetBrains Mono, monospace", color="#e5e5e5", size=11),
    margin=dict(l=10, r=10, t=40, b=10),
    xaxis=dict(gridcolor="#2a2a2a", linecolor="#3a3a3a"),
    yaxis=dict(gridcolor="#2a2a2a", linecolor="#3a3a3a"),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#2a2a2a", borderwidth=1)
)

st.markdown('<div class="bb-panel bb-panel-accent"><div class="bb-panel-header"><span class="bb-panel-title">◈ Performance Metrics</span></div><div class="bb-panel-body">', unsafe_allow_html=True)
metrics_data = {
    "Metric": ["TOTAL RETURN", "ANN RETURN", "ANN VOL", "SHARPE", "MAX DD"],
    "OPTIMIZED": [
        f"{(cum_opt.iloc[-1] - 1) * 100:.2f}%",
        f"{opt_daily.mean() * TRADING_DAYS * 100:.2f}%",
        f"{opt_daily.std() * np.sqrt(TRADING_DAYS) * 100:.2f}%",
        f"{compute_sharpe(opt_daily):.3f}",
        f"{max_drawdown_pct(cum_opt):.2f}%"
    ],
    "EQUAL-WEIGHT": [
        f"{(cum_eq.iloc[-1] - 1) * 100:.2f}%",
        f"{eq_daily.mean() * TRADING_DAYS * 100:.2f}%",
        f"{eq_daily.std() * np.sqrt(TRADING_DAYS) * 100:.2f}%",
        f"{compute_sharpe(eq_daily):.3f}",
        f"{max_drawdown_pct(cum_eq):.2f}%"
    ],
    "SPY": [
        f"{(cum_spy.iloc[-1] - 1) * 100:.2f}%",
        f"{aligned_spy.mean() * TRADING_DAYS * 100:.2f}%",
        f"{aligned_spy.std() * np.sqrt(TRADING_DAYS) * 100:.2f}%",
        f"{compute_sharpe(aligned_spy):.3f}",
        f"{max_drawdown_pct(cum_spy):.2f}%"
    ]
}
st.dataframe(pd.DataFrame(metrics_data),   hide_index=True)
st.markdown('</div></div>', unsafe_allow_html=True)

st.markdown('<div class="bb-panel"><div class="bb-panel-header"><span class="bb-panel-title">◫ KPI Summary</span></div><div class="bb-panel-body">', unsafe_allow_html=True)
k1, k2, k3 = st.columns(3)
k1.metric("OPT TOTAL RETURN", f"{(cum_opt.iloc[-1]-1)*100:.2f}%", delta=f"{((cum_opt.iloc[-1]-1) - (cum_spy.iloc[-1]-1))*100:.2f}% vs SPY")
k2.metric("OPT SHARPE", f"{compute_sharpe(opt_daily):.3f}", delta=f"{compute_sharpe(opt_daily) - compute_sharpe(aligned_spy):.3f} vs SPY")
k3.metric("OPT MAX DD", f"{max_drawdown_pct(cum_opt):.2f}%", delta=f"{max_drawdown_pct(cum_opt) - max_drawdown_pct(cum_spy):.2f}% vs SPY", delta_color="inverse")
st.markdown('</div></div>', unsafe_allow_html=True)

st.markdown('<div class="bb-panel bb-panel-green"><div class="bb-panel-header"><span class="bb-panel-title">◈ Cumulative Returns vs Benchmark</span></div><div class="bb-panel-body">', unsafe_allow_html=True)
fig = go.Figure()
fig.add_trace(go.Scatter(x=cum_opt.index, y=(cum_opt - 1) * 100, mode='lines', name="OPTIMIZED", line=dict(color="#ff6600", width=2.5)))
fig.add_trace(go.Scatter(x=cum_eq.index, y=(cum_eq - 1) * 100, mode='lines', name="EQUAL-WEIGHT", line=dict(color="#888888", width=1.5, dash="dash")))
fig.add_trace(go.Scatter(x=cum_spy.index, y=(cum_spy - 1) * 100, mode='lines', name="SPY", line=dict(color="#00d084", width=1.5, dash="dot")))
fig.add_hline(y=0, line_color="#3a3a3a", line_width=0.8)
fig.update_layout(**PLOTLY_THEME)
fig.update_layout(xaxis_title="DATE", yaxis_title="CUMULATIVE RETURN (%)", height=450, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
st.plotly_chart(fig, width='stretch')
st.markdown('</div></div>', unsafe_allow_html=True)

st.markdown('<div class="bb-panel"><div class="bb-panel-header"><span class="bb-panel-title">◫ Rolling 60-Day Sharpe</span></div><div class="bb-panel-body">', unsafe_allow_html=True)
MIN_DAYS = 65
if len(opt_daily) < MIN_DAYS:
    st.info(f"INSUFFICIENT DATA: {len(opt_daily)} DAYS (NEED {MIN_DAYS})")
else:
    def rolling_sharpe(series: pd.Series, window: int = 60, rf_daily: float = 0.05/252) -> pd.Series:
        roll_mean = series.rolling(window).mean()
        roll_std = series.rolling(window).std()
        return ((roll_mean - rf_daily) / roll_std * np.sqrt(252)).where(roll_std > 0)
    roll_opt = rolling_sharpe(opt_daily)
    roll_eq = rolling_sharpe(eq_daily)
    roll_spy = rolling_sharpe(aligned_spy)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=roll_opt.index, y=roll_opt, mode='lines', name="OPTIMIZED", line=dict(color="#ff6600", width=2)))
    fig2.add_trace(go.Scatter(x=roll_eq.index, y=roll_eq, mode='lines', name="EQUAL-WEIGHT", line=dict(color="#888888", width=1.5, dash="dash")))
    fig2.add_trace(go.Scatter(x=roll_spy.index, y=roll_spy, mode='lines', name="SPY", line=dict(color="#00d084", width=1.5, dash="dot")))
    fig2.add_hline(y=0, line_color="#3a3a3a", line_width=0.8)
    fig2.update_layout(**PLOTLY_THEME)
    fig2.update_layout(xaxis_title="DATE", yaxis_title="ROLLING SHARPE (60D)", height=400, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig2, width='stretch')
st.markdown('</div></div>', unsafe_allow_html=True)

st.markdown('<div class="bb-panel bb-panel-red"><div class="bb-panel-header"><span class="bb-panel-title">◫ Drawdown Comparison</span></div><div class="bb-panel-body">', unsafe_allow_html=True)
def drawdown_series(cum: pd.Series) -> pd.Series:
    return ((cum - cum.cummax()) / cum.cummax()) * 100

dd_opt = drawdown_series(cum_opt)
dd_eq = drawdown_series(cum_eq)
dd_spy = drawdown_series(cum_spy)
fig3 = go.Figure()
fig3.add_trace(go.Scatter(x=dd_opt.index, y=dd_opt, mode='lines', name="OPTIMIZED", line=dict(color="#ff6600", width=1.5), fill='tozeroy', fillcolor="rgba(255,102,0,0.1)"))
fig3.add_trace(go.Scatter(x=dd_eq.index, y=dd_eq, mode='lines', name="EQUAL-WEIGHT", line=dict(color="#888888", width=1.2, dash="dash")))
fig3.add_trace(go.Scatter(x=dd_spy.index, y=dd_spy, mode='lines', name="SPY", line=dict(color="#00d084", width=1.2, dash="dot")))
fig3.add_hline(y=0, line_color="#3a3a3a", line_width=0.8)
fig3.update_layout(**PLOTLY_THEME)
fig3.update_layout(xaxis_title="DATE", yaxis_title="DRAWDOWN (%)", height=380, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
st.plotly_chart(fig3, width='stretch')
st.markdown('</div></div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("PAST PERFORMANCE DOES NOT GUARANTEE FUTURE RESULTS | AI PORTFOLIO OPTIMIZER Terminal Edition")
