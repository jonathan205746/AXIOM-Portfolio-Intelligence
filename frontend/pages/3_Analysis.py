"""
frontend/pages/3_Analysis.py  (Bloomberg Terminal Edition)
-----------------------------------------------------------
Plotly charts, AI Score, risk gauges, exports.
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
from typing import Any, cast
from src.database.db import get_portfolio_holdings, save_optimization_run
from pages.report_generator import generate_bloomberg_report

st.set_page_config(page_title="ANALYSIS | AI Portfolio Optimizer", page_icon="🤖", layout="wide")

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
.bb-panel-green { border-top: 2px solid var(--positive); }
.bb-panel-red { border-top: 2px solid var(--negative); }
.bb-metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 1px; background: var(--border); border: 1px solid var(--border); }
.bb-metric-cell { background: var(--bg-panel); padding: 10px; text-align: center; }
.bb-metric-value { font-size: 1.2rem; font-weight: 700; color: var(--text); line-height: 1; }
.bb-metric-value.pos { color: var(--positive); }
.bb-metric-value.neg { color: var(--negative); }
.bb-metric-value.accent { color: var(--accent); }
.bb-metric-label { font-size: 0.6rem; color: var(--text-faded); text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }
.stButton > button { background: var(--accent) !important; color: var(--text-inverse) !important; border: none !important; border-radius: var(--radius-sm) !important; font-family: var(--font) !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; font-size: 0.75rem !important; }
.stButton > button:hover { background: var(--accent-dim) !important; box-shadow: 0 0 12px var(--accent-glow) !important; }
.stSlider > div > div > div { color: var(--accent) !important; }
.stSelectbox > div > div, .stNumberInput > div > div { background: var(--bg-input) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; color: var(--text) !important; }
.stNumberInput > div > div > input { color: var(--text) !important; font-family: var(--font) !important; }
[data-testid="stMetric"] { background: var(--bg-panel) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; }
[data-testid="stMetricValue"] { font-family: var(--font) !important; font-weight: 700 !important; color: var(--text) !important; }
[data-testid="stMetricLabel"] { font-family: var(--font) !important; color: var(--text-dim) !important; text-transform: uppercase !important; font-size: 0.6rem !important; letter-spacing: 1px !important; }
[data-testid="stTabs"] [data-baseweb="tab-list"] { gap: 0 !important; border-bottom: 1px solid var(--border) !important; background: var(--bg-panel) !important; }
[data-testid="stTabs"] [data-baseweb="tab"] { border-radius: 0 !important; padding: 10px 16px !important; font-weight: 600 !important; font-size: 0.75rem !important; color: var(--text-dim) !important; border: none !important; text-transform: uppercase; letter-spacing: 0.5px; }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background: var(--accent) !important; height: 2px !important; }
[data-testid="stTabs"] [aria-selected="true"] { color: var(--accent) !important; background: var(--accent-soft) !important; }
.positive { color: var(--positive) !important; font-weight: 700; }
.negative { color: var(--negative) !important; font-weight: 700; }
.neutral { color: var(--text-dim) !important; font-weight: 600; }
.loading-pulse { display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: var(--accent); animation: pulse 1s infinite; margin-right: 8px; }
@keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(1.3); } 100% { opacity: 1; transform: scale(1); } }
@media (max-width: 768px) { .block-container { padding: 0.5rem !important; } }
</style>
""", unsafe_allow_html=True)

# ── ACTION HELPER (must be at module level) ──────────────
def _get_action(ticker: str, final_weights: dict, weight_changes: dict) -> str:
    final = final_weights.get(ticker, 0)
    if final < 0.001:
        return "EXCLUDE"
    change = weight_changes.get(ticker, {}).get("change", 0)
    if change > 0.001:
        return "BUY"
    if change < -0.001:
        return "SELL"
    return "HOLD"

