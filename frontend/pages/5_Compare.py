"""
Axiom Benchmark Comparison v2.1
Portfolio vs SPY & equal-weight with glassmorphic terminal aesthetic.
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

# ── Design System ───────────────────────────────────────────
from frontend.ui.theme import inject_theme, apply_plotly_theme
from frontend.ui.components import (
    page_sidebar, command_bar, section_header, metric_grid,
    glass_container, info_card, badge
)

st.set_page_config(page_title="Compare | Axiom", page_icon="⚖", layout="wide")
inject_theme()

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

results = st.session_state.get("results")
if not results:
    info_card(
        "Analysis Required",
        "Run portfolio optimization first to generate benchmark comparison data.",
        badge("RUN ANALYSIS", "accent"),
        accent="cyan"
    )
    if st.button("▣ Go to Analysis →", type="primary", use_container_width=True):
        st.switch_page("pages/3_Analysis.py")
    st.stop()

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
page_sidebar("pages/5_Compare.py", user=user, market_data=market_data)
command_bar("AXIOM / BENCHMARK", f"PORTFOLIO: {portfolio['name'].upper()}")

# ── Header ──────────────────────────────────────────────────
st.markdown("""
<div style="padding: 20px 0 12px;">
    <div style="font-size:1.6rem;font-weight:800;color:#f0f0f5;letter-spacing:-0.03em;font-family:'Inter',sans-serif;">
        Benchmark Comparison
    </div>
    <div style="font-size:0.85rem;color:#8b8b9e;margin-top:6px;">
        Final Target vs Equal-Weight vs S&P 500 (SPY)
    </div>
