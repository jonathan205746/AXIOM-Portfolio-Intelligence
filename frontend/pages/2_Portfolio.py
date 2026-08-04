"""
frontend/pages/2_Portfolio.py  (Bloomberg Terminal Edition)
-----------------------------------------------------------
Holdings management with terminal aesthetic.
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import yfinance as yf
from datetime import datetime, date
import plotly.express as px
from src.database.db import get_user_portfolios, create_portfolio, delete_portfolio, get_portfolio_holdings, add_holding, delete_holding

st.set_page_config(page_title="PORTFOLIO | AI Portfolio Optimizer", page_icon="📂", layout="wide")

if not st.session_state.get("logged_in"):
    st.warning("AUTHENTICATION REQUIRED")
    st.page_link("pages/1_Login.py", label="▶ GO TO LOGIN")
    st.stop()

user = st.session_state["user"]

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
.bb-table-header { display: flex; background: var(--bg-hover); border-bottom: 1px solid var(--border-bright); padding: 6px 10px; font-size: 0.7rem; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: 0.5px; }
.bb-table-row { display: flex; border-bottom: 1px dotted var(--border); padding: 6px 10px; font-size: 0.78rem; transition: background 0.1s; }
.bb-table-row:hover { background: var(--bg-hover); }
.bb-table-row:last-child { border-bottom: none; }
.bb-table-cell { flex: 1; color: var(--text-dim); }
.bb-table-cell strong { color: var(--text); font-weight: 600; }
.bb-metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 1px; background: var(--border); border: 1px solid var(--border); }
.bb-metric-cell { background: var(--bg-panel); padding: 10px; text-align: center; }
.bb-metric-value { font-size: 1.2rem; font-weight: 700; color: var(--text); line-height: 1; }
.bb-metric-value.pos { color: var(--positive); }
.bb-metric-value.neg { color: var(--negative); }
.bb-metric-value.accent { color: var(--accent); }
.bb-metric-label { font-size: 0.6rem; color: var(--text-faded); text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }
.stButton > button { background: var(--accent) !important; color: var(--text-inverse) !important; border: none !important; border-radius: var(--radius-sm) !important; font-family: var(--font) !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; font-size: 0.75rem !important; }
.stButton > button:hover { background: var(--accent-dim) !important; box-shadow: 0 0 12px var(--accent-glow) !important; }
.stButton > button[kind="secondary"] { background: var(--bg-hover) !important; color: var(--text) !important; border: 1px solid var(--border) !important; }
.stSelectbox > div > div, .stTextInput > div > div, .stNumberInput > div > div, .stDateInput > div > div { background: var(--bg-input) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; color: var(--text) !important; }
.stTextInput > div > div > input, .stNumberInput > div > div > input { color: var(--text) !important; font-family: var(--font) !important; }
[data-testid="stMetric"] { background: var(--bg-panel) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; }
[data-testid="stMetricValue"] { font-family: var(--font) !important; font-weight: 700 !important; color: var(--text) !important; }
[data-testid="stMetricLabel"] { font-family: var(--font) !important; color: var(--text-dim) !important; text-transform: uppercase !important; font-size: 0.6rem !important; letter-spacing: 1px !important; }
.positive { color: var(--positive) !important; font-weight: 700; }
.negative { color: var(--negative) !important; font-weight: 700; }
@media (max-width: 768px) { .block-container { padding: 0.5rem !important; } }
</style>
""", unsafe_allow_html=True)

INDIAN_STOCKS = {
    "TCS": "TCS.NS", "INFY": "INFY.NS", "RELIANCE": "RELIANCE.NS", "WIPRO": "WIPRO.NS",
    "HDFCBANK": "HDFCBANK.NS", "ICICIBANK": "ICICIBANK.NS", "TATAMOTORS": "TATAMOTORS.NS",
    "BAJFINANCE": "BAJFINANCE.NS", "SBIN": "SBIN.NS", "AXISBANK": "AXISBANK.NS",
    "BHARTIARTL": "BHARTIARTL.NS", "ITC": "ITC.NS", "LT": "LT.NS", "MARUTI": "MARUTI.NS",
    "NESTLEIND": "NESTLEIND.NS", "TITAN": "TITAN.NS", "HINDUNILVR": "HINDUNILVR.NS",
    "KOTAKBANK": "KOTAKBANK.NS", "ASIANPAINT": "ASIANPAINT.NS", "ULTRACEMCO": "ULTRACEMCO.NS"
}
BLOCKED_TICKERS = {
    "INR", "USD", "EUR", "GBP", "JPY", "CNY", "AUD", "CAD", "CHF", "SEK", "NZD",
    "SGD", "HKD", "KRW", "MXN", "RUB", "ZAR", "TRY", "BRL", "BTC", "ETH", "GOLD",
    "SILVER", "OIL", "CRUDE", "NATGAS", "NG", "GC", "SI", "CL"
}

