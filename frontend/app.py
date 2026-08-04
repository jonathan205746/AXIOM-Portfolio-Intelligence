"""
frontend/app.py  (Bloomberg Terminal Edition)
----------------------------------------------
Hero Dashboard with terminal aesthetic.
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

# Auto-detect API URL: local dev → localhost, Render → deployed URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


try:
    from src.database.db import init_db, get_user_portfolios, get_portfolio_history
    init_db()
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False

st.set_page_config(page_title="AI Portfolio Optimizer | TERMINAL", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

# ── INJECT BLOOMBERG CSS ───────────────────────────────────
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
  --font: 'JetBrains Mono','Courier New','Consolas',monospace;
  --radius: 0px; --radius-sm: 2px;
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
.bb-sidebar-header span { color: var(--text-inverse) !important; font-size: 0.65rem; opacity: 0.8; }
.bb-section { padding: 8px 16px; border-bottom: 1px solid var(--border); }
.bb-section-title { font-size: 0.6rem; font-weight: 700; color: var(--accent) !important; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px; }
.bb-ticker-row { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; font-size: 0.75rem; border-bottom: 1px dotted var(--border); }
.bb-ticker-row:last-child { border-bottom: none; }
.bb-ticker-symbol { color: var(--text); font-weight: 600; }
.bb-ticker-price { color: var(--text-dim); font-family: var(--font); }
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
.bb-cmd-text { color: var(--text-dim); }
.bb-tape { background: var(--bg-panel); border-bottom: 1px solid var(--border); padding: 6px 0; overflow: hidden; white-space: nowrap; font-size: 0.75rem; }
.bb-tape-item { display: inline-block; margin-right: 24px; color: var(--text-dim); }
.bb-tape-item strong { color: var(--text); margin-right: 4px; }
.bb-tape-up { color: var(--positive); }
.bb-tape-down { color: var(--negative); }
.bb-panel { background: var(--bg-panel); border: 1px solid var(--border); margin-bottom: 1px; }
.bb-panel-header { background: var(--bg-hover); border-bottom: 1px solid var(--border); padding: 8px 12px; display: flex; align-items: center; justify-content: space-between; }
.bb-panel-title { font-size: 0.75rem; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: 1px; }
.bb-panel-subtitle { font-size: 0.65rem; color: var(--text-faded); }
.bb-panel-body { padding: 12px; }
.bb-panel-accent { border-top: 2px solid var(--accent); }
.bb-panel-green { border-top: 2px solid var(--positive); }
.bb-panel-red { border-top: 2px solid var(--negative); }
.bb-metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1px; background: var(--border); border: 1px solid var(--border); }
.bb-metric-cell { background: var(--bg-panel); padding: 12px; text-align: center; }
.bb-metric-value { font-size: 1.4rem; font-weight: 700; color: var(--text); line-height: 1; }
.bb-metric-value.pos { color: var(--positive); }
.bb-metric-value.neg { color: var(--negative); }
.bb-metric-value.accent { color: var(--accent); }
.bb-metric-label { font-size: 0.6rem; color: var(--text-faded); text-transform: uppercase; letter-spacing: 1px; margin-top: 6px; }
.bb-table-header { display: flex; background: var(--bg-hover); border-bottom: 1px solid var(--border-bright); padding: 6px 10px; font-size: 0.7rem; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: 0.5px; }
.bb-table-row { display: flex; border-bottom: 1px dotted var(--border); padding: 6px 10px; font-size: 0.78rem; transition: background 0.1s; }
.bb-table-row:hover { background: var(--bg-hover); }
.bb-table-row:last-child { border-bottom: none; }
.bb-table-cell { flex: 1; color: var(--text-dim); }
.bb-table-cell strong { color: var(--text); font-weight: 600; }
.stButton > button { background: var(--accent) !important; color: var(--text-inverse) !important; border: none !important; border-radius: var(--radius-sm) !important; font-family: var(--font) !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; font-size: 0.75rem !important; transition: all 0.15s !important; }
.stButton > button:hover { background: var(--accent-dim) !important; box-shadow: 0 0 12px var(--accent-glow) !important; }
[data-testid="stMetric"] { background: var(--bg-panel) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; }
[data-testid="stMetricValue"] { font-family: var(--font) !important; font-weight: 700 !important; color: var(--text) !important; }
[data-testid="stMetricLabel"] { font-family: var(--font) !important; color: var(--text-dim) !important; text-transform: uppercase !important; font-size: 0.6rem !important; letter-spacing: 1px !important; }
[data-testid="stTabs"] [data-baseweb="tab-list"] { gap: 0 !important; border-bottom: 1px solid var(--border) !important; background: var(--bg-panel) !important; }
[data-testid="stTabs"] [data-baseweb="tab"] { border-radius: 0 !important; padding: 10px 16px !important; font-weight: 600 !important; font-size: 0.75rem !important; color: var(--text-dim) !important; border: none !important; text-transform: uppercase; letter-spacing: 0.5px; }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background: var(--accent) !important; height: 2px !important; }
[data-testid="stTabs"] [aria-selected="true"] { color: var(--accent) !important; background: var(--accent-soft) !important; }
.stSelectbox > div > div, .stTextInput > div > div, .stNumberInput > div > div { background: var(--bg-input) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; color: var(--text) !important; }
.stTextInput > div > div > input, .stNumberInput > div > div > input { color: var(--text) !important; font-family: var(--font) !important; }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 3px; }
@media (max-width: 768px) { .block-container { padding: 0.5rem !important; } .bb-metric-grid { grid-template-columns: repeat(2, 1fr); } }
</style>
""", unsafe_allow_html=True)

