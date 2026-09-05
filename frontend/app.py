"""
Axiom Dashboard V1.0.0
Institutional-grade portfolio intelligence hub.
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Axiom | Portfolio Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Inject Design System ────────────────────────────────────
from frontend.ui.theme import inject_theme
from frontend.ui.components import (
    sidebar_brand, sidebar_user, sidebar_nav_item,
    command_bar, ticker_tape, metric_grid, section_header,
    info_card, badge, status_pill, glass_panel
)
inject_theme()

# ── Database Init ───────────────────────────────────────────
try:
    from src.database.db import (
        get_portfolio_history,
        get_user_portfolios,
        init_db,
    )
    from src.optimization.health_score import HealthScoreEngine

    init_db()
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False

logged_in = st.session_state.get("logged_in", False)
user = st.session_state.get("user", None)

# ── Market Data ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def _market_snapshot():
    fallback = {
        "SPX": {"price": 4500.0, "change": 0.45},
        "NIFTY": {"price": 22500.0, "change": -0.12},
        "NDX": {"price": 14000.0, "change": 0.78},
        "BTC": {"price": 67500.0, "change": 1.23},
        "ETH": {"price": 3450.0, "change": -0.85},
        "GOLD": {"price": 2450.0, "change": 0.32},
    }
    out = {}
    try:
        import yfinance as yf
        for t, n in [("^GSPC", "SPX"), ("^NSEI", "NIFTY"), ("^IXIC", "NDX"),
                     ("BTC-USD", "BTC"), ("ETH-USD", "ETH"), ("GC=F", "GOLD")]:
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

# ── SIDEBAR ─────────────────────────────────────────────────
with st.sidebar:
    sidebar_brand()
    
    # Market snapshot mini-cards
    st.markdown("""
    <div style="padding: 0 16px; margin: 12px 0;">
        <div style="font-size:0.6rem;color:#4a4a5e;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">
            Global Markets
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    for name, data in market_data.items():
        color = "#10B981" if data["change"] >= 0 else "#F43F5E"
        icon = "▲" if data["change"] >= 0 else "▼"
        sign = "+" if data["change"] >= 0 else ""
        st.markdown(f"""
        <div style="
            display: flex; justify-content: space-between; align-items: center;
            padding: 6px 16px; font-size: 0.75rem;
            border-bottom: 1px solid rgba(255,255,255,0.03);
            font-family: 'JetBrains Mono', monospace;
            transition: all 0.15s ease;
        ">
            <span style="color: #f0f0f5; font-weight: 600;">{name}</span>
            <div>
                <span style="color: #8b8b9e;">{data['price']:,.2f}</span>
                <span style="color: {color}; font-weight: 700; margin-left: 6px;">{icon} {sign}{data['change']:.2f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='border-top:1px solid rgba(255,255,255,0.06);margin:12px 0;'></div>", unsafe_allow_html=True)
    
    if logged_in and user:
        sidebar_user(user.get("username", "User"), "Portfolio Manager")
        
        st.markdown("""
        <div style="padding: 0 16px; margin-bottom: 8px;">
            <div style="font-size:0.6rem;color:#4a4a5e;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;">
                Navigation
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        pages = [
            ("app.py", "◈", "Dashboard", True),
            ("pages/2_Portfolio.py", "◫", "Portfolio", False),
            ("pages/3_Analysis.py", "▣", "Analysis", False),
            ("pages/4_History.py", "◫", "History", False),
            ("pages/5_Compare.py", "⚖", "Benchmark", False),
        ]
        for page, icon, label, is_active in pages:
            if is_active:
                st.markdown(sidebar_nav_item(label, icon, active=True), unsafe_allow_html=True)
            else:
                st.page_link(page, label=f"{icon}  {label}", width='stretch')
        
        st.markdown("<div style='border-top:1px solid rgba(255,255,255,0.06);margin:12px 0;'></div>", unsafe_allow_html=True)
        
        if st.button("◀ Logout", key="logout_main"):
            for k in ["logged_in", "user", "current_portfolio", "results"]:
                st.session_state.pop(k, None)
            st.rerun()
    else:
        st.markdown("""
        <div style="padding: 0 16px; margin: 12px 0;">
            <div style="font-size:0.6rem;color:#4a4a5e;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">
                Account
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.page_link("pages/1_Login.py", label="🔐  Authenticate", width="stretch")
        st.markdown("""
        <div style="padding: 8px 16px; font-size: 0.7rem; color: #4a4a5e; line-height: 1.5;">
            Sign in to access quantitative analytics, AI recommendations, and portfolio tracking.
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="padding: 12px 16px; margin-top: auto; border-top: 1px solid rgba(255,255,255,0.06);">
        <div style="font-size:0.6rem;color:#4a4a5e;text-align:center;letter-spacing:0.05em;">
            AXIOM V1.0.0 · Portfolio Intelligence
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── COMMAND BAR ─────────────────────────────────────────────
status = "LIVE" if logged_in else "GUEST"
command_bar("AXIOM / DASHBOARD", f"SESSION: {status}")

# ── TICKER TAPE ─────────────────────────────────────────────
ticker_tape([{"name": k, **v} for k, v in market_data.items()])

# ── MAIN CONTENT ────────────────────────────────────────────
if not DB_AVAILABLE:
    st.error("⚠ Database offline — ensure SQLite is writable")

st.markdown("""
<div style="padding: 20px 0 12px;">
    <div style="font-size:1.8rem;font-weight:800;color:#f0f0f5;letter-spacing:-0.03em;font-family:'Inter',sans-serif;line-height:1.1;">
        Portfolio Intelligence
    </div>
    <div style="font-size:0.85rem;color:#8b8b9e;margin-top:6px;font-weight:400;">
        Quantitative analysis, sentiment engine, and AI-driven optimization
    </div>
</div>
""", unsafe_allow_html=True)

if logged_in and user and DB_AVAILABLE:
    portfolios = get_user_portfolios(user["id"])
    results = st.session_state.get("results")
    
    # KPI Section
    if results and portfolios:
        try:
            opt = results.get("opt_result", {})
            risk = results.get("risk_report", {})
            sent = results.get("sentiment_scores", {})
            final_weights = results.get("final_weights", {})
            baseline = results.get("baseline", {})
            all_news = results.get("all_news", {})

            sharpe = opt.get("sharpe_ratio", 0)
            vol = (
                risk.get("volatility", {})
                .get("portfolio_annualized", 0)
            )

            valid_sentiment = {
                ticker: score
                for ticker, score in sent.items()
                if score is not None
            }
            avg_sent = (
                sum(valid_sentiment.values()) / len(valid_sentiment)
                if valid_sentiment
                else 0
            )

            health = (
                results.get("health_score")
                or HealthScoreEngine.calculate(
                    sharpe=sharpe,
                    volatility=vol,
                    var95=(
                        risk
                        .get("value_at_risk", {})
                        .get("historical_95", {})
                        .get("var_pct", 0.0)
                    ),
                    max_drawdown_pct=(
                        risk
                        .get("drawdown", {})
                        .get("portfolio", {})
                        .get("max_drawdown_pct", 0.0)
                    ),
                    sentiment_scores=valid_sentiment,
                    final_weights=final_weights,
                    risk_report=risk,
                    baseline_sharpe=baseline.get("sharpe_ratio"),
                    news_counts={
                        ticker: len(all_news.get(ticker, []))
                        for ticker in final_weights
                    },
                )
            )

            portfolio_health_score = float(
                health.get("score", 0)
            )
        except Exception:
            portfolio_health_score = 0
            sharpe = 0
            vol = 0
            avg_sent = 0
        
        section_header("Portfolio Health", "Real-time composite metrics", accent="primary")
        
        metrics = [
            {"label": "Portfolio Health", "value": f"{portfolio_health_score:.0f}", "tone": "accent", "icon": "◈", "delta": f"{portfolio_health_score:.0f}/100"},
            {"label": "Sharpe Ratio", "value": f"{sharpe:.2f}", "tone": "cyan", "icon": "◉"},
            {"label": "Exp Return", "value": f"{opt.get('expected_return', 0)*100:.1f}%", "tone": "positive" if opt.get('expected_return', 0) > 0 else "negative", "icon": "▲"},
            {"label": "Volatility", "value": f"{vol*100:.1f}%", "tone": "negative", "icon": "◊"},
            {"label": "Sentiment", "value": f"{avg_sent:+.2f}", "tone": "positive" if avg_sent > 0 else "negative", "icon": "◎"},
        ]
        metric_grid(metrics, columns=5)
        
        # Quick Actions
        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("◫ Open Portfolio", width='stretch'):
                st.switch_page("pages/2_Portfolio.py")
        with c2:
            if st.button("▣ Run Analysis", type="primary", width='stretch'):
                st.switch_page("pages/3_Analysis.py")
        with c3:
            if st.button("⚖ Benchmark", width='stretch'):
                st.switch_page("pages/5_Compare.py")
    else:
        info_card(
            "No Analysis Data",
            "Build a portfolio and run your first optimization to unlock the AI health dashboard.",
            badge("GET STARTED", "accent"),
            accent="cyan"
        )
        if st.button("▶ Initialize Portfolio", type="primary", width='stretch'):
            st.switch_page("pages/2_Portfolio.py")
    
    # Active Portfolios
    if portfolios:
        section_header("Active Portfolios", f"{len(portfolios)} records", accent="green")
        
        cols = st.columns(min(len(portfolios), 3))
        for i, pf in enumerate(portfolios[:3]):
            hist = get_portfolio_history(pf["id"], limit=1)
            last = hist[0] if hist else None
            sh = f"{last['sharpe_ratio']:.3f}" if last and last.get("sharpe_ratio") else "—"
            ret = f"{last['expected_return']*100:.1f}%" if last and last.get("expected_return") else "—"
            vol_ = f"{last['volatility']*100:.1f}%" if last and last.get("volatility") else "—"
            rd = last["run_date"][:10] if last else "NO RUNS"
            
            with cols[i]:
                st.markdown(f"""
                <div style="
                    background: rgba(18,18,26,0.72);
                    border: 1px solid rgba(255,255,255,0.06);
                    border-radius: 12px;
                    backdrop-filter: blur(20px);
                    padding: 16px;
                    transition: all 0.2s ease;
                    box-shadow: 0 4px 24px rgba(0,0,0,0.2);
                ">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                        <strong style="color:#f0f0f5;font-size:0.85rem;font-weight:700;font-family:'Inter',sans-serif;">{pf['name'].upper()}</strong>
                        <span style="background:rgba(255,107,53,0.12);color:#FF6B35;padding:2px 8px;border-radius:6px;font-size:0.6rem;font-weight:700;letter-spacing:0.04em;">{pf['currency']}</span>
                    </div>
                    <div style="font-size:0.75rem;color:#8b8b9e;line-height:1.8;font-family:'JetBrains Mono',monospace;">
                        <div style="display:flex;justify-content:space-between;">
                            <span>SHARPE</span><strong style="color:#f0f0f5">{sh}</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between;">
                            <span>RETURN</span><strong style="color:#10B981">{ret}</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between;">
                            <span>VOLATILITY</span><strong style="color:#F43F5E">{vol_}</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between;margin-top:4px;padding-top:4px;border-top:1px solid rgba(255,255,255,0.04);">
                            <span style="color:#4a4a5e;font-size:0.65rem;">LAST RUN</span>
                            <span style="color:#4a4a5e;font-size:0.65rem;">{rd}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
else:
    # Guest Landing
    section_header("System Overview", "Capabilities & architecture", accent="cyan")
    
    feats = [
    (
        "◫",
        "Market Data",
        "Yahoo Finance prices with five-minute market caching",
        "primary",
    ),
    (
        "◈",
        "Sentiment",
        "FinBERT scoring on ticker-relevant financial news",
        "cyan",
    ),
    (
        "▣",
        "Optimizer",
        "Constrained mean-variance Sharpe optimization",
        "green",
    ),
    (
        "◉",
        "LLM Engine",
        "Groq-hosted AI reasoning and ticker guidance",
        "violet",
    ),
    (
        "⚖",
        "Benchmark",
        "Final target vs equal-weight and SPY comparison",
        "accent",
    ),
]
    
    cols = st.columns(5)
    for col, (icon, title, desc, accent) in zip(cols, feats):
        color = {"primary": "#FF6B35", "cyan": "#00D9FF", "green": "#10B981", "violet": "#8B5CF6", "accent": "#FF6B35"}[accent]
        with col:
            st.markdown(f"""
            <div style="
                background: rgba(18,18,26,0.72);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 12px;
                backdrop-filter: blur(20px);
                padding: 20px 12px;
                text-align: center;
                transition: all 0.2s ease;
                height: 100%;
            ">
                <div style="font-size:1.6rem;color:{color};margin-bottom:8px;text-shadow:0 0 20px {color}40;">{icon}</div>
                <div style="font-size:0.8rem;font-weight:700;color:#f0f0f5;margin-bottom:4px;font-family:'Inter',sans-serif;">{title}</div>
                <div style="font-size:0.7rem;color:#4a4a5e;line-height:1.4;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    
    left, right = st.columns([1.2, 1])
    with left:
        section_header("Workflow", "Step-by-step pipeline", accent="primary")
        steps = [
    (
        "01",
        "Add Holdings",
        "Add US or Indian equities with quantity and purchase basis",
    ),
    (
        "02",
        "Fetch Market Data",
        "Retrieve historical prices and ticker-relevant news",
    ),
    (
        "03",
        "Optimize",
        "Maximize historical Sharpe under allocation constraints",
    ),
    (
        "04",
        "Apply AI Signals",
        "Adjust target weights and generate per-ticker guidance",
    ),
    (
        "05",
        "Track & Compare",
        "Save each run and compare final targets with equal-weight and SPY",
    ),
]
        for num, title, desc in steps:
            st.markdown(f"""
            <div style="
                display: flex; align-items: flex-start; gap: 12px;
                margin-bottom: 12px; padding: 12px;
                background: rgba(18,18,26,0.5);
                border: 1px solid rgba(255,255,255,0.04);
                border-radius: 10px;
                transition: all 0.2s ease;
            ">
                <span style="
                    background: linear-gradient(135deg, #FF6B35, #CC4F25);
                    color: #020202;
                    padding: 4px 8px;
                    border-radius: 6px;
                    font-size: 0.65rem;
                    font-weight: 800;
                    font-family: 'JetBrains Mono', monospace;
                    min-width: 28px;
                    text-align: center;
                ">{num}</span>
                <span>
                    <strong style="color: #f0f0f5; font-size: 0.82rem; font-family: 'Inter', sans-serif;">{title}</strong>
                    <br><span style="color: #4a4a5e; font-size: 0.75rem;">{desc}</span>
                </span>
            </div>
            """, unsafe_allow_html=True)
    
    with right:
        section_header(
            "Example Tickers",
            "Common US and Indian equity symbols",
            accent="green",
        )

        outer_style = (
            "background:rgba(18,18,26,0.5);"
            "border:1px solid rgba(255,255,255,0.04);"
            "border-radius:10px;"
            "padding:14px;"
            "margin-bottom:10px;"
        )

        title_style = (
            "font-size:0.75rem;"
            "color:#8b8b9e;"
            "margin-bottom:6px;"
            "font-weight:600;"
        )

        content_style = (
            "background:rgba(255,255,255,0.03);"
            "padding:6px 10px;"
            "border-radius:6px;"
            "display:flex;"
            "align-items:center;"
            "justify-content:center;"
            "min-height:58px;"
            "color:#f0f0f5;"
            "font-size:0.75rem;"
            "line-height:1.6;"
            "text-align:center;"
            "font-family:'JetBrains Mono',monospace;"
            "border:1px solid rgba(255,255,255,0.04);"
        )

        cards = [
            (
                "US EQUITY EXAMPLES",
                "AAPL · MSFT · GOOGL · AMZN · NVDA · META · TSLA · NFLX",
            ),
            (
                "INDIAN NSE EXAMPLES",
                "TCS · INFY · RELIANCE · WIPRO · HDFCBANK · ICICIBANK",
            ),
            (
                "PORTFOLIO GUARDRAILS",
                "Long-only allocation · Normalized weights · "
                "Per-asset allocation caps · Common-date validation",
            ),
            (
                "RISK &amp; REPORTING",
                "VaR · Drawdown · Volatility · Sharpe ratio · "
                "Benchmark comparison · Downloadable portfolio report",
            ),
        ]

        cards_html = "".join(
            (
                f'<div style="{outer_style}">'
                f'<div style="{title_style}">{title}</div>'
                f'<div style="{content_style}">{content}</div>'
                "</div>"
            )
            for title, content in cards
        )

        st.markdown(cards_html, unsafe_allow_html=True)


    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    cta1, cta2, _ = st.columns([1, 1, 2])
    with cta1:
        if st.button("▶ Authenticate", type="primary", width='stretch'):
            st.switch_page("pages/1_Login.py")
    with cta2:
        st.link_button("◉ Source Code", "https://github.com/Parmodk2310/AI-Powered-Portfolio-Optimizer", width='stretch')

st.markdown("""
<div style="border-top:1px solid rgba(255,255,255,0.06);margin-top:32px;padding-top:16px;">
    <div style="font-size:0.65rem;color:#4a4a5e;text-align:center;letter-spacing:0.05em;">
        AXIOM Portfolio Intelligence · Built by Parmod · Stack: FinBERT · FAISS · Groq · Streamlit
    </div>
</div>
""", unsafe_allow_html=True)