US_INDICES = {"SPX": "^GSPC", "NDX": "^IXIC", "DJI": "^DJI"}

def validate_ticker(ticker: str) -> tuple[bool, str]:
    t = ticker.strip().upper()
    if t in BLOCKED_TICKERS:
        return False, f"❌ {t} is a currency/commodity code, not a stock ticker. Use equity symbols only."
    return True, ""

def normalize_ticker(ticker: str):
    t = ticker.strip().upper()
    if t in INDIAN_STOCKS:
        return INDIAN_STOCKS[t], t, "IN"
    if t.endswith(".NS"):
        return t, t.replace(".NS", ""), "IN"
    return t, t, "US"

def get_current_price(yf_ticker: str):
    try:
        data = yf.Ticker(yf_ticker).history(period="2d")
        if not data.empty:
            return float(data["Close"].iloc[-1])
        return None
    except Exception:
        return None

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
    _render_nav("pages/2_Portfolio.py")
    st.markdown('</div>', unsafe_allow_html=True)
    if st.button("◀ LOGOUT", width='stretch'):
        for k in ["logged_in", "user", "current_portfolio", "results"]:
            st.session_state.pop(k, None)
        st.switch_page("app.py")
    st.markdown('<div class="bb-sidebar-footer">TERMINAL EDITION v5.0</div>', unsafe_allow_html=True)

st.markdown(f'<div class="bb-cmd-bar"><span class="bb-cmd-prompt">➜</span><span style="color:var(--text-dim);">PORTFOLIO MANAGEMENT // USER: {user["username"].upper()}</span></div>', unsafe_allow_html=True)
st.markdown('<div style="padding:12px 0;"><span style="font-size:1.4rem;font-weight:800;color:var(--text);letter-spacing:-1px;">◫ PORTFOLIO MANAGER</span><br><span style="font-size:0.8rem;color:var(--text-dim);">MANAGE HOLDINGS AND PREPARE FOR AI ANALYSIS</span></div>', unsafe_allow_html=True)

portfolios = get_user_portfolios(user["id"])

col_left, col_right = st.columns([3, 1], gap="small")

with col_right:
    st.markdown('<div class="bb-panel bb-panel-accent"><div class="bb-panel-header"><span class="bb-panel-title">+ New Portfolio</span></div><div class="bb-panel-body">', unsafe_allow_html=True)
    new_name = st.text_input("NAME", placeholder="e.g. TECH_PICKS_INDIA")
    new_desc = st.text_input("DESC", placeholder="OPTIONAL")
    new_curr = st.selectbox("CURRENCY", ["USD", "INR"])
    if st.button("+ CREATE", width='stretch'):
        if new_name:
            p = create_portfolio(user["id"], new_name, new_desc, new_curr)
            if p:
                st.success(f"CREATED: {new_name.upper()}")
                st.rerun()
        else:
            st.error("NAME REQUIRED")
    st.markdown('</div></div>', unsafe_allow_html=True)

with col_left:
    if not portfolios:
        st.markdown('<div class="bb-panel"><div class="bb-panel-body"><span style="color:var(--text-dim);">No portfolios found. Create one to begin.</span></div></div>', unsafe_allow_html=True)
        fc1, fc2, fc3 = st.columns(3)
        for col, icon, title, desc in [
            (fc1, "◫", "CREATE PORTFOLIO", "Name it and set currency"),
            (fc2, "+", "ADD HOLDINGS", "US or Indian tickers"),
            (fc3, "▣", "RUN ANALYSIS", "Sharpe + sentiment + LLM"),
        ]:
            col.markdown(f'<div style="background:var(--bg-panel);border:1px solid var(--border);padding:12px;text-align:center;min-height:120px"><div style="font-size:1.2rem;color:var(--accent);margin-bottom:4px">{icon}</div><b style="font-size:0.75rem;color:var(--text)">{title}</b><br><small style="color:var(--text-dim);font-size:0.65rem">{desc}</small></div>', unsafe_allow_html=True)
        st.stop()

    portfolio_names = [p["name"] for p in portfolios]
    selected_name = st.selectbox("SELECT PORTFOLIO", portfolio_names)
    selected_portfolio = next(p for p in portfolios if p["name"] == selected_name)
    st.session_state["current_portfolio"] = selected_portfolio

