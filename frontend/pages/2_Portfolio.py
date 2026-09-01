"""
Axiom Portfolio Manager v2.0
Holdings management with institutional terminal aesthetic.
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import yfinance as yf
from datetime import datetime, date
import plotly.express as px
from src.database.db import get_user_portfolios, create_portfolio, delete_portfolio, get_portfolio_holdings, add_holding, delete_holding

st.set_page_config(page_title="Portfolio | Axiom", page_icon="◫", layout="wide")

if not st.session_state.get("logged_in"):
    st.warning("Authentication required")
    st.page_link("pages/1_Login.py", label="▶ Go to Login")
    st.stop()

user = st.session_state["user"]

from frontend.ui.theme import inject_theme, apply_plotly_theme
from frontend.ui.components import (
    sidebar_brand, sidebar_user, sidebar_nav_item, command_bar,
    section_header, metric_grid, badge, info_card, glass_panel
)
inject_theme()

# ── Constants ───────────────────────────────────────────────
INDIAN_STOCKS = {
    "TCS": "TCS.NS", "INFY": "INFY.NS", "RELIANCE": "RELIANCE.NS",
    "WIPRO": "WIPRO.NS", "HDFCBANK": "HDFCBANK.NS", "ICICIBANK": "ICICIBANK.NS",
    "TATAMOTORS": "TATAMOTORS.NS", "BAJFINANCE": "BAJFINANCE.NS",
    "SBIN": "SBIN.NS", "AXISBANK": "AXISBANK.NS", "BHARTIARTL": "BHARTIARTL.NS",
    "ITC": "ITC.NS", "LT": "LT.NS", "MARUTI": "MARUTI.NS",
    "NESTLEIND": "NESTLEIND.NS", "TITAN": "TITAN.NS", "HINDUNILVR": "HINDUNILVR.NS",
    "KOTAKBANK": "KOTAKBANK.NS", "ASIANPAINT": "ASIANPAINT.NS", "ULTRACEMCO": "ULTRACEMCO.NS"
}
BLOCKED_TICKERS = {"INR", "USD", "EUR", "GBP", "JPY", "CNY", "AUD", "CAD", "CHF", "BTC", "ETH", "GOLD", "SILVER", "OIL", "CRUDE"}

def validate_ticker(ticker: str) -> tuple[bool, str]:
    t = ticker.strip().upper()
    if t in BLOCKED_TICKERS:
        return False, f"❌ {t} is not an equity ticker."
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
    except Exception:
        pass
    return None

# ── Sidebar ─────────────────────────────────────────────────
with st.sidebar:
    sidebar_brand()
    sidebar_user(user.get("username", "User"), "Portfolio Manager")
    
    st.markdown("""
    <div style="padding: 0 16px; margin: 12px 0;">
        <div style="font-size:0.6rem;color:#4a4a5e;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">
            Navigation
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    pages = [
        ("app.py", "◈", "Dashboard"), ("pages/2_Portfolio.py", "◫", "Portfolio"),
        ("pages/3_Analysis.py", "▣", "Analysis"), ("pages/4_History.py", "◫", "History"),
        ("pages/5_Compare.py", "⚖", "Benchmark")
    ]
    for page, icon, label in pages:
        is_active = page == "pages/2_Portfolio.py"
        if is_active:
            st.markdown(sidebar_nav_item(label, icon, active=True), unsafe_allow_html=True)
        else:
            st.page_link(page, label=f"{icon}  {label}", width='stretch')
    
    st.markdown("<div style='border-top:1px solid rgba(255,255,255,0.06);margin:12px 0;'></div>", unsafe_allow_html=True)
    if st.button("◀ Logout", key="logout_portfolio"):
        for k in ["logged_in", "user", "current_portfolio", "results"]:
            st.session_state.pop(k, None)
        st.switch_page("app.py")
    
    st.markdown("""
    <div style="padding: 12px 16px; margin-top: auto; border-top: 1px solid rgba(255,255,255,0.06);">
        <div style="font-size:0.6rem;color:#4a4a5e;text-align:center;letter-spacing:0.05em;">
            AXIOM v2.0 · Portfolio Intelligence
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Command Bar ─────────────────────────────────────────────
command_bar("AXIOM / PORTFOLIO", f"USER: {user['username'].upper()}")

st.markdown("""
<div style="padding: 20px 0 12px;">
    <div style="font-size:1.6rem;font-weight:800;color:#f0f0f5;letter-spacing:-0.03em;font-family:'Inter',sans-serif;">
        Portfolio Manager
    </div>
    <div style="font-size:0.85rem;color:#8b8b9e;margin-top:6px;">
        Manage holdings and prepare for quantitative analysis
    </div>
</div>
""", unsafe_allow_html=True)

portfolios = get_user_portfolios(user["id"])

# ── Layout ──────────────────────────────────────────────────
col_left, col_right = st.columns([3, 1], gap="small")

with col_right:
    section_header("+ New Portfolio", "Create workspace", accent="green")
    st.markdown("""
    <div style="
        background: rgba(18,18,26,0.72);
        border: 1px solid rgba(255,255,255,0.06);
        border-top: 2px solid #10B981;
        border-radius: 12px;
        backdrop-filter: blur(20px);
        padding: 16px;
    ">
    """, unsafe_allow_html=True)
    new_name = st.text_input("NAME", placeholder="e.g. TECH_PICKS_INDIA", key="new_pf_name")
    new_desc = st.text_input("DESCRIPTION", placeholder="Optional", key="new_pf_desc")
    new_curr = st.selectbox("CURRENCY", ["USD", "INR"], key="new_pf_curr")
    if st.button("+ CREATE", use_container_width=True, type="primary"):
        if new_name:
            p = create_portfolio(user["id"], new_name, new_desc, new_curr)
            if p:
                st.success(f"Created: {new_name.upper()}")
                st.rerun()
        else:
            st.error("Name required")
    st.markdown("</div>", unsafe_allow_html=True)

with col_left:
    if not portfolios:
        info_card(
            "No Portfolios Found",
            "Create a portfolio workspace to begin tracking holdings and running AI analysis.",
            badge("START HERE", tone="positive"),
            accent="cyan"
        )
        st.stop()
    
    portfolio_names = [p["name"] for p in portfolios]
    selected_name = st.selectbox("SELECT PORTFOLIO", portfolio_names, key="sel_pf")
    selected_portfolio = next(p for p in portfolios if p["name"] == selected_name)
    st.session_state["current_portfolio"] = selected_portfolio

# ── Portfolio Header ────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin:16px 0;">
    <span style="font-size:1.1rem;color:#FF6B35;">◫</span>
    <strong style="font-size:0.95rem;color:#f0f0f5;font-family:'Inter',sans-serif;">{selected_portfolio['name'].upper()}</strong>
    <span style="background:rgba(255,107,53,0.12);color:#FF6B35;padding:2px 8px;border-radius:6px;font-size:0.6rem;font-weight:700;letter-spacing:0.04em;">{selected_portfolio['currency']}</span>
</div>
""", unsafe_allow_html=True)