@st.cache_data(ttl=300)
def _market_snapshot():
    fallback = {"SPX": {"price": 4500.0, "change": 0.45}, "NIFTY": {"price": 22500.0, "change": -0.12}, "NDX": {"price": 14000.0, "change": 0.78}, "BTC": {"price": 67500.0, "change": 1.23}}
    out = {}
    try:
        import yfinance as yf
        for t, n in [("^GSPC", "SPX"), ("^NSEI", "NIFTY"), ("^IXIC", "NDX"), ("BTC-USD", "BTC")]:
            try:
                h = yf.Ticker(t).history(period="2d")
                if len(h) >= 2:
                    c, p = h["Close"].iloc[-1], h["Close"].iloc[-2]
                    out[n] = {"price": c, "change": (c - p) / p * 100}
                else:
                    out[n] = fallback[n]
            except Exception:
                out[n] = fallback[n]
    except Exception:
        return fallback
    return out
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
    _render_nav("pages/3_Analysis.py")
    st.markdown('</div>', unsafe_allow_html=True)
    if st.button("◀ LOGOUT", width='stretch'):
        for k in ["logged_in", "user", "current_portfolio", "results"]:
            st.session_state.pop(k, None)
        st.switch_page("app.py")
    st.markdown('<div class="bb-sidebar-footer">TERMINAL EDITION v5.0</div>', unsafe_allow_html=True)

st.markdown(f'<div class="bb-cmd-bar"><span class="bb-cmd-prompt">➜</span><span style="color:var(--text-dim);">AI ANALYSIS // PORTFOLIO: {portfolio["name"].upper()}</span></div>', unsafe_allow_html=True)
st.markdown('<div style="padding:12px 0;"><span style="font-size:1.4rem;font-weight:800;color:var(--text);letter-spacing:-1px;">▣ QUANTITATIVE ANALYSIS</span><br><span style="font-size:0.8rem;color:var(--text-dim);">BLEND QUANTITATIVE SIGNALS WITH MARKET SENTIMENT AND AI REASONING</span></div>', unsafe_allow_html=True)

holdings = get_portfolio_holdings(portfolio["id"])
if len(holdings) < 2:
    st.error("MINIMUM 2 HOLDINGS REQUIRED FOR OPTIMIZATION")
    st.page_link("pages/2_Portfolio.py", label="◫ ADD HOLDINGS")
    st.stop()

tickers = [h["ticker"] for h in holdings]
display_names = {h["ticker"]: h["display_name"] for h in holdings}
st.info(f"SELECTED: {', '.join([h['display_name'] for h in holdings])}")

st.markdown('<div class="bb-panel bb-panel-accent"><div class="bb-panel-header"><span class="bb-panel-title">◈ Strategy Settings</span></div><div class="bb-panel-body">', unsafe_allow_html=True)
s1, s2 = st.columns(2)
with s1:
    alpha = st.slider("QUANT/SENTIMENT BALANCE", 0.0, 1.0, 0.6, 0.05, help="1.0 = RISK/RETURN FIRST | 0.0 = SENTIMENT FIRST")
    st.caption(f"QUANT: {int(alpha*100)}% • SENTIMENT: {int((1-alpha)*100)}%")
with s2:
    portfolio_value = st.number_input("PORTFOLIO VALUE (USD)", min_value=1000, max_value=10_000_000, value=100_000, step=10_000)
    use_llm = st.checkbox("ENABLE LLM RECOMMENDATIONS", value=True)
run_button = st.button("▶ RUN OPTIMIZATION", type="primary", width='stretch')
st.markdown('</div></div>', unsafe_allow_html=True)