</div>
""", unsafe_allow_html=True)

# ── Data Prep ───────────────────────────────────────────────
available = results.get("tickers", [])
final_weights = results.get("final_weights", {})
returns_df = results.get("returns", pd.DataFrame())

if returns_df.empty or not available:
    st.error("No return data — re-run analysis")
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
    raise ValueError(f"Cannot extract close price for {ticker}")

# ── Fetch SPY ───────────────────────────────────────────────
with st.spinner("Fetching SPY benchmark..."):
    spy_available = False
    try:
        raw_spy = fetch_stock_data(["SPY"])
        spy_returns = extract_close_series(raw_spy, "SPY").pct_change().dropna()
        common_idx = returns_df.index.intersection(spy_returns.index)
        aligned_returns = returns_df.loc[common_idx]
        aligned_spy = pd.Series(spy_returns.loc[common_idx].astype(float).dropna(), name="SPY")
        if len(common_idx) < 10:
            st.warning(f"Only {len(common_idx)} overlapping days with SPY")
        spy_available = True
    except Exception as e:
        st.error(f"SPY fetch failed: {e}")

if not spy_available:
    st.stop()

aligned_tickers = [t for t in available if t in aligned_returns.columns]
if not aligned_tickers:
    st.error("No overlapping tickers")
    st.stop()

comparison_df = (
    aligned_returns[aligned_tickers]
    .join(aligned_spy.rename("SPY"), how="inner")
    .dropna()
)

if len(comparison_df) < 10:
    st.error("Insufficient complete overlapping history for comparison")
    st.stop()

w_final_raw = np.array(
    [float(final_weights.get(t, 0.0)) for t in aligned_tickers],
    dtype=float,
)
w_eq = np.full(len(aligned_tickers), 1.0 / len(aligned_tickers))

w_final = (
    w_final_raw / w_final_raw.sum()
    if w_final_raw.sum() > 0
    else w_eq
)

ret_matrix = comparison_df[aligned_tickers].to_numpy(dtype=float)
final_daily = pd.Series(
    ret_matrix @ w_final,
    index=comparison_df.index,
    name="Final Target",
)
eq_daily = pd.Series(
    ret_matrix @ w_eq,
    index=comparison_df.index,
    name="Equal-Weight",
)
aligned_spy = comparison_df["SPY"].astype(float)

cum_final = (1 + final_daily).cumprod()
cum_eq = (1 + eq_daily).cumprod()
cum_spy = (1 + aligned_spy).cumprod()

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

opt_total_return = (cum_final.iloc[-1] - 1) * 100
eq_total_return = (cum_eq.iloc[-1] - 1) * 100
spy_total_return = (cum_spy.iloc[-1] - 1) * 100

opt_ann_return = final_daily.mean() * TRADING_DAYS * 100
eq_ann_return = eq_daily.mean() * TRADING_DAYS * 100
spy_ann_return = aligned_spy.mean() * TRADING_DAYS * 100

opt_ann_vol = final_daily.std() * np.sqrt(TRADING_DAYS) * 100
eq_ann_vol = eq_daily.std() * np.sqrt(TRADING_DAYS) * 100
spy_ann_vol = aligned_spy.std() * np.sqrt(TRADING_DAYS) * 100

opt_sharpe = compute_sharpe(final_daily)
eq_sharpe = compute_sharpe(eq_daily)
spy_sharpe = compute_sharpe(aligned_spy)

opt_max_dd = max_drawdown_pct(cum_final)
eq_max_dd = max_drawdown_pct(cum_eq)
spy_max_dd = max_drawdown_pct(cum_spy)


# ── Performance Metrics Table ───────────────────────────────
section_header("Performance Metrics", "Side-by-side comparison", accent="primary")
glass_container(accent="primary")

metrics_data = {
    "Metric": ["Total Return", "Ann Return", "Ann Vol", "Sharpe", "Max DD"],
    "Final Target": [
        f"{opt_total_return:.2f}%",
        f"{opt_ann_return:.2f}%",
        f"{opt_ann_vol:.2f}%",
        f"{opt_sharpe:.3f}",
        f"{opt_max_dd:.2f}%",
    ],
    "Equal-Weight": [
        f"{eq_total_return:.2f}%",
        f"{eq_ann_return:.2f}%",
        f"{eq_ann_vol:.2f}%",
        f"{eq_sharpe:.3f}",
        f"{eq_max_dd:.2f}%",
    ],
    "SPY": [
        f"{spy_total_return:.2f}%",
        f"{spy_ann_return:.2f}%",
        f"{spy_ann_vol:.2f}%",
        f"{spy_sharpe:.3f}",
        f"{spy_max_dd:.2f}%"
    ]
}
st.dataframe(pd.DataFrame(metrics_data), hide_index=True, width='stretch')

st.caption(
    "In-sample historical illustration using the current final target weights. "
    "All portfolios use the same complete overlapping dates. Weights are held "
    "constant and transaction costs, taxes, slippage, and rebalancing are excluded."
)


st.markdown("</div>", unsafe_allow_html=True)

# ── KPI Summary ─────────────────────────────────────────────
section_header("KPI Summary", "Final target portfolio highlights", accent="green")
k1, k2, k3 = st.columns(3)
with k1:
    st.metric("Final Total Return", f"{(cum_final.iloc[-1]-1)*100:.2f}%",
              delta=f"{((cum_final.iloc[-1]-1) - (cum_spy.iloc[-1]-1))*100:.2f}% vs SPY")
with k2:
    st.metric("Final Sharpe", f"{compute_sharpe(final_daily):.3f}",
              delta=f"{compute_sharpe(final_daily) - compute_sharpe(aligned_spy):.3f} vs SPY")
final_max_dd = max_drawdown_pct(cum_final)
spy_max_dd = max_drawdown_pct(cum_spy)
drawdown_gap = abs(final_max_dd) - abs(spy_max_dd)

with k3:
    st.metric(
        "Final Max DD",
        f"{final_max_dd:.2f}%",
        delta=f"{drawdown_gap:+.2f} pp deeper than SPY",
        delta_color="inverse",
    )

# ── Cumulative Returns Chart ────────────────────────────────
section_header("Cumulative Returns vs Benchmark", "Growth trajectory", accent="cyan")
glass_container(accent="cyan")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=cum_final.index, y=(cum_final - 1) * 100,
    mode='lines', name="Final Target",
    line=dict(color="#FF6B35", width=2.5)
))
fig.add_trace(go.Scatter(
    x=cum_eq.index, y=(cum_eq - 1) * 100,
    mode='lines', name="Equal-Weight",
    line=dict(color="#8b8b9e", width=1.5, dash="dash")
))
fig.add_trace(go.Scatter(
    x=cum_spy.index, y=(cum_spy - 1) * 100,
    mode='lines', name="SPY",
    line=dict(color="#10B981", width=1.5, dash="dot")
))
fig.add_hline(y=0, line_color="rgba(255,255,255,0.1)", line_width=1)
fig.update_layout(
    title="Cumulative Return Comparison",
    xaxis_title="Date", yaxis_title="Cumulative Return (%)",
    height=480,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
fig = apply_plotly_theme(fig)
st.plotly_chart(fig, width='stretch')
st.markdown("</div>", unsafe_allow_html=True)

# ── Rolling Sharpe Chart ────────────────────────────────────
section_header("Rolling 60-Day Sharpe", "Risk-adjusted momentum", accent="violet")
glass_container(accent="violet")

MIN_DAYS = 65
if len(final_daily) < MIN_DAYS:
    info_card(
        "Insufficient Data",
        f"Need {MIN_DAYS} days of data for rolling Sharpe calculation. Current: {len(final_daily)} days.",
        badge("NEED MORE DATA", "warning"),
        accent="amber"
    )
else:
    def rolling_sharpe(series: pd.Series, window: int = 60, rf_daily: float = 0.05/252) -> pd.Series:
        roll_mean = series.rolling(window).mean()
        roll_std = series.rolling(window).std()
        return ((roll_mean - rf_daily) / roll_std * np.sqrt(252)).where(roll_std > 0)

    roll_opt = rolling_sharpe(final_daily)
    roll_eq = rolling_sharpe(eq_daily)
    roll_spy = rolling_sharpe(aligned_spy)

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=roll_opt.index, y=roll_opt, mode='lines',
        name="Final Target", line=dict(color="#FF6B35", width=2)
    ))
    fig2.add_trace(go.Scatter(
        x=roll_eq.index, y=roll_eq, mode='lines',
        name="Equal-Weight", line=dict(color="#8b8b9e", width=1.5, dash="dash")
    ))
    fig2.add_trace(go.Scatter(
        x=roll_spy.index, y=roll_spy, mode='lines',
        name="SPY", line=dict(color="#10B981", width=1.5, dash="dot")
    ))
    fig2.add_hline(y=0, line_color="rgba(255,255,255,0.1)", line_width=1)
    fig2.update_layout(
        title="Rolling Sharpe Ratio (60D)",
        xaxis_title="Date", yaxis_title="Rolling Sharpe",
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig2 = apply_plotly_theme(fig2)
    st.plotly_chart(fig2, width='stretch')

st.markdown("</div>", unsafe_allow_html=True)

# ── Drawdown Chart ──────────────────────────────────────────
section_header("Drawdown Comparison", "Peak-to-trough analysis", accent="red")
glass_container(accent="red")

def drawdown_series(cum: pd.Series) -> pd.Series:
    return ((cum - cum.cummax()) / cum.cummax()) * 100

dd_opt = drawdown_series(cum_final)
dd_eq = drawdown_series(cum_eq)
dd_spy = drawdown_series(cum_spy)

fig3 = go.Figure()
fig3.add_trace(go.Scatter(
    x=dd_opt.index, y=dd_opt, mode='lines',
    name="Final Target", line=dict(color="#FF6B35", width=1.5),
    fill='tozeroy', fillcolor="rgba(255,107,53,0.08)"
))
fig3.add_trace(go.Scatter(
    x=dd_eq.index, y=dd_eq, mode='lines',
    name="Equal-Weight", line=dict(color="#8b8b9e", width=1.2, dash="dash")
))
fig3.add_trace(go.Scatter(
    x=dd_spy.index, y=dd_spy, mode='lines',
    name="SPY", line=dict(color="#10B981", width=1.2, dash="dot")
))
fig3.add_hline(y=0, line_color="rgba(255,255,255,0.1)", line_width=1)
fig3.update_layout(
    title="Drawdown Comparison",
    xaxis_title="Date", yaxis_title="Drawdown (%)",
    height=400,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
fig3 = apply_plotly_theme(fig3)
st.plotly_chart(fig3, width='stretch')
st.markdown("</div>", unsafe_allow_html=True)

# ── Allocation Comparison ───────────────────────────────────
section_header("Weight Allocation Comparison", "Final Target vs Equal-Weight", accent="amber")
display_names = {t: t for t in aligned_tickers}
c1, c2 = st.columns(2)
with c1:
    glass_container(accent="primary")
    alloc_opt = {"Ticker": [display_names.get(t, t) for t in aligned_tickers],
                 "Weight": [final_weights.get(t, 0) * 100 for t in aligned_tickers]}
    fig_p1 = go.Figure(go.Pie(
        labels=alloc_opt["Ticker"], values=alloc_opt["Weight"], hole=0.55,
        marker_colors=["#FF6B35", "#00D9FF", "#8B5CF6", "#10B981", "#F43F5E", "#F59E0B", "#EC4899", "#6366F1"]
    ))
    fig_p1.update_layout(title="Final Target Weights", showlegend=True, height=320)
    fig_p1 = apply_plotly_theme(fig_p1)
    st.plotly_chart(fig_p1, width='stretch')
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    glass_container(accent="cyan")
    alloc_eq = {"Ticker": [display_names.get(t, t) for t in aligned_tickers],
                "Weight": [100/len(aligned_tickers)] * len(aligned_tickers)}
    fig_p2 = go.Figure(go.Pie(
        labels=alloc_eq["Ticker"], values=alloc_eq["Weight"], hole=0.55,
        marker_colors=["#8b8b9e", "#4a4a5e", "#6e6e8a", "#a0a0b8", "#555555", "#777777", "#999999", "#bbbbbb"]
    ))
    fig_p2.update_layout(title="Equal Weights", showlegend=True, height=320)
    fig_p2 = apply_plotly_theme(fig_p2)
    st.plotly_chart(fig_p2, width='stretch')
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
<div style="border-top:1px solid rgba(255,255,255,0.06);margin-top:32px;padding-top:20px;">
    <div style="font-size:0.65rem;color:#4a4a5e;text-align:center;letter-spacing:0.05em;">
        Past performance does not guarantee future results | AXIOM Portfolio Intelligence · Terminal Edition
    </div>
</div>
""", unsafe_allow_html=True)