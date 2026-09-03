"""
Axiom Quantitative Analysis v2.1
AI-driven portfolio optimization with glassmorphic terminal aesthetic.
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import math
from typing import Any, cast
from src.data.market_data import get_fx_rate as fetch_fx_rate
from src.database.db import (
    get_portfolio_holdings,
    save_optimization_run,
)
from pages.report_generator import generate_axiom_report
from src.data.market_data import (
    get_fx_rate as fetch_fx_rate,
)
from src.optimization.health_score import HealthScoreEngine
from src.optimization.adaptive_optimizer import AdaptiveHealthOptimizer
from src.utils.sentiment import (
    SentimentLabel,
    classify_sentiment,
)

from src.optimization.rebalancing import (
    build_rebalance_plan,
    calculate_current_allocation,
    classify_model_adjustment,
)


st.set_page_config(page_title="Analysis | Axiom", page_icon="▣", layout="wide")

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


base_currency = str(
    portfolio.get("currency") or "USD"
).upper()

# ── Design System ───────────────────────────────────────────
from frontend.ui.theme import inject_theme, apply_plotly_theme
from frontend.ui.components import (
    page_sidebar, command_bar, section_header, metric_grid,
    glass_container, info_card, badge, loading_skeleton
)
inject_theme()

SENTIMENT_VISUALS = {
    SentimentLabel.POSITIVE: {
        "label": "Positive",
        "symbol": "▲",
        "css": "positive",
        "accent": "cyan",
    },
    SentimentLabel.NEGATIVE: {
        "label": "Negative",
        "symbol": "▼",
        "css": "negative",
        "accent": "red",
    },
    SentimentLabel.NEUTRAL: {
        "label": "Neutral",
        "symbol": "—",
        "css": "neutral",
        "accent": "primary",
    },
    SentimentLabel.INSUFFICIENT_EVIDENCE: {
        "label": "Insufficient Evidence",
        "symbol": "?",
        "css": "neutral",
        "accent": "amber",
    },
}


def get_sentiment_visual(score: float | None) -> dict[str, str]:
    sentiment = classify_sentiment(score)
    return SENTIMENT_VISUALS[sentiment]


def format_sentiment_score(score: float | None) -> str:
    if score is None:
        return "N/A"

    return f"{score:+.3f}"


def sentiment_progress_value(score: float | None) -> int:
    if score is None:
        return 50

    progress_value = int((score + 1.0) / 2.0 * 100)
    return max(0, min(100, progress_value))

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


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_fx_rate(
    source_currency: str,
    target_currency: str,
) -> float:
    """Return a cached latest FX conversion rate."""
    return fetch_fx_rate(
        source_currency,
        target_currency,
    )


# ── Sidebar & Command Bar ───────────────────────────────────
page_sidebar("pages/3_Analysis.py", user=user, market_data=market_data)
command_bar("AXIOM / ANALYSIS", f"PORTFOLIO: {portfolio['name'].upper()}")

# ── Header ──────────────────────────────────────────────────
st.markdown("""
<div style="padding: 20px 0 12px;">
    <div style="font-size:1.6rem;font-weight:800;color:#f0f0f5;letter-spacing:-0.03em;font-family:'Inter',sans-serif;">
        Quantitative Analysis
    </div>
    <div style="font-size:0.85rem;color:#8b8b9e;margin-top:6px;">
        Blend quantitative signals with market sentiment and AI reasoning
    </div>