def run_pipeline(tickers, alpha, portfolio_value, use_llm):
    
    try:
        from src.data.stock_fetcher import fetch_stock_data
        from src.data.news_fetcher import fetch_news
        from src.models.sentiment import aggregate_sentiment
        from src.optimization.portfolio import PortfolioOptimizer
        from src.optimization.risk import RiskAnalyzer
        from src.optimization.combined_signal import CombinedSignal
        from src.models.rag_pipeline import RAGPipeline
    except Exception as exc:
        st.error(f"IMPORT ERROR: {exc}")
        return None

    results = {}
    status = st.empty()
    def _set(msg, pct):
        status.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;padding:8px;background:var(--bg-panel);border:1px solid var(--border);"><span class="loading-pulse"></span><span style="font-size:0.8rem;color:var(--text-dim)">{msg}</span><span style="margin-left:auto;font-size:0.7rem;color:var(--accent);font-weight:700;">{pct}%</span></div>', unsafe_allow_html=True)

    _set("FETCHING PRICE DATA...", 10)
    try:
        prices = fetch_stock_data(tickers, period="1y")
        if isinstance(prices.columns, pd.MultiIndex):
            if "Close" in prices.columns.get_level_values(0):
                prices = prices["Close"]
            elif len(tickers) == 1 and len(prices.columns) == 1:
                prices = prices.iloc[:, 0].to_frame(name=tickers[0])
        if isinstance(prices, pd.Series):
            prices = prices.to_frame()
        if isinstance(prices.columns, pd.MultiIndex):
            prices.columns = [col[-1] if isinstance(col, tuple) else col for col in prices.columns]
        available = [t for t in tickers if t in prices.columns]
        if not available:
            raise ValueError("NO VALID TICKERS")
        prices = prices[available]
        if isinstance(prices, pd.Series):
            prices = prices.to_frame()
        results["prices"] = prices
        results["returns"] = prices.pct_change(fill_method=None).dropna()
    except Exception as exc:
        st.error(f"PRICE FETCH FAILED: {exc}")
        return None

    _set("OPTIMIZING PORTFOLIO...", 25)
    try:
        optimizer = PortfolioOptimizer(prices)
        opt_result = optimizer.optimize()
        baseline = optimizer.equal_weight_baseline()
        frontier_df = optimizer.efficient_frontier(n_points=800)
        results.update({"opt_result": opt_result, "baseline": baseline, "frontier_df": frontier_df})
    except Exception as exc:
        st.error(f"OPTIMIZATION FAILED: {exc}")
        return None

    _set("FETCHING NEWS...", 40)
    all_news = {}
    for ticker in available:
        try:
            articles = fetch_news(ticker, company_name=None)
            if not articles:
                company = display_names.get(ticker, ticker).replace(".NS", "")
                articles = fetch_news(ticker, company_name=company)
            all_news[ticker] = articles
        except Exception:
            all_news[ticker] = []

    results["all_news"] = all_news

    _set("RUNNING FINBERT...", 55)
    sentiment_scores = {}
    for ticker in available:
        try:
            headlines = [a.get("title", "") for a in all_news.get(ticker, []) if a.get("title")]
            sentiment_scores[ticker] = aggregate_sentiment(headlines) if headlines else 0.0
        except Exception:
            sentiment_scores[ticker] = 0.0
    results["sentiment_scores"] = sentiment_scores

    _set("COMBINING SIGNALS...", 70)
    try:
        combiner = CombinedSignal(opt_result, sentiment_scores)
        combined = combiner.combine(alpha=alpha, max_weight=0.40)
        results["combined"] = combined
        results["final_weights"] = combined["final_weights"]

        # Recompute return/volatility/Sharpe from the FINAL blended weights,
        # not the pre-sentiment optimizer output. opt_result never changes
        # with alpha — this does.
        final_weights_arr = np.array(
            [combined["final_weights"].get(t, 0.0) for t in optimizer.tickers]
        )
        results["final_stats"] = {
            "expected_return": optimizer.portfolio_return(final_weights_arr),
            "volatility": optimizer.portfolio_volatility(final_weights_arr),
            "sharpe_ratio": optimizer.sharpe_ratio(final_weights_arr),
        }
    except Exception as exc:
        st.error(f"SIGNAL COMBINATION FAILED: {exc}")
        return None

    _set("COMPUTING RISK...", 82)
    try:
        risk_analyzer = RiskAnalyzer(prices)
        risk_report = risk_analyzer.full_risk_report(combined["final_weights"], portfolio_value)
        results["risk_report"] = risk_report
        results["tickers"] = available
    except Exception as exc:
        st.error(f"RISK ANALYSIS FAILED: {exc}")
        return None

    _set("GENERATING LLM...", 92)
    recommendations = []
    if use_llm:
        try:
            rag = RAGPipeline()
        except Exception:
            rag = None
        if rag is not None:
            for ticker in available:
                try:
                    articles_text = [a.get("title", "") for a in all_news.get(ticker, []) if a.get("title")]
                    rec = rag.generate_recommendation(ticker=ticker, sentiment_score=sentiment_scores.get(ticker, 0.0), portfolio_weight=combined["final_weights"].get(ticker, 0.0), retrieved_articles=articles_text)
                    recommendations.append(rec)
                except Exception:
                    pass
    results["recommendations"] = recommendations
    _set("COMPLETE", 100)
    status.empty()
    return results