st.markdown(f'<div style="display:flex;align-items:center;gap:8px;margin:8px 0;"><span style="font-size:1rem;color:var(--accent);">◫</span><b style="font-size:0.9rem;color:var(--text)">{selected_portfolio["name"].upper()}</b><span style="background:var(--accent-soft);color:var(--accent);padding:1px 6px;font-size:0.6rem;font-weight:700;">{selected_portfolio["currency"]}</span></div>', unsafe_allow_html=True)

with st.expander("🗑 DELETE PORTFOLIO"):
    st.warning("PERMANENTLY DELETES ALL DATA")
    confirm = st.checkbox(f'CONFIRM DELETE "{selected_portfolio["name"].upper()}"')
    if st.button("🗑 DELETE", type="primary", disabled=not confirm):
        delete_portfolio(selected_portfolio["id"])
        st.session_state.pop("current_portfolio", None)
        st.success("PORTFOLIO DELETED")
        st.rerun()

st.markdown('<div class="bb-panel bb-panel-green"><div class="bb-panel-header"><span class="bb-panel-title">+ Add Holding</span></div><div class="bb-panel-body">', unsafe_allow_html=True)
with st.form("add_holding_form", clear_on_submit=True):
    fc1, fc2, fc3, fc4, fc5 = st.columns([2, 1.5, 1.5, 1.5, 2])
    ticker_input = fc1.text_input("TICKER", placeholder="AAPL or TCS")
    quantity = fc2.number_input("QTY", min_value=0.001, value=1.0, step=0.5)
    buy_price = fc3.number_input("BUY PRICE", min_value=0.01, value=100.0)
    buy_currency = fc4.selectbox("CURR", ["USD", "INR"])
    buy_date_val = fc5.date_input("DATE", value=date.today())
    submitted = st.form_submit_button("+ ADD HOLDING",   type="primary")
    if submitted:
        if not ticker_input:
            st.error("TICKER REQUIRED")
        else:
            valid, err_msg = validate_ticker(ticker_input)
            if not valid:
                st.error(err_msg)
            else:
                yf_ticker, display, exchange = normalize_ticker(ticker_input)
                result = add_holding(selected_portfolio["id"], yf_ticker, display, exchange, quantity, buy_price, buy_currency, datetime.combine(buy_date_val, datetime.min.time()))
                if result:
                    st.success(f"ADDED {display} ({yf_ticker}) — {quantity} @ {buy_currency} {buy_price:.2f}")
                    st.rerun()
                else:
                    st.error("FAILED TO ADD")
st.markdown('</div></div>', unsafe_allow_html=True)

holdings = get_portfolio_holdings(selected_portfolio["id"])

if not holdings:
    st.info("NO HOLDINGS — ADD STOCKS ABOVE")
    st.stop()

rows = []
total_invested = 0
total_current = 0
prices_map = {}

with st.spinner("FETCHING PRICES..."):
    for h in holdings:
        current_price = get_current_price(h["ticker"])
        prices_map[h["ticker"]] = current_price
        invested = h["quantity"] * h["buy_price"]
        current_val = h["quantity"] * current_price if current_price else invested
        pnl = current_val - invested
        pnl_pct = (pnl / invested * 100) if invested > 0 else 0
        total_invested += invested
        total_current += current_val
        rows.append({
            "Ticker": h["display_name"], "Exchange": h["exchange"], "Qty": h["quantity"],
            "Buy Price": f"{h['buy_currency']} {h['buy_price']:.2f}",
            "Current Price": f"{current_price:.2f}" if current_price else "N/A",
            "Invested": invested, "Current Value": current_val if current_price else invested,
            "P&L": pnl, "P&L %": pnl_pct, "Buy Date": h["buy_date"], "_id": h["id"]
        })