logged_in = st.session_state.get("logged_in", False)
user = st.session_state.get("user", None)

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

# ── SIDEBAR ────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="bb-sidebar-header"><h1>▶ AI PORTFOLIO OPTIMIZER</h1><span>TERMINAL EDITION v5.0</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="bb-section"><div class="bb-section-title">Market Data</div>', unsafe_allow_html=True)
    for name, data in market_data.items():
        cls = "bb-ticker-change-pos" if data["change"] >= 0 else "bb-ticker-change-neg"
        sign = "+" if data["change"] >= 0 else ""
        st.markdown(f'<div class="bb-ticker-row"><span class="bb-ticker-symbol">{name}</span><div><span class="bb-ticker-price">{data["price"]:,.2f}</span> <span class="{cls}">{sign}{data["change"]:.2f}%</span></div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if logged_in and user:
        uname = user.get("username", "USER")
        st.markdown(f'<div class="bb-user-block"><div class="bb-user-avatar">{uname[:2].upper()}</div><div class="bb-user-info"><div class="bb-user-name">{uname.upper()}</div><div class="bb-user-role">INVESTOR ACCOUNT</div></div></div>', unsafe_allow_html=True)

        st.markdown('<div class="bb-section"><div class="bb-section-title">Navigation</div>', unsafe_allow_html=True)
        pages = [("app.py", "⌂", "DASHBOARD"), ("pages/2_Portfolio.py", "◫", "PORTFOLIO"), ("pages/3_Analysis.py", "▣", "ANALYSIS"), ("pages/4_History.py", "◫", "HISTORY"), ("pages/5_Compare.py", "⚖", "COMPARE")]
        for page, icon, label in pages:
            active = " active" if page == "app.py" else ""
            if page == "app.py":
                st.markdown(f'<div class="bb-nav-item{active}">{icon}&nbsp;&nbsp;{label}</div>', unsafe_allow_html=True)
            else:
                st.page_link(page, label=f"{icon}  {label}")
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("◀ LOGOUT",   ):
            for k in ["logged_in", "user", "current_portfolio", "results"]:
                st.session_state.pop(k, None)
            st.switch_page("app.py")
    else:
        st.markdown('<div class="bb-section"><div class="bb-section-title">Account</div>', unsafe_allow_html=True)
        st.page_link("pages/1_Login.py", label="▶ LOGIN / REGISTER")
        st.markdown('<p style="font-size:0.7rem;color:var(--text-faded);margin-top:8px;">Authenticate to access portfolio tools and AI analytics.</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="bb-section"><div class="bb-section-title">Markets</div><div style="font-size:0.75rem;color:var(--text-dim);line-height:1.8">US: AAPL MSFT NVDA GOOGL<br>IN: TCS INFY RELIANCE</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="bb-sidebar-footer">AI PORTFOLIO OPTIMIZER<br>Bloomberg Terminal Edition</div>', unsafe_allow_html=True)

# ── COMMAND BAR ────────────────────────────────────────────
st.markdown(f'<div class="bb-cmd-bar"><span class="bb-cmd-prompt">➜</span><span class="bb-cmd-text">AI-PORTFOLIO-OPTIMIZER v5.0</span><span style="color:var(--text-faded);margin-left:auto;font-size:0.7rem;">SESSION: {"AUTHENTICATED" if logged_in else "GUEST"}</span></div>', unsafe_allow_html=True)

# ── TICKER TAPE ────────────────────────────────────────────
tape_items = ""
for name, data in market_data.items():
    cls = "bb-tape-up" if data["change"] >= 0 else "bb-tape-down"
    sign = "+" if data["change"] >= 0 else ""
    tape_items += f'<span class="bb-tape-item"><strong>{name}</strong> {data["price"]:,.2f} <span class="{cls}">{sign}{data["change"]:.2f}%</span></span>'
st.markdown(f'<div class="bb-tape">{tape_items}</div>', unsafe_allow_html=True)

# ── MAIN DASHBOARD ─────────────────────────────────────────
if not DB_AVAILABLE:
    st.error("⚠ DATABASE OFFLINE — Run `pip install sqlalchemy bcrypt`")

st.markdown('<div style="padding:12px 0;"><span style="font-size:1.6rem;font-weight:800;color:var(--text);letter-spacing:-1px;">AI PORTFOLIO OPTIMIZER</span><br><span style="font-size:0.8rem;color:var(--text-dim);">QUANTITATIVE ANALYSIS & SENTIMENT ENGINE — US & INDIAN EQUITIES</span></div>', unsafe_allow_html=True)

if logged_in and user and DB_AVAILABLE:
    portfolios = get_user_portfolios(user["id"]) if DB_AVAILABLE else []
    results = st.session_state.get("results")

    # KPI Panel
    if results and portfolios:
        try:
            opt = results.get("opt_result", {})
            risk = results.get("risk_report", {})
            sent = results.get("sentiment_scores", {})
            fw = results.get("final_weights", {})
            sharpe = opt.get("sharpe_ratio", 0)
            var95 = abs(risk.get("value_at_risk", {}).get("historical_95", {}).get("var_pct", 0))
            vol = risk.get("volatility", {}).get("portfolio_annualized", 0)
            avg_sent = sum(sent.values()) / len(sent) if sent else 0
            div = sum(1 for w in fw.values() if w > 0.01) / len(fw) if fw else 0
            ss = min(max(sharpe * 25, 0), 100)
            vs = max(0, 100 - var95 * 1000)
            vos = max(0, 100 - vol * 100)
            sns = (avg_sent + 1) * 50
            ds = div * 100
            ai_score = min(100, max(0, ss * 0.35 + vs * 0.2 + vos * 0.2 + sns * 0.15 + ds * 0.1))
        except Exception:
            ai_score, sharpe, vol, avg_sent = 0, 0, 0, 0

        st.markdown('<div class="bb-panel bb-panel-accent"><div class="bb-panel-header"><span class="bb-panel-title">◈ Portfolio Health</span><span class="bb-panel-subtitle">REAL-TIME METRICS</span></div><div class="bb-panel-body">', unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns(5)
        metrics = [
            (c1, f"{ai_score:.0f}", "AI SCORE", "accent"),
            (c2, f"{sharpe:.2f}", "SHARPE RATIO", ""),
            (c3, f"{opt.get('expected_return', 0)*100:.1f}%", "EXP RETURN", "pos" if opt.get('expected_return', 0) > 0 else "neg"),
            (c4, f"{vol*100:.1f}%", "VOLATILITY", "neg"),
            (c5, f"{avg_sent:+.2f}", "SENTIMENT", "pos" if avg_sent > 0 else "neg"),
        ]
        for col, val, lbl, color_cls in metrics:
            with col:
                st.markdown(f'<div style="text-align:center;padding:8px;"><div class="bb-metric-value {color_cls}">{val}</div><div class="bb-metric-label">{lbl}</div></div>', unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("◫ PORTFOLIO",   ):
                st.switch_page("pages/2_Portfolio.py")
        with b2:
            if st.button("▣ RUN ANALYSIS",   ):
                st.switch_page("pages/3_Analysis.py")
        with b3:
            if st.button("⚖ BENCHMARK",   ):
                st.switch_page("pages/5_Compare.py")
    else:
        st.markdown('<div class="bb-panel"><div class="bb-panel-body"><span style="color:var(--text-dim);font-size:0.85rem;">No analysis data. Build portfolio and run first optimization.</span></div></div>', unsafe_allow_html=True)
        if st.button("▶ INITIALIZE PORTFOLIO", type="primary"):
            st.switch_page("pages/2_Portfolio.py")

    if portfolios:
        st.markdown('<div class="bb-panel bb-panel-green"><div class="bb-panel-header"><span class="bb-panel-title">◫ Active Portfolios</span><span class="bb-panel-subtitle">{0} RECORDS</span></div><div class="bb-panel-body">'.format(len(portfolios)), unsafe_allow_html=True)
        cols = st.columns(min(len(portfolios), 3))
        for i, pf in enumerate(portfolios[:3]):
            hist = get_portfolio_history(pf["id"], limit=1)
            last = hist[0] if hist else None
            sh = f"{last['sharpe_ratio']:.3f}" if last and last.get("sharpe_ratio") else "—"
            ret = f"{last['expected_return']*100:.1f}%" if last and last.get("expected_return") else "—"
            vol_ = f"{last['volatility']*100:.1f}%" if last and last.get("volatility") else "—"
            rd = last["run_date"][:10] if last else "NO RUNS"
            with cols[i]:
                st.markdown(f'<div style="border:1px solid var(--border);padding:12px;background:var(--bg-hover);"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;"><strong style="color:var(--text);font-size:0.85rem;">{pf["name"].upper()}</strong><span style="background:var(--accent-soft);color:var(--accent);padding:1px 6px;font-size:0.6rem;font-weight:700;">{pf["currency"]}</span></div><div style="font-size:0.75rem;color:var(--text-dim);line-height:1.8">SHARPE: <strong style="color:var(--text)">{sh}</strong><br>RETURN: <strong style="color:var(--positive)">{ret}</strong><br>VOL: <strong style="color:var(--negative)">{vol_}</strong><br><span style="color:var(--text-faded)">LAST: {rd}</span></div></div>', unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)
else:
    # Landing page for guests
    st.markdown('<div class="bb-panel bb-panel-accent"><div class="bb-panel-header"><span class="bb-panel-title">◈ System Overview</span></div><div class="bb-panel-body">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    feats = [
        (c1, "◫", "REAL-TIME", "Live yfinance feeds"),
        (c2, "◈", "SENTIMENT", "FinBERT NLP scoring"),
        (c3, "▣", "OPTIMIZER", "Sharpe maximization"),
        (c4, "◉", "LLM ENGINE", "Groq Llama 3.3 70B"),
        (c5, "⚖", "BENCHMARK", "SPY comparison"),
    ]
    for col, icon, title, desc in feats:
        with col:
            st.markdown(f'<div style="text-align:center;padding:8px;"><div style="font-size:1.4rem;color:var(--accent);margin-bottom:4px;">{icon}</div><div style="font-size:0.75rem;font-weight:700;color:var(--text);">{title}</div><div style="font-size:0.65rem;color:var(--text-dim);">{desc}</div></div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

    left, right = st.columns([1.2, 1])
    with left:
        st.markdown('<div class="bb-panel"><div class="bb-panel-header"><span class="bb-panel-title">◉ Workflow</span></div><div class="bb-panel-body">', unsafe_allow_html=True)
        steps = [("01", "ADD HOLDINGS", "US or Indian tickers with qty & price"), ("02", "FETCH DATA", "Prices, news, sentiment in one click"), ("03", "OPTIMIZE", "Max Sharpe adjusted for sentiment"), ("04", "LLM REASONING", "Plain-English per ticker guidance"), ("05", "TRACK", "Every run saved vs SPY benchmark")]
        for num, title, desc in steps:
            st.markdown(f'<div style="display:flex;align-items:flex-start;gap:10px;margin-bottom:10px;font-size:0.8rem"><span style="background:var(--accent);color:var(--text-inverse);padding:2px 6px;font-size:0.65rem;font-weight:800;min-width:24px;text-align:center;">{num}</span><span><strong style="color:var(--text)">{title}</strong><br><span style="color:var(--text-dim);font-size:0.72rem;">{desc}</span></span></div>', unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="bb-panel"><div class="bb-panel-header"><span class="bb-panel-title">◫ Supported Tickers</span></div><div class="bb-panel-body">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.75rem;color:var(--text-dim);margin-bottom:8px;"><strong style="color:var(--text)">US LARGE-CAP</strong></div>', unsafe_allow_html=True)
        st.code("AAPL MSFT GOOGL AMZN NVDA META TSLA NFLX", language=None)
        st.markdown('<div style="font-size:0.75rem;color:var(--text-dim);margin-bottom:8px;"><strong style="color:var(--text)">INDIAN NSE</strong></div>', unsafe_allow_html=True)
        st.code("TCS INFY RELIANCE WIPRO HDFCBANK ICICIBANK", language=None)
        st.markdown('</div></div>', unsafe_allow_html=True)

    cta1, cta2, _ = st.columns([1, 1, 2])
    with cta1:
        if st.button("▶ AUTHENTICATE", type="primary"):
            st.switch_page("pages/1_Login.py")
    with cta2:
        st.link_button("◉ SOURCE CODE", "https://github.com/Parmodk2310/AI-Powered-Portfolio-Optimizer"   )

st.markdown("---")
st.caption("AI PORTFOLIO OPTIMIZER | Bloomberg Terminal Edition | Built by Parmod | Stack: FinBERT · FAISS · Groq · Streamlit")