if run_button:
    with st.spinner(""):
        try:
            results = run_pipeline(tickers, alpha, portfolio_value, use_llm)
            if not results:
                st.stop()

            # Overwrite opt_result's top-level stats with the post-sentiment
            # numbers BEFORE storing to session_state, so Overview/History/
            # every chart on this page all agree on the same Sharpe/Return/Vol.
            results["opt_result"]["sharpe_ratio"] = results["final_stats"]["sharpe_ratio"]
            results["opt_result"]["expected_return"] = results["final_stats"]["expected_return"]
            results["opt_result"]["volatility"] = results["final_stats"]["volatility"]

            st.session_state["results"] = results
            safe_opt = {}
            for key, value in results["opt_result"].items():
                safe_opt[key] = value.tolist() if isinstance(value, np.ndarray) else value
            safe_opt["baseline_sharpe"] = results["baseline"]["sharpe_ratio"]
            save_optimization_run(portfolio_id=portfolio["id"], alpha=alpha, opt_result=safe_opt,sentiment_scores=results["sentiment_scores"],recommendations=results["recommendations"],risk_report=results["risk_report"])
            st.success("ANALYSIS COMPLETE — SAVED TO HISTORY")
        except Exception as e:
            st.error(f"PIPELINE ERROR: {e}")
            st.stop()

results = st.session_state.get("results")
if not results:
    st.info("CONFIGURE SETTINGS AND CLICK RUN OPTIMIZATION")
    st.stop()

available = results["tickers"]
opt_result = results["opt_result"]
baseline = results["baseline"]
final_weights = results["final_weights"]
sentiment_scores = results["sentiment_scores"]
risk_report = results["risk_report"]
recommendations = results.get("recommendations", [])
combined = results["combined"]
frontier_df = results["frontier_df"]
prices = results["prices"]
returns_df = results["returns"]

sharpe = opt_result.get("sharpe_ratio", 0)
var95_val = abs(risk_report.get("value_at_risk", {}).get("historical_95", {}).get("var_pct", 0))
vol = risk_report.get("volatility", {}).get("portfolio_annualized", 0)
avg_sent = sum(sentiment_scores.values()) / len(sentiment_scores) if sentiment_scores else 0
div = sum(1 for w in final_weights.values() if w > 0.01) / len(final_weights) if final_weights else 0
ss = min(max(sharpe * 25, 0), 100)
vs = max(0, 100 - var95_val * 1000)
vos = max(0, 100 - vol * 100)
sns = (avg_sent + 1) * 50
ds = div * 100
ai_score = min(100, max(0, ss * 0.35 + vs * 0.2 + vos * 0.2 + sns * 0.15 + ds * 0.1))
score_label = "EXCELLENT" if ai_score >= 80 else "GOOD" if ai_score >= 60 else "FAIR" if ai_score >= 40 else "POOR"

st.markdown('<div class="bb-panel bb-panel-accent"><div class="bb-panel-header"><span class="bb-panel-title">◈ Key Performance Indicators</span></div><div class="bb-panel-body">', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f'<div style="text-align:center"><div style="font-size:2rem;font-weight:800;color:var(--accent);line-height:1">{ai_score:.0f}</div><div style="font-size:0.6rem;color:var(--text-faded);text-transform:uppercase;letter-spacing:1px;margin-top:4px">AI Score</div><div style="font-size:0.7rem;color:var(--text-dim);margin-top:2px">{score_label}</div></div>', unsafe_allow_html=True)
with c2:
    delta = opt_result["sharpe_ratio"] - baseline["sharpe_ratio"]
    st.metric("SHARPE", f"{opt_result['sharpe_ratio']:.3f}", delta=f"{delta:+.3f}")
with c3:
    st.metric("EXP RETURN", f"{opt_result['expected_return']*100:.1f}%")
with c4:
    st.metric("VOLATILITY", f"{risk_report['volatility']['portfolio_annualized']*100:.1f}%")
var95 = risk_report["value_at_risk"]["historical_95"]
with c5:
    st.metric("95% VaR", f"${var95['var_usd']:,.0f}", delta=f"{var95['var_pct']*100:.2f}%", delta_color="inverse")
st.markdown('</div></div>', unsafe_allow_html=True)