</div>
""", unsafe_allow_html=True)



def _safe_float(value: Any, digits: int | None = None) -> float | None:
    if value is None or pd.isna(value):
        return None
    result = float(value)
    if digits is not None:
        result = round(result, digits)
    return result


def _safe_pct(value: Any, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(value) * 100:.{digits}f}%"


# ── Holdings Check ──────────────────────────────────────────
holdings = get_portfolio_holdings(portfolio["id"])
if len(holdings) < 2:
    info_card(
        "Insufficient Holdings",
        "Add at least 2 positions to run portfolio optimization and risk analysis.",
        badge("MIN 2 TICKERS", "warning"),
        accent="amber"
    )
    if st.button("◫ Add Holdings →", type="primary", use_container_width=True):
        st.switch_page("pages/2_Portfolio.py")
    st.stop()

tickers = [h["ticker"] for h in holdings]
display_names = {h["ticker"]: h["display_name"] for h in holdings}

st.markdown(f'''
<div style="
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 16px;
    font-size: 0.78rem;
    color: #8b8b9e;
    font-family: 'JetBrains Mono', monospace;
">
    <span style="color:#4a4a5e;">SELECTED:</span> {', '.join([h['display_name'] for h in holdings])}
</div>
''', unsafe_allow_html=True)

# ── Strategy Settings ───────────────────────────────────────
section_header("Strategy Configuration", "Optimization parameters", accent="primary")
glass_container(accent="primary")

s1, s2 = st.columns(2)
with s1:
    alpha = st.slider("Quant / Sentiment Balance", 0.0, 1.0, 0.6, 0.05,
                      help="1.0 = Risk/Return first | 0.0 = Sentiment first")
    st.caption(f"Quant: {int(alpha*100)}% • Sentiment: {int((1-alpha)*100)}%")
with s2:
    portfolio_value = st.number_input(
        f"Risk Scenario Value ({base_currency})", min_value=1000, max_value=10_000_000, value=100_000, step=10_000)
    use_llm = st.checkbox("Enable AI Research Commentary", value=True)

run_button = st.button("▶ Run Optimization", type="primary", use_container_width=True)

# ── Pipeline ────────────────────────────────────────────────
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
        st.error(f"Import error: {exc}")
        return None

    results = {}
    # A placeholder replaces the prior progress stage instead of appending it.
    status_placeholder = st.empty()

    def _set(msg, pct, stage=""):
        with status_placeholder.container():
            st.markdown(f'''
            <div style="
                display:flex;align-items:center;gap:10px;margin-bottom:10px;padding:10px 14px;
                background:rgba(18,18,26,0.9);border:1px solid rgba(255,255,255,0.06);border-radius:10px;
                backdrop-filter:blur(20px);
            ">
                <span style="display:inline-block;width:8px;height:8px;background:#FF6B35;border-radius:50%;box-shadow:0 0 8px rgba(255,107,53,0.5);animation:pulse 1.5s infinite;"></span>
                <span style="font-size:0.8rem;color:#8b8b9e;font-family:'JetBrains Mono',monospace;">{msg}</span>
                <span style="margin-left:auto;font-size:0.7rem;color:#FF6B35;font-weight:700;font-family:'JetBrains Mono',monospace;">{pct}%</span>
            </div>
            <style>@keyframes pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.3; }} }}</style>
            ''', unsafe_allow_html=True)

            # Show skeleton for the upcoming content area
            if stage == "prices":
                loading_skeleton(height=80, lines=2)
            elif stage == "optimizer":
                loading_skeleton(height=100, lines=3)
            elif stage == "news":
                loading_skeleton(height=120, lines=3)
            elif stage == "sentiment":
                loading_skeleton(height=60, lines=2)
            elif stage == "adaptive":
                loading_skeleton(height=150, lines=4)
            elif stage == "llm":
                loading_skeleton(height=200, lines=5)

    _set("Fetching price data...", 10, "prices")
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
            raise ValueError("No valid tickers")
        prices = prices[available]
        if isinstance(prices, pd.Series):
            prices = prices.to_frame()
        results["prices"] = prices
        returns_df = prices.pct_change(fill_method=None).dropna()
        if returns_df.empty:
            raise ValueError("Return series is empty; correlation cannot be calculated")
        results["returns"] = returns_df
        # Report generation receives an explicit matrix so it does not need to
        # reconstruct correlation data from Streamlit session objects.
        results["correlation_matrix"] = returns_df.corr()
    except Exception as exc:
        st.error(f"Price fetch failed: {exc}")
        return None


    _set("Calculating current allocation...", 20, "prices")

    latest_prices = {
        ticker: float(
            prices[ticker].dropna().iloc[-1]
        )
        for ticker in available
        if not prices[ticker].dropna().empty
    }

    try:
        current_allocation = calculate_current_allocation(
            holdings=holdings,
            latest_prices=latest_prices,
            base_currency=base_currency,
            fx_rate_provider=_cached_fx_rate,
        )
    except Exception as exc:
        current_allocation = {
            "base_currency": base_currency,
            "market_values": {},
            "current_weights": {},
            "total_market_value": None,
            "excluded_tickers": {
                ticker: f"{type(exc).__name__}: {exc}"
                for ticker in tickers
            },
            "is_complete": False,
        }

    results["current_allocation"] = current_allocation
    results["base_currency"] = base_currency

    excluded_tickers = current_allocation[
        "excluded_tickers"
    ]

    if excluded_tickers:
        st.warning(
            "Actual rebalance actions are unavailable because "
            "current price or FX data is missing for: "
            + ", ".join(sorted(excluded_tickers))
        )

    _set("Preparing optimizer...", 25, "optimizer")
    try:
        optimizer = PortfolioOptimizer(prices)
        baseline = optimizer.equal_weight_baseline()
        frontier_df = optimizer.efficient_frontier(n_points=800)
        results.update({"baseline": baseline, "frontier_df": frontier_df})
    except Exception as exc:
        st.error(f"Optimization setup failed: {exc}")
        return None

    _set("Fetching news...", 40, "news")
    all_news = {}
    for ticker in available:
        try:
            articles = fetch_news(ticker, company_name=None)
            if not articles:
                company = display_names.get(ticker, ticker).replace(".NS", "")
                articles = fetch_news(ticker, company_name=company)
            all_news[ticker] = articles
        except Exception as exc:
            all_news[ticker] = []
            st.warning(f"News fetch failed for {ticker}: {type(exc).__name__}: {exc}")
    results["all_news"] = all_news

    _set("Running FinBERT...", 55, "sentiment")

    # Public/report values preserve missing evidence as None.
    sentiment_scores = {}

    # The optimizer requires numeric values. A missing score receives
    # 0.0 here only to mean "apply no sentiment adjustment."
    optimization_sentiment_scores = {}

    for ticker in available:
        try:
            headlines = [
                article.get("title", "")
                for article in all_news.get(ticker, [])
                if article.get("title")
            ]

            if headlines:
                score = float(aggregate_sentiment(headlines))
                sentiment_scores[ticker] = score
                optimization_sentiment_scores[ticker] = score
            else:
                sentiment_scores[ticker] = None
                optimization_sentiment_scores[ticker] = 0.0

        except Exception as exc:
            sentiment_scores[ticker] = None
            optimization_sentiment_scores[ticker] = 0.0
            st.warning(
                f"Sentiment analysis failed for {ticker}: "
                f"{type(exc).__name__}: {exc}"
            )

    results["sentiment_scores"] = sentiment_scores
    results["optimization_sentiment_scores"] = (
        optimization_sentiment_scores
    )

    _set("Searching health-aware portfolios...", 72, "adaptive")
    try:
        risk_analyzer = RiskAnalyzer(prices)
        news_counts = {t: len(all_news.get(t, [])) for t in available}
        adaptive = AdaptiveHealthOptimizer(
           optimizer,
           risk_analyzer,
           optimization_sentiment_scores,
           news_counts,
        )

        selected = adaptive.search(alpha=alpha, portfolio_value=portfolio_value)

        opt_result = selected["opt_result"]
        combined = selected["combined"]
        risk_report = selected["risk_report"]
        final_weights = selected["final_weights"]

        rebalance_plan = build_rebalance_plan(
            current_weights=current_allocation[
                "current_weights"
            ],
            target_weights=final_weights,
            allocation_complete=bool(
                current_allocation["is_complete"]
            ),
        )

        results.update({
            "opt_result": opt_result,
            "combined": combined,
            "final_weights": final_weights,
            "final_stats": selected["final_stats"],
            "risk_report": risk_report,
            "health_score": selected["health_score"],
            "adaptive_candidates": selected["candidates"],
            "selected_cap": selected["selected_cap"],
            "tickers": available,
            "rebalance_plan": rebalance_plan,
        })
    except Exception as exc:
        st.error(f"Adaptive optimization failed: {exc}")
        return None

    # ── Evidence-grounded AI research commentary ─────
    _set("Generating AI research commentary...", 92, "llm")
    recommendations = []
    llm_error = None

    if use_llm:
        rag = None

        try:
            rag = RAGPipeline()
        except Exception as exc:
            llm_error = f"LLM initialization failed: {exc}"
            st.warning(llm_error)

        if rag is not None:
            for ticker in available:
                articles_text = [
                    article.get("title", "")
                    for article in all_news.get(ticker, [])
                    if article.get("title")
                ]
                sentiment_score = sentiment_scores.get(ticker)

                # Do not ask the LLM to interpret nonexistent evidence.
                if sentiment_score is None or not articles_text:
                    continue

                try:
                    rec = rag.generate_recommendation(
                        ticker=ticker,
                        sentiment_score=sentiment_score,
                        portfolio_weight=opt_result[
                            "weights"
                        ].get(ticker, 0.0),
                        retrieved_articles=articles_text,
                    )

                    if rec:
                        recommendations.append(rec)

                except Exception as exc:
                    st.warning(
                        "AI commentary failed for "
                        f"{display_names.get(ticker, ticker)}: "
                        f"{type(exc).__name__}: {exc}"
                    )

        if not recommendations and not llm_error:
            st.info(
                "No evidence-grounded AI commentary was returned. "
                "Quantitative results remain available."
            )

    else:
        st.info(
            "AI research commentary is disabled. "
            "Quantitative analysis remains available."
        )

    results["recommendations"] = recommendations
    status_placeholder.empty()
    return results


if run_button:
    with st.spinner(""):
        try:
            results = run_pipeline(tickers, alpha, portfolio_value, use_llm)
            if not results:
                st.stop()

            results["opt_result"]["sharpe_ratio"] = results["final_stats"]["sharpe_ratio"]
            results["opt_result"]["expected_return"] = results["final_stats"]["expected_return"]
            results["opt_result"]["volatility"] = results["final_stats"]["volatility"]

            st.session_state["results"] = results
            safe_opt = {}
            for key, value in results["opt_result"].items():
                safe_opt[key] = value.tolist() if isinstance(value, np.ndarray) else value
            safe_opt["baseline_sharpe"] = results["baseline"]["sharpe_ratio"]
            save_optimization_run(
                portfolio_id=portfolio["id"],
                alpha=alpha,
                opt_result=safe_opt,
                sentiment_scores=results["sentiment_scores"],
                recommendations=results["recommendations"],
                risk_report=results["risk_report"]
            )
            st.success("Analysis complete — saved to history")
        except Exception as e:
            st.error(f"Pipeline error: {e}")
            st.stop()


# ── Results Display ─────────────────────────────────────────
results = st.session_state.get("results")
if not results:
    info_card(
        "Ready to Optimize",
        "Configure your strategy settings above and click Run Optimization to begin the AI pipeline.",
        badge("CONFIGURE", "cyan"),
        accent="cyan"
    )
    st.stop()

available = results["tickers"]
opt_result = results["opt_result"]
baseline = results["baseline"]
final_weights = results["final_weights"]
sentiment_scores = results["sentiment_scores"]
risk_report = results["risk_report"]
recommendations = results.get("recommendations", [])
combined = results["combined"]
rebalance_plan = results.get("rebalance_plan", {})
current_allocation = results.get(
    "current_allocation",
    {},
)
frontier_df = results["frontier_df"]
prices = results["prices"]
returns_df = results["returns"]

sharpe = opt_result.get("sharpe_ratio", 0)
vol = risk_report.get("volatility", {}).get("portfolio_annualized", 0)
health = results.get("health_score") or HealthScoreEngine.calculate(
    sharpe=sharpe,
    volatility=vol,
    var95=(
        risk_report
        .get("value_at_risk", {})
        .get("historical_95", {})
        .get("var_pct", 0.0)
    ),
    max_drawdown_pct=(
        risk_report
        .get("drawdown", {})
        .get("portfolio", {})
        .get("max_drawdown_pct", 0.0)
    ),
    sentiment_scores={
        ticker: score
        for ticker, score in sentiment_scores.items()
        if score is not None
    },
    final_weights=final_weights,
    risk_report=risk_report,
    baseline_sharpe=baseline.get("sharpe_ratio"),
    news_counts={
        ticker: len(
            results.get("all_news", {}).get(ticker, [])
        )
        for ticker in available
    },
)
ai_score = health["score"]
score_label = f'{health["label"]} · {health["grade"]}'
var95 = risk_report["value_at_risk"]["historical_95"]

# ── KPI Metrics ─────────────────────────────────────────────
section_header("Key Performance Indicators", "Real-time composite metrics", accent="primary")
metrics = [
    {"label": "AI Score", "value": f"{ai_score:.0f}", "tone": "accent", "icon": "◈", "delta": score_label},
    {"label": "Sharpe Ratio", "value": f"{sharpe:.3f}", "tone": "cyan", "icon": "◉", "delta": f"{sharpe - baseline.get('sharpe_ratio', 0):+.3f} vs base"},
    {"label": "Exp Return", "value": f"{opt_result.get('expected_return', 0)*100:.1f}%", "tone": "positive" if opt_result.get("expected_return", 0) > 0 else "negative", "icon": "▲"},
    {"label": "Volatility", "value": f"{vol*100:.1f}%", "tone": "negative", "icon": "◊"},
    {"label": "95% VaR", "value": f"${var95['var_usd']:,.0f}", "tone": "negative", "icon": "⚡", "delta": f"{var95['var_pct']*100:.2f}%"},
]
metric_grid(metrics, columns=5)

# ── Exports ─────────────────────────────────────────────────
st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)


weights_export_rows = []

for ticker in available:
    plan_entry = rebalance_plan.get(ticker, {})

    weights_export_rows.append({
        "Ticker": display_names.get(ticker, ticker),
        "Current Weight": _safe_pct(
            plan_entry.get("current_weight"),
            2,
        ),
        "Quant Target": _safe_pct(
            opt_result["weights"].get(ticker),
            2,
        ),
        "Final Target": _safe_pct(
            final_weights.get(ticker),
            2,
        ),
        "Model Shift": _safe_pct(
            combined["weight_changes"][ticker]["change"],
            2,
        ),
        "Model Adjustment": classify_model_adjustment(
            opt_result["weights"].get(ticker, 0.0),
            final_weights.get(ticker, 0.0),
        ),
        "Rebalance Gap": _safe_pct(
            plan_entry.get("gap"),
            2,
        ),
        "Rebalance Action": plan_entry.get(
            "action",
            "UNAVAILABLE",
        ),
    })

weights_csv = (
    pd.DataFrame(weights_export_rows)
    .to_csv(index=False)
    .encode("utf-8")
)

risk_csv = pd.DataFrame([
    {"Metric": "Volatility", "Value": f"{risk_report['volatility']['portfolio_annualized']*100:.2f}%"},
    {"Metric": "95% VaR", "Value": f"${var95['var_usd']:,.0f}"},
    {"Metric": "99% VaR", "Value": f"${risk_report['value_at_risk']['historical_99']['var_usd']:,.0f}"}
]).to_csv(index=False).encode("utf-8")

col_e1, col_e2, col_e3, col_e4 = st.columns(4)
with col_e1:
    st.download_button("◉ Weights CSV", weights_csv, "optimized_weights.csv", "text/csv", use_container_width=True)
with col_e2:
    st.download_button("◉ Risk CSV", risk_csv, "risk_metrics.csv", "text/csv", use_container_width=True)
with col_e3:
    if st.button("◉ Share", use_container_width=True):
        st.code(f"Portfolio: {portfolio['name']} | Sharpe: {opt_result['sharpe_ratio']:.2f} | AI: {ai_score:.0f}/100", language=None)
with col_e4:
    try:
        report_html = generate_axiom_report(portfolio, results, display_names)
        st.download_button(
            "◉ Full Report",
            report_html.encode("utf-8"),
            f"AI_PORTFOLIO_REPORT_{portfolio['name'].upper().replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.html",
            "text/html",
            type="primary",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Report generation error: {e}")

# ── Tabs ────────────────────────────────────────────────────
section_header("Detailed Analytics", "Multi-dimensional portfolio intelligence", accent="violet")
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["◈ Overview", "⚖ Optimization", "◉ Sentiment", "◫ Risk", "◉ AI", "◫ Performance"])

with tab1:
    st.caption("High-level portfolio snapshot")
    c1, c2 = st.columns(2)
    disp = [display_names.get(t, t) for t in available]
    with c1:
        glass_container(accent="primary")
        fig = go.Figure(go.Bar(
            y=disp, x=[final_weights[t]*100 for t in available],
            orientation='h', marker_color='#FF6B35',
            text=[f"{final_weights[t]*100:.1f}%" for t in available],
            textposition='outside'
        ))
        fig.update_layout(title="Final Weights", xaxis_title="Weight (%)", yaxis=dict(autorange="reversed"), height=350)
        fig = apply_plotly_theme(fig)
        st.plotly_chart(fig, width='stretch')
    with c2:
        glass_container(accent="cyan")
        fig2 = go.Figure(go.Bar(
            y=disp, x=[100/len(available)]*len(available),
            orientation='h', marker_color='#8b8b9e',
            text=[f"{100/len(available):.1f}%"]*len(available),
            textposition='outside'
        ))
        fig2.update_layout(title=f"Equal Weight (Sharpe={baseline['sharpe_ratio']:.3f})", xaxis_title="Weight (%)", yaxis=dict(autorange="reversed"), height=350)
        fig2 = apply_plotly_theme(fig2)
        st.plotly_chart(fig2, width='stretch')

    glass_container(accent="primary")
    df_weights = pd.DataFrame([
    {
        "Ticker": display_names.get(t, t),
        "Quant Target": (
            f"{opt_result['weights'][t] * 100:.1f}%"
        ),
        "Final Target": (
            f"{final_weights[t] * 100:.1f}%"
        ),
        "Model Shift": (
            f"{combined['weight_changes'][t]['change'] * 100:+.1f}%"
        ),
        "Model Adjustment": classify_model_adjustment(
            opt_result["weights"].get(t, 0.0),
            final_weights.get(t, 0.0),
        ),
} for t in available
    ])
    st.dataframe(df_weights, hide_index=True, width='stretch')

with tab2:
    st.caption("Efficient frontier and optimal vs baseline")
    glass_container(accent="violet")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=frontier_df["volatility"]*100, y=frontier_df["return"]*100,
        mode='markers', marker=dict(
            color=frontier_df["sharpe"],
            colorscale=[[0,'#F43F5E'],[0.5,'#FF6B35'],[1,'#10B981']],
            size=5, opacity=0.6
        ), name="Frontier"
    ))
    fig.add_trace(go.Scatter(
        x=[opt_result["volatility"]*100], y=[opt_result["expected_return"]*100],
        text=[f"Final (Sharpe={opt_result['sharpe_ratio']:.3f})"],
        textposition="top center", mode="markers+text",
        marker=dict(color='#FF6B35', size=14, symbol='star'),
        name="Optimal"
    ))
    fig.add_trace(go.Scatter(
        x=[baseline["volatility"]*100], y=[baseline["expected_return"]*100],
        mode='markers+text', marker=dict(color='#8b8b9e', size=10, symbol='diamond'),
        text=[f"Baseline (Sharpe={baseline['sharpe_ratio']:.3f})"],
        textposition="bottom center", name="Baseline"
    ))
    fig.update_layout(title="Efficient Frontier", xaxis_title="Volatility (%)", yaxis_title="Return (%)", height=500)
    fig = apply_plotly_theme(fig)
    st.plotly_chart(fig, width='stretch')

with tab3:
    st.caption("FinBERT sentiment scores")
    for t in available:
        score = sentiment_scores[t]
        visual = get_sentiment_visual(score)

        progress_value = sentiment_progress_value(score)
        score_text = format_sentiment_score(score)

        ca, cb, cc = st.columns([1.5, 4, 1.5])

        ca.markdown(
            f"**{visual['symbol']} {display_names.get(t, t)}**"
        )
        cb.progress(progress_value)
        cc.markdown(
            f'<span class="{visual["css"]}">'
            f'{score_text} ({visual["label"]})'
            "</span>",
            unsafe_allow_html=True,
        )

    all_news = results.get("all_news", {})
    st.markdown("---")
    st.markdown("#### Recent Headlines")
    for t in available:
        articles = all_news.get(t, [])
        with st.expander(f"{display_names.get(t, t)} — {len(articles)} articles"):
            for a in articles[:6]:
                st.markdown(f"• {a.get('title', '')}")

with tab4:
    st.caption("Risk metrics, correlation, volatility")
    var99 = risk_report["value_at_risk"]["historical_99"]
    mdd = risk_report["drawdown"]["portfolio"]
    conc = risk_report["concentration"]

    glass_container(accent="red")
    r1, r2, r3, r4 = st.columns(4)

    r1.metric(
        "95% VaR (1-Day)",
        f"${abs(var95['var_usd']):,.0f}",
        delta=(
            f"{abs(var95['var_pct']) * 100:.2f}% "
            "potential loss"
        ),
        delta_color="off",
    )

    r2.metric(
        "99% VaR (1-Day)",
        f"${abs(var99['var_usd']):,.0f}",
        delta=(
            f"{abs(var99['var_pct']) * 100:.2f}% "
            "potential loss"
        ),
        delta_color="off",
    )

    r3.metric(
        "Max Drawdown",
        f"{abs(mdd['max_drawdown_pct']):.2f}%",
        delta="Peak-to-trough loss",
        delta_color="off",
    )

    r4.metric(
        "Concentration",
        conc.get("label", "N/A"),
        delta=f"HHI {conc.get('hhi', 0.0):.3f}",
        delta_color="off",
    )

    c1, c2 = st.columns(2)
    with c1:
        glass_container(accent="violet")
        corr = returns_df.corr()
        corr.columns = [display_names.get(t, t) for t in corr.columns]
        corr.index = corr.columns
        fig_c = px.imshow(corr, color_continuous_scale=[[0,'#F43F5E'],[0.5,'#12121a'],[1,'#10B981']], aspect="auto")
        fig_c.update_traces(texttemplate="%{z:.2f}")
        fig_c.update_layout(title="Correlation Matrix", height=400)
        fig_c = apply_plotly_theme(fig_c)
        st.plotly_chart(fig_c, width='stretch')
    with c2:
        glass_container(accent="amber")
        vols = risk_report["volatility"]["per_ticker_annualized"]
        vol_df = pd.DataFrame({
            "Ticker": [display_names.get(t, t) for t in vols.keys()],
            "Volatility": [v*100 for v in vols.values()]
        })
        fig_v = px.bar(vol_df, x="Volatility", y="Ticker", orientation='h',
                       color="Volatility", color_continuous_scale=[[0,'#10B981'],[0.5,'#FF6B35'],[1,'#F43F5E']])
        fig_v.add_vline(x=vol*100, line_dash="dash", line_color="#FF6B35",
                        annotation_text=f"Portfolio: {vol*100:.1f}%")
        fig_v.update_layout(yaxis=dict(autorange="reversed"), height=400)
        fig_v = apply_plotly_theme(fig_v)
        st.plotly_chart(fig_v, width='stretch')

    st.markdown("#### Risk Gauges")

    def make_risk_gauge(
        value: float,
        title: str,
        axis_max: float,
        color: str,
        threshold: float | None = None,
        suffix: str = "",
    ) -> go.Figure:
        gauge = {
            "axis": {
                "range": [0, axis_max],
                "tickcolor": "#8b8b9e",
                "tickfont": {
                    "color": "#8b8b9e",
                    "size": 10,
                },
            },
            "bar": {
                "color": color,
                "thickness": 0.7,
            },
            "bgcolor": "#0a0a0f",
            "bordercolor": "rgba(255,255,255,0.06)",
            "steps": [
                {
                    "range": [0, axis_max * 0.4],
                    "color": "rgba(16,185,129,0.08)",
                },
                {
                    "range": [
                        axis_max * 0.4,
                        axis_max * 0.7,
                    ],
                    "color": "rgba(255,107,53,0.08)",
                },
                {
                    "range": [
                        axis_max * 0.7,
                        axis_max,
                    ],
                    "color": "rgba(244,63,94,0.08)",
                },
            ],
        }

        if threshold is not None:
            gauge["threshold"] = {
                "line": {
                    "color": "#FF6B35",
                    "width": 2,
                },
                "thickness": 0.8,
                "value": threshold,
            }

        formatted_value = f"{value:.2f}{suffix}"

        figure = go.Figure(
            go.Indicator(
                mode="gauge",
                value=value,
                domain={
                    "x": [0.03, 0.97],
                    "y": [0.18, 0.90],
                },
                title={
                    "text": title,
                    "font": {
                        "color": "#f0f0f5",
                        "size": 13,
                    },
                },
                gauge=gauge,
            )
        )

        figure.add_annotation(
            x=0.5,
            y=0.08,
            xref="paper",
            yref="paper",
            text=formatted_value,
            showarrow=False,
            xanchor="center",
            yanchor="middle",
            font={
                "family": "JetBrains Mono, monospace",
                "color": "#f0f0f5",
                "size": 24,
            },
        )

        figure.update_layout(
            height=245,
            margin={
                "l": 8,
                "r": 8,
                "t": 45,
                "b": 8,
            },
        )

        return apply_plotly_theme(figure)


    sharpe_axis_max = max(
        4.0,
        math.ceil(max(0.0, sharpe) + 0.5),
    )


    g1, g2, g3 = st.columns(3)

    with g1:
        fig_g1 = make_risk_gauge(
            value=abs(var95["var_pct"]) * 100,
            title="95% One-Day VaR",
            axis_max=5.0,
            color="#F43F5E",
            threshold=2.5,
            suffix="%",
        )
        st.plotly_chart(
            fig_g1,
            width="stretch",
            key="risk_var95_gauge",
        )

    with g2:
        fig_g2 = make_risk_gauge(
            value=abs(mdd["max_drawdown_pct"]),
            title="Maximum Drawdown",
            axis_max=50.0,
            color="#FF6B35",
            threshold=20.0,
            suffix="%",
        )
        st.plotly_chart(
            fig_g2,
            width="stretch",
            key="risk_drawdown_gauge",
        )

    with g3:
        fig_g3 = make_risk_gauge(
            value=max(0.0, sharpe),
            title="Sharpe Ratio",
            axis_max=sharpe_axis_max,
            color="#10B981",
            threshold=1.0,
        )
        st.plotly_chart(
            fig_g3,
            width="stretch",
            key="risk_sharpe_gauge",
        )

with tab5:
    st.caption("Evidence-grounded research commentary from the configured Groq model")
    if not recommendations:
        info_card(
            "AI Research Commentary Unavailable",
            (
                "The quantitative analysis remains available. "
                "Enable AI commentary and re-run the pipeline if needed."
            ),
            badge("OPTIONAL", "warning"),
            accent="amber",
        )
    else:
        for rec in recommendations:
            ticker = rec.get("ticker", "")
            score = rec.get("sentiment_score")
            visual = get_sentiment_visual(score)
            score_text = format_sentiment_score(score)
            optimizer_weight_pct = rec.get(
                "portfolio_weight_pct",
                "N/A",
            )
            commentary = rec.get(
                "recommendation",
                "AI research commentary is unavailable.",
            )

            glass_container(accent=visual["accent"])

            st.markdown(
                f"**{display_names.get(ticker, ticker)}**"
                f" — Sentiment: {score_text} ({visual['label']})"
                f" | Optimizer target: {optimizer_weight_pct}%"
            )
            st.markdown(commentary)
            st.markdown(
                "<div style='height:8px;'></div>",
                unsafe_allow_html=True,
            )

with tab6:
    st.caption(
        "Historical cumulative returns and portfolio performance"
    )
    glass_container(accent="green")

    cumulative_returns = (
        (1.0 + returns_df)
        .cumprod()
        .sub(1.0)
        .mul(100.0)
    )

    # Create an independent figure. Do not reuse the Efficient
    # Frontier figure from the Optimization tab.
    ticker_return_fig = go.Figure()

    colors = [
        "#FF6B35",
        "#00D9FF",
        "#8B5CF6",
        "#10B981",
        "#F43F5E",
        "#F59E0B",
        "#EC4899",
        "#6366F1",
    ]

    for index, ticker in enumerate(
        cumulative_returns.columns
    ):
        ticker_return_fig.add_trace(
            go.Scatter(
                x=cumulative_returns.index,
                y=cumulative_returns[ticker],
                mode="lines",
                name=display_names.get(
                    ticker,
                    ticker,
                ),
                line={
                    "color": colors[
                        index % len(colors)
                    ],
                    "width": 1.7,
                },
                hovertemplate=(
                    "%{x|%Y-%m-%d}"
                    "<br>Cumulative return: %{y:+.2f}%"
                    "<extra>%{fullData.name}</extra>"
                ),
            )
        )

    ticker_return_fig.update_layout(
        title="Cumulative Return by Ticker",
        xaxis_title="Date",
        yaxis_title="Cumulative Return (%)",
        hovermode="x unified",
        height=450,
        legend_title_text="Ticker",
    )

    ticker_return_fig.update_yaxes(
        ticksuffix="%",
        zeroline=True,
        zerolinecolor="rgba(255,255,255,0.20)",
    )

    ticker_return_fig = apply_plotly_theme(
        ticker_return_fig
    )

    st.plotly_chart(
        ticker_return_fig,
        width="stretch",
        key="ticker_cumulative_returns",
    )

    st.caption(
        "Each line represents one ticker's standalone historical "
        "return. These lines do not apply portfolio weights."
    )


    st.markdown("#### Final Portfolio Cumulative Return")

    aligned_weights = pd.Series(
        {
            ticker: float(
                final_weights.get(ticker, 0.0)
            )
            for ticker in returns_df.columns
        },
        dtype=float,
    )

    aligned_weights = aligned_weights.reindex(
        returns_df.columns
    ).fillna(0.0)

    weight_total = float(aligned_weights.sum())

    if weight_total <= 0:
        st.info(
            "Portfolio performance is unavailable because "
            "the final weights contain no usable values."
        )
    else:
        aligned_weights = (
            aligned_weights / weight_total
        )

        portfolio_daily_returns = returns_df.mul(
            aligned_weights,
            axis=1,
        ).sum(axis=1)

        portfolio_cumulative_return = (
            (1.0 + portfolio_daily_returns)
            .cumprod()
            .sub(1.0)
            .mul(100.0)
        )

        portfolio_return_fig = go.Figure()

        portfolio_return_fig.add_trace(
            go.Scatter(
                x=portfolio_cumulative_return.index,
                y=portfolio_cumulative_return,
                mode="lines",
                name="Final Portfolio",
                line={
                    "color": "#FF6B35",
                    "width": 2.8,
                },
                hovertemplate=(
                    "%{x|%Y-%m-%d}"
                    "<br>Cumulative return: %{y:+.2f}%"
                    "<extra>Final Portfolio</extra>"
                ),
            )
        )

        portfolio_return_fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Cumulative Return (%)",
            hovermode="x unified",
            height=380,
            showlegend=False,
        )

        portfolio_return_fig.update_yaxes(
            ticksuffix="%",
            zeroline=True,
            zerolinecolor=(
                "rgba(255,255,255,0.20)"
            ),
        )

        portfolio_return_fig = apply_plotly_theme(
            portfolio_return_fig
        )

        st.plotly_chart(
            portfolio_return_fig,
            width="stretch",
            key="final_portfolio_cumulative_return",
        )

        ending_return = float(
            portfolio_cumulative_return.iloc[-1]
        )

        st.caption(
            f"Historical weighted cumulative return: "
            f"{ending_return:+.2f}%. "
            "Calculated using the current final target weights. "
            "This is an in-sample illustration, not a live "
            "trading track record."
        )

# ── Health Score Expander ───────────────────────────────────
with st.expander("◈ AI Health Score v3 — Explain Score", expanded=False):
    glass_container(accent="primary")
    score_rows = []
    for key, value in health.get("components", {}).items():
        score_rows.append({
            "Component": key.replace("_", " ").title(),
            "Score": round(value, 1),
            "Weight": f'{health.get("component_weights", {}).get(key, 0) * 100:.0f}%',
        })
    st.dataframe(pd.DataFrame(score_rows), hide_index=True, width='stretch')
    d = health.get("diagnostics", {})
    st.caption(
        f'Max Position {d.get("max_weight", 0)*100:.1f}% | '
        f'Top-2 {d.get("top_two_weight", 0)*100:.1f}% | '
        f'HHI {d.get("hhi", 0):.3f} | '
        f'Penalty {health.get("penalty_total", 0):.1f} pts'
    )
    for tip in health.get("improvements", []):
        st.markdown(f"• {tip}")
    if results.get("adaptive_candidates"):
        st.markdown("**Adaptive Cap Search**")
        cand_df = pd.DataFrame(results["adaptive_candidates"])
        if not cand_df.empty:
            cand_df["max_weight_cap"] = (
                cand_df["max_weight_cap"].map(
                    lambda value: (
                        f"{float(value) * 100:.1f}%"
                        if pd.notna(value)
                        else "N/A"
                    )
                )
            )

            cand_df["health_score"] = (
                cand_df["health_score"].map(
                    lambda value: (
                        round(float(value), 1)
                        if pd.notna(value)
                        else None
                    )
                )
            )

            cand_df["sharpe_ratio"] = (
                cand_df["sharpe_ratio"].map(
                    lambda value: (
                        round(float(value), 3)
                        if pd.notna(value)
                        else None
                    )
                )
            )

            cand_df["volatility"] = (
                cand_df["volatility"].map(
                    lambda value: (
                        f"{float(value) * 100:.1f}%"
                        if pd.notna(value)
                        else "N/A"
                    )
                )
            )

            cand_df = cand_df.rename(
                columns={
                    "max_weight_cap": "Max Weight",
                    "health_score": "Health",
                    "sharpe_ratio": "Sharpe",
                    "volatility": "Volatility",
                    "max_drawdown_pct": "Max Drawdown",
                }
            )

            if "Max Drawdown" in cand_df:
                cand_df["Max Drawdown"] = (
                    cand_df["Max Drawdown"].map(
                        lambda value: (
                            f"{float(value):.2f}%"
                            if pd.notna(value)
                            else "N/A"
                        )
                    )
                )

            st.dataframe(
                cand_df,
                hide_index=True,
                width="stretch",
            )


    st.caption(
        "Each line shows the standalone cumulative return of one "
        "ticker. It does not apply portfolio weights or represent "
        "the combined portfolio return."
    )

st.markdown("""
<div style="border-top:1px solid rgba(255,255,255,0.06);margin-top:32px;padding-top:16px;">
    <div style="font-size:0.65rem;color:#4a4a5e;text-align:center;letter-spacing:0.05em;">
        AXIOM Portfolio Intelligence · Terminal Edition
    </div>
</div>
""", unsafe_allow_html=True)