with st.expander("🗑 Delete Portfolio"):
    st.warning("Permanently deletes all holdings and history")
    confirm = st.checkbox(f'Confirm delete "{selected_portfolio["name"].upper()}"', key="del_confirm")
    if st.button("🗑 DELETE", type="primary", disabled=not confirm, use_container_width=True):
        delete_portfolio(selected_portfolio["id"])
        st.session_state.pop("current_portfolio", None)
        st.success("Portfolio deleted")
        st.rerun()

# ── Add Holding ─────────────────────────────────────────────
section_header("+ Add Holding", "Position entry", accent="primary")
st.markdown("""
<div style="
    background: rgba(18,18,26,0.72);
    border: 1px solid rgba(255,255,255,0.06);
    border-top: 2px solid #FF6B35;
    border-radius: 12px;
    backdrop-filter: blur(20px);
    padding: 16px;
    margin-bottom: 16px;
">
""", unsafe_allow_html=True)

with st.form("add_holding_form", clear_on_submit=True):
    fc1, fc2, fc3, fc4, fc5 = st.columns([2, 1.5, 1.5, 1.5, 2])
    ticker_input = fc1.text_input("TICKER", placeholder="AAPL or TCS", key="add_ticker")
    quantity = fc2.number_input("QTY", min_value=0.001, value=1.0, step=0.5, key="add_qty")
    buy_price = fc3.number_input("BUY PRICE", min_value=0.01, value=100.0, key="add_price")
    buy_currency = fc4.selectbox("CURR", ["USD", "INR"], key="add_curr")
    buy_date_val = fc5.date_input("DATE", value=date.today(), key="add_date")
    
    submitted = st.form_submit_button("+ ADD HOLDING", use_container_width=True)
    if submitted:
        if not ticker_input:
            st.error("Ticker required")
        else:
            valid, err_msg = validate_ticker(ticker_input)
            if not valid:
                st.error(err_msg)
            else:
                yf_ticker, display, exchange = normalize_ticker(ticker_input)
                result = add_holding(
                    selected_portfolio["id"], yf_ticker, display, exchange,
                    quantity, buy_price, buy_currency,
                    datetime.combine(buy_date_val, datetime.min.time())
                )
                if result:
                    st.success(f"Added {display} ({yf_ticker}) — {quantity} @ {buy_currency} {buy_price:.2f}")
                    st.rerun()
                else:
                    st.error("Failed to add")