weights_csv = pd.DataFrame([{"Ticker": display_names.get(t, t),"Weight": f"{final_weights[t] * 100:.2f}%","Action": _get_action(t, final_weights, combined["weight_changes"])} for t in available]).to_csv(index=False).encode("utf-8")
risk_csv = pd.DataFrame([{"Metric": "Volatility", "Value": f"{risk_report['volatility']['portfolio_annualized']*100:.2f}%"}, {"Metric": "95% VaR", "Value": f"${var95['var_usd']:,.0f}"}, {"Metric": "99% VaR", "Value": f"${risk_report['value_at_risk']['historical_99']['var_usd']:,.0f}"}]).to_csv(index=False).encode("utf-8")
col_e1, col_e2, col_e3, col_e4 = st.columns(4)
with col_e1:
    st.download_button("◉ WEIGHTS CSV", weights_csv, "optimized_weights.csv", "text/csv", width='stretch')
with col_e2:
    st.download_button("◉ RISK CSV", risk_csv, "risk_metrics.csv", "text/csv", width='stretch')
with col_e3:
    if st.button("◉ SHARE", width='stretch'):
        st.code(f"PORTFOLIO: {portfolio['name']} | SHARPE: {opt_result['sharpe_ratio']:.2f} | AI: {ai_score:.0f}/100", language=None)
with col_e4:
    try:
        report_html = generate_bloomberg_report(portfolio, results, display_names)
        st.download_button(
            "◉ FULL REPORT",
            report_html.encode("utf-8"),
            f"AI_PORTFOLIO_REPORT_{portfolio['name'].upper().replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.html",
            "text/html",
             
            type="primary"
        )
    except Exception as e:
        st.error(f"REPORT GEN ERROR: {e}")

st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["◈ OVERVIEW", "⚖ OPTIMIZATION", "◉ SENTIMENT", "◫ RISK", "◉ AI", "◫ PERFORMANCE"])

PLOTLY_THEME: dict[str, Any] = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="JetBrains Mono, monospace", color="#e5e5e5", size=11),
    margin=dict(l=10, r=10, t=40, b=10),
    xaxis=dict(gridcolor="#2a2a2a", linecolor="#3a3a3a"),
    yaxis=dict(gridcolor="#2a2a2a", linecolor="#3a3a3a"),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#2a2a2a", borderwidth=1)
)

with tab1:
    st.caption("HIGH-LEVEL PORTFOLIO SNAPSHOT")
    c1, c2 = st.columns(2)
    disp = [display_names.get(t, t) for t in available]
    with c1:
        fig = go.Figure(go.Bar(y=disp, x=[final_weights[t]*100 for t in available], orientation='h', marker_color='#ff6600', text=[f"{final_weights[t]*100:.1f}%" for t in available], textposition='outside'))
        fig.update_layout(**PLOTLY_THEME)
        fig.update_layout(title="FINAL WEIGHTS", xaxis_title="WEIGHT (%)", yaxis=dict(autorange="reversed"), height=350)
        st.plotly_chart(fig, width='stretch')
    with c2:
        fig2 = go.Figure(go.Bar(y=disp, x=[100/len(available)]*len(available), orientation='h', marker_color='#555555', text=[f"{100/len(available):.1f}%"]*len(available), textposition='outside'))
        fig2.update_layout(**PLOTLY_THEME)
        fig2.update_layout(title=f"EQUAL WEIGHT (SHARPE={baseline['sharpe_ratio']:.3f})", xaxis_title="WEIGHT (%)", yaxis=dict(autorange="reversed"), height=350)
        st.plotly_chart(fig2, width='stretch')
    df_weights = pd.DataFrame([{"Ticker": display_names.get(t, t),"Optimized": f"{opt_result['weights'][t]*100:.1f}%","Final": f"{final_weights[t]*100:.1f}%","Change": f"{combined['weight_changes'][t]['change']*100:+.1f}%","Action": _get_action(t, final_weights, combined["weight_changes"])} for t in available])
    st.dataframe(df_weights,   hide_index=True)