total_pnl = total_current - total_invested
total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0

st.markdown('<div class="bb-panel"><div class="bb-panel-header"><span class="bb-panel-title">◈ Current Holdings</span><span class="bb-panel-subtitle">{0} POSITIONS</span></div><div class="bb-panel-body">'.format(len(rows)), unsafe_allow_html=True)

h1, h2, h3, h4, h5, h6, h7 = st.columns([2.2, 1, 1.4, 1.3, 1.4, 1.6, 0.6])
h1.markdown("**TICKER**"); h2.markdown("**QTY**"); h3.markdown("**BUY**"); h4.markdown("**CURRENT**"); h5.markdown("**VALUE**"); h6.markdown("**P&L**"); h7.markdown("**DEL**")
st.divider()

for row in rows:
    color = "var(--positive)" if row["P&L"] >= 0 else "var(--negative)"
    flag = "🇮🇳" if row["Exchange"] == "IN" else "🇺🇸"
    c1, c2, c3, c4, c5, c6, c7 = st.columns([2.2, 1, 1.4, 1.3, 1.4, 1.6, 0.6])
    c1.markdown(f"**{flag} {row['Ticker']}**")
    c2.write(f"{row['Qty']:.2f}")
    c3.write(row["Buy Price"])
    c4.write(row["Current Price"])
    c5.write(f"{row['Current Value']:,.0f}")
    c6.markdown(f'<span style="color:{color};font-weight:700;">{row["P&L"]:+.0f} ({row["P&L %"]:+.1f}%)</span>', unsafe_allow_html=True)
    if c7.button("×", key=f"del_{row['_id']}"):
        delete_holding(row["_id"])
        st.rerun()
    st.divider()

total_qty = sum(r["Qty"] for r in rows)
total_buy = sum(h["quantity"] * h["buy_price"] for h in holdings)
total_value = sum(r["Current Value"] for r in rows)
total_pnl = total_value - total_buy
total_pnl_pct = (total_pnl / total_buy * 100) if total_buy > 0 else 0
color = "var(--positive)" if total_pnl >= 0 else "var(--negative)"

tc1, tc2, tc3, tc4, tc5, tc6, tc7 = st.columns([2.2, 1, 1.4, 1.3, 1.4, 1.6, 0.6])
tc1.markdown("### **TOTAL**")
tc2.markdown(f"### **{total_qty:.2f}**")
tc3.markdown(f"### **${total_buy:,.2f}**")
tc4.markdown("### **—**")
tc5.markdown(f"### **${total_value:,.2f}**")
tc6.markdown(f'<div style="color:{color};font-size:20px;font-weight:800;text-align:center;">${total_pnl:,.2f}<div style="font-size:14px">({total_pnl_pct:+.2f}%)</div></div>', unsafe_allow_html=True)
tc7.markdown("")
st.markdown('</div></div>', unsafe_allow_html=True)

if rows:
    st.markdown('<div class="bb-panel bb-panel-accent"><div class="bb-panel-header"><span class="bb-panel-title">◫ Allocation</span></div><div class="bb-panel-body">', unsafe_allow_html=True)
    alloc_df = {"Ticker": [r["Ticker"] for r in rows], "Value": [r["Current Value"] for r in rows]}
    fig = px.pie(alloc_df, values="Value", names="Ticker", hole=0.55, color_discrete_sequence=["#ff6600", "#cc5200", "#ff8533", "#ffaa66", "#2e75b6", "#1f4e79", "#00d084", "#ff3333"])
    fig.update_layout(
        showlegend=True, margin=dict(t=10, b=10, l=10, r=10), height=300,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono, monospace", color="#e5e5e5", size=11),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#2a2a2a", borderwidth=1)
    )
    st.plotly_chart(fig, width='stretch')
    st.markdown('</div></div>', unsafe_allow_html=True)

st.info(f"**{len(rows)} TICKERS READY:** {', '.join([r['Ticker'] for r in rows])}")
if st.button("▣ GO TO ANALYSIS →",   type="primary"):
    st.switch_page("pages/3_Analysis.py")

st.markdown("---")
st.caption("AI PORTFOLIO OPTIMIZER | Terminal Edition")