st.markdown("</div>", unsafe_allow_html=True)

# ── Holdings Table ──────────────────────────────────────────
holdings = get_portfolio_holdings(selected_portfolio["id"])

if not holdings:
    info_card("No Holdings", "Add stocks above to begin tracking.", badge_html="", accent="warning")
    st.stop()

rows = []
total_invested = 0
total_current = 0
prices_map = {}

with st.spinner("Fetching prices..."):
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

section_header("Current Holdings", f"{len(rows)} positions", accent="cyan")

st.markdown("""
<div style="
    background: rgba(18,18,26,0.72);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    backdrop-filter: blur(20px);
    overflow: hidden;
    margin-bottom: 16px;
">
""", unsafe_allow_html=True)

# Table Header
st.markdown("""
<div style="display:flex;background:rgba(255,255,255,0.02);border-bottom:1px solid rgba(255,255,255,0.06);padding:10px 12px;font-size:0.6rem;font-weight:700;color:#FF6B35;text-transform:uppercase;letter-spacing:0.08em;font-family:'Inter',sans-serif;">
    <div style="flex:2.2;">TICKER</div>
    <div style="flex:1;">QTY</div>
    <div style="flex:1.4;">BUY</div>
    <div style="flex:1.3;">CURRENT</div>
    <div style="flex:1.4;">VALUE</div>
    <div style="flex:1.6;">P&L</div>
    <div style="flex:0.6;">DEL</div>
</div>
""", unsafe_allow_html=True)