with tab2:
    st.caption("EFFICIENT FRONTIER AND OPTIMAL VS BASELINE")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=frontier_df["volatility"]*100, y=frontier_df["return"]*100, mode='markers', marker=dict(color=frontier_df["sharpe"], colorscale=[[0,'#ff3333'],[0.5,'#ff6600'],[1,'#00d084']], size=5, opacity=0.6), name="FRONTIER"))
    fig.add_trace(go.Scatter(x=[opt_result["volatility"]*100], y=[opt_result["expected_return"]*100], text=[f"FINAL PORTFOLIO (SHARPE={opt_result['sharpe_ratio']:.3f})"], textposition="top center", name="OPTIMAL"))
    fig.add_trace(go.Scatter(x=[baseline["volatility"]*100], y=[baseline["expected_return"]*100], mode='markers+text', marker=dict(color='#888888', size=10, symbol='diamond'), text=[f"BASELINE (SHARPE={baseline['sharpe_ratio']:.3f})"], textposition="bottom center", name="BASELINE"))
    fig.update_layout(title="EFFICIENT FRONTIER", xaxis_title="VOLATILITY (%)", yaxis_title="RETURN (%)", height=500, **PLOTLY_THEME)
    st.plotly_chart(fig, width='stretch')

with tab3:
    st.caption("FINBERT SENTIMENT SCORES")
    for t in available:
        score = sentiment_scores[t]
        label = "POSITIVE" if score >= 0.3 else ("NEGATIVE" if score <= -0.3 else "NEUTRAL")
        emoji = "▲" if score >= 0.3 else ("▼" if score <= -0.3 else "—")
        pct = int((score + 1) / 2 * 100)
        ca, cb, cc = st.columns([1.5, 4, 1.5])
        ca.markdown(f"**{emoji} {display_names.get(t, t)}**")
        cb.progress(pct)
        css = "positive" if score >= 0.3 else ("negative" if score <= -0.3 else "neutral")
        cc.markdown(f'<span class="{css}">{score:+.3f} ({label})</span>', unsafe_allow_html=True)
    all_news = results.get("all_news", {})
    st.markdown("---")
    st.markdown("#### RECENT HEADLINES")
    for t in available:
        articles = all_news.get(t, [])
        with st.expander(f"{display_names.get(t, t)} — {len(articles)} ARTICLES"):
            for a in articles[:6]:
                st.markdown(f"• {a.get('title', '')}")

with tab4:
    st.caption("RISK METRICS, CORRELATION, VOLATILITY")
    var99 = risk_report["value_at_risk"]["historical_99"]
    mdd = risk_report["drawdown"]["portfolio"]
    conc = risk_report["concentration"]
    r1, r2, r3 = st.columns(3)
    r1.metric("95% VaR (1-Day)", f"${var95['var_usd']:,.0f}", delta=f"{var95['var_pct']*100:.2f}%", delta_color="inverse")
    r2.metric("99% VaR (1-Day)", f"${var99['var_usd']:,.0f}", delta=f"{var99['var_pct']*100:.2f}%", delta_color="inverse")
    r3.metric("MAX DRAWDOWN", f"{mdd['max_drawdown_pct']:.2f}%", delta=conc["label"], delta_color="off")
    c1, c2 = st.columns(2)
    with c1:
        corr = returns_df.corr()
        corr.columns = [display_names.get(t, t) for t in corr.columns]
        corr.index = corr.columns
        fig_c = px.imshow(corr, color_continuous_scale=[[0,'#ff3333'],[0.5,'#111111'],[1,'#00d084']], aspect="auto")
        fig_c.update_traces(texttemplate="%{z:.2f}")
        fig_c.update_layout(title="CORRELATION MATRIX", height=400, **PLOTLY_THEME)
        st.plotly_chart(fig_c, width='stretch')
    with c2:
        vols = risk_report["volatility"]["per_ticker_annualized"]
        vol_df = pd.DataFrame({"Ticker": [display_names.get(t, t) for t in vols.keys()], "Volatility": [v*100 for v in vols.values()]})
        fig_v = px.bar(vol_df, x="Volatility", y="Ticker", orientation='h', color="Volatility", color_continuous_scale=[[0,'#00d084'],[0.5,'#ff6600'],[1,'#ff3333']])
        fig_v.add_vline(x=vol*100, line_dash="dash", line_color="#ff6600", annotation_text=f"PORTFOLIO: {vol*100:.1f}%")
        fig_v.update_layout(**PLOTLY_THEME)
        fig_v.update_layout(yaxis=dict(autorange="reversed"), height=400)
        st.plotly_chart(fig_v, width='stretch')
    st.markdown("#### RISK GAUGES")
    g1, g2, g3 = st.columns(3)
    with g1:
        fig_g1 = go.Figure(go.Indicator(mode="gauge+number", value=var95["var_pct"]*100, title={"text": "95% VaR (%)", "font": {"color": "#e5e5e5", "size": 12}}, gauge={"axis": {"range": [0, 5], "tickcolor": "#888"}, "bar": {"color": "#ff3333"}, "bgcolor": "#0a0a0a", "bordercolor": "#2a2a2a", "steps": [{"range": [0, 2], "color": "#0a0a0a"}, {"range": [2, 4], "color": "#111"}, {"range": [4, 5], "color": "#1a1a1a"}], "threshold": {"line": {"color": "#ff6600", "width": 2}, "thickness": 0.8, "value": 2.5}}))
        fig_g1.update_layout(height=220, **PLOTLY_THEME)
        st.plotly_chart(fig_g1, width='stretch')
    with g2:
        fig_g2 = go.Figure(go.Indicator(mode="gauge+number", value=abs(mdd["max_drawdown_pct"]), title={"text": "MAX DRAWDOWN (%)", "font": {"color": "#e5e5e5", "size": 12}}, gauge={"axis": {"range": [0, 50], "tickcolor": "#888"}, "bar": {"color": "#ff6600"}, "bgcolor": "#0a0a0a", "bordercolor": "#2a2a2a", "steps": [{"range": [0, 10], "color": "#0a0a0a"}, {"range": [10, 25], "color": "#111"}, {"range": [25, 50], "color": "#1a1a1a"}]}))
        fig_g2.update_layout(height=220, **PLOTLY_THEME)
        st.plotly_chart(fig_g2, width='stretch')
    with g3:
        fig_g3 = go.Figure(go.Indicator(mode="gauge+number", value=sharpe, title={"text": "SHARPE RATIO", "font": {"color": "#e5e5e5", "size": 12}}, gauge={"axis": {"range": [0, 4], "tickcolor": "#888"}, "bar": {"color": "#00d084"}, "bgcolor": "#0a0a0a", "bordercolor": "#2a2a2a", "steps": [{"range": [0, 1], "color": "#1a1a1a"}, {"range": [1, 2], "color": "#111"}, {"range": [2, 4], "color": "#0a0a0a"}]}))
        fig_g3.update_layout(height=220, **PLOTLY_THEME)
        st.plotly_chart(fig_g3, width='stretch')

with tab5:
    st.caption("AI-GENERATED GUIDANCE FROM GROQ LLAMA 3.3 70B")
    if not recommendations:
        st.warning("ENABLE LLM IN SETTINGS AND RE-RUN")
    else:
        for rec in recommendations:
            t = rec.get("ticker", "")
            score = rec.get("sentiment_score", 0)
            emoji = "▲" if score >= 0.3 else ("▼" if score <= -0.3 else "—")
            label = rec.get("sentiment_label", "NEUTRAL")
            weight_pct = rec.get("portfolio_weight_pct", "0")
            st.markdown(f"**{emoji} {display_names.get(t, t)}** — SENTIMENT: {score:+.3f} ({label}) | WEIGHT: {weight_pct}%")
            st.markdown(rec.get("recommendation", ""))
            st.markdown("---")

with tab6:
    st.caption("CUMULATIVE RETURNS AND ROLLING SHARPE")
    cum_returns = (1 + returns_df).cumprod()
    fig = go.Figure()
    colors = ["#ff6600", "#00d084", "#2e75b6", "#ff3333", "#f59e0b", "#8b5cf6"]
    for i, t in enumerate(available):
        fig.add_trace(go.Scatter(x=cum_returns.index, y=cum_returns[t], mode="lines", name=display_names.get(t, t), line=dict(color=colors[i % len(colors)], width=1.5)))
    fig.update_layout(title="CUMULATIVE RETURNS BY TICKER", xaxis_title="DATE", yaxis_title="GROWTH", height=450, **PLOTLY_THEME)
    st.plotly_chart(fig, width='stretch')

st.markdown("---")
st.caption("AI PORTFOLIO OPTIMIZER | Terminal Edition")