for row in rows:
    color = "#10B981" if row["P&L"] >= 0 else "#F43F5E"
    flag = "🇮🇳" if row["Exchange"] == "IN" else "🇺🇸"
    
    c1, c2, c3, c4, c5, c6, c7 = st.columns([2.2, 1, 1.4, 1.3, 1.4, 1.6, 0.6])
    c1.markdown(f"<span style='color:#f0f0f5;font-weight:600;'>{flag} {row['Ticker']}</span>", unsafe_allow_html=True)
    c2.write(f"<span style='color:#8b8b9e;font-family:JetBrains Mono;'>{row['Qty']:.2f}</span>", unsafe_allow_html=True)
    c3.write(f"<span style='color:#8b8b9e;font-family:JetBrains Mono;'>{row['Buy Price']}</span>", unsafe_allow_html=True)
    c4.write(f"<span style='color:#8b8b9e;font-family:JetBrains Mono;'>{row['Current Price']}</span>", unsafe_allow_html=True)
    c5.write(f"<span style='color:#f0f0f5;font-family:JetBrains Mono;font-weight:600;'>{row['Current Value']:,.0f}</span>", unsafe_allow_html=True)
    c6.markdown(f"<span style='color:{color};font-weight:700;font-family:JetBrains Mono;'>{row['P&L']:+.0f} ({row['P&L %']:+.1f}%)</span>", unsafe_allow_html=True)
    if c7.button("×", key=f"del_{row['_id']}"):
        delete_holding(row["_id"])
        st.rerun()

# Total Row
st.markdown("<div style='border-top:1px solid rgba(255,255,255,0.08);margin:8px 0;'></div>", unsafe_allow_html=True)
total_color = "#10B981" if total_pnl >= 0 else "#F43F5E"
st.markdown(f"""
<div style="display:flex;padding:10px 12px;align-items:center;">
    <div style="flex:2.2;"><strong style="color:#f0f0f5;font-size:0.9rem;">TOTAL</strong></div>
    <div style="flex:1;"><strong style="color:#f0f0f5;font-family:JetBrains Mono;">{sum(r['Qty'] for r in rows):.2f}</strong></div>
    <div style="flex:1.4;"><strong style="color:#f0f0f5;font-family:JetBrains Mono;">${total_invested:,.2f}</strong></div>
    <div style="flex:1.3;"><span style="color:#4a4a5e;">—</span></div>
    <div style="flex:1.4;"><strong style="color:#f0f0f5;font-family:JetBrains Mono;">${total_current:,.2f}</strong></div>
    <div style="flex:1.6;">
        <div style="color:{total_color};font-size:1.1rem;font-weight:800;font-family:JetBrains Mono;text-align:center;">
            ${total_pnl:,.2f}
            <div style="font-size:0.75rem;">({total_pnl_pct:+.2f}%)</div>
        </div>
    </div>
    <div style="flex:0.6;"></div>
</div>
""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ── Allocation Chart ────────────────────────────────────────
if rows:
    section_header("Allocation", "Current weight distribution", accent="violet")
    st.markdown("""
    <div style="
        background: rgba(18,18,26,0.72);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        backdrop-filter: blur(20px);
        padding: 16px;
    ">
    """, unsafe_allow_html=True)
    
    alloc_df = {"Ticker": [r["Ticker"] for r in rows], "Value": [r["Current Value"] for r in rows]}
    fig = px.pie(
        alloc_df, values="Value", names="Ticker", hole=0.55,
        color_discrete_sequence=["#FF6B35", "#00D9FF", "#8B5CF6", "#10B981", "#F43F5E", "#F59E0B", "#EC4899", "#6366F1"]
    )
    fig.update_layout(
        showlegend=True, margin=dict(t=10, b=10, l=10, r=10), height=320,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono, monospace", color="#f0f0f5", size=11),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(255,255,255,0.06)", borderwidth=1)
    )
    st.plotly_chart(fig, width='stretch')
    st.markdown("</div>", unsafe_allow_html=True)

st.info(f"**{len(rows)} tickers ready:** {', '.join([r['Ticker'] for r in rows])}")
if st.button("▣ Go to Analysis →", type="primary", use_container_width=True):
    st.switch_page("pages/3_Analysis.py")

st.markdown("""
<div style="border-top:1px solid rgba(255,255,255,0.06);margin-top:32px;padding-top:16px;">
    <div style="font-size:0.65rem;color:#4a4a5e;text-align:center;letter-spacing:0.05em;">
        AXIOM Portfolio Intelligence · Terminal Edition
    </div>
</div>
""", unsafe_allow_html=True)