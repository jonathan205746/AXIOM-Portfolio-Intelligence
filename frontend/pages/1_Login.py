"""
frontend/pages/1_Login.py  (Bloomberg Terminal Edition)
--------------------------------------------------------
Authentication with terminal aesthetic.
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from src.database.db import create_user, get_user, create_portfolio, reset_password

st.set_page_config(page_title="AUTH | AI Portfolio Optimizer", page_icon="🔐", layout="wide")

# ── INJECT CSS ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700;800&display=swap');
:root {
  --bg: #050505; --bg-panel: #0a0a0a; --bg-hover: #141414; --bg-input: #0d0d0d;
  --text: #e5e5e5; --text-dim: #888888; --text-faded: #555555; --text-inverse: #050505;
  --accent: #ff6600; --accent-dim: #cc5200; --accent-glow: rgba(255,102,0,0.25); --accent-soft: rgba(255,102,0,0.1);
  --positive: #00d084; --negative: #ff3333; --border: #2a2a2a; --border-bright: #3a3a3a;
  --font: 'JetBrains Mono','Courier New',monospace; --radius: 0px; --radius-sm: 2px;
}
<link href="https://fonts.googleapis.com/icon?family=Material+Icons"
      rel="stylesheet">
* { font-family: var(--font) !important; }

.block-container { padding: 0.5rem 1rem 1rem !important; max-width: 100% !important; }
[data-testid="stAppViewContainer"] { background: var(--bg) !important; }
[data-testid="stSidebarNav"] { display: none !important; }
[data-testid="stSidebar"] { background: var(--bg-panel) !important; border-right: 1px solid var(--border) !important; min-width: 280px !important; }
.bb-sidebar-header { background: linear-gradient(90deg, var(--accent), var(--accent-dim)); padding: 12px 16px; border-bottom: 1px solid var(--border); }
.bb-sidebar-header h1 { color: var(--text-inverse) !important; font-size: 0.85rem !important; font-weight: 800 !important; letter-spacing: 1px; margin: 0; }
.bb-section { padding: 8px 16px; border-bottom: 1px solid var(--border); }
.bb-section-title { font-size: 0.6rem; font-weight: 700; color: var(--accent) !important; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px; }
.bb-ticker-row { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; font-size: 0.75rem; border-bottom: 1px dotted var(--border); }
.bb-ticker-symbol { color: var(--text); font-weight: 600; }
.bb-ticker-price { color: var(--text-dim); }
.bb-ticker-change-pos { color: var(--positive); font-weight: 700; }
.bb-ticker-change-neg { color: var(--negative); font-weight: 700; }
.bb-nav-item { display: flex; align-items: center; gap: 10px; padding: 8px 12px; margin: 2px 0; border-left: 3px solid transparent; color: var(--text-dim) !important; font-size: 0.8rem; font-weight: 500; text-decoration: none !important; transition: all 0.15s; cursor: pointer; }
.bb-nav-item:hover { background: var(--bg-hover); border-left-color: var(--accent-dim); color: var(--text) !important; }
.bb-nav-item.active { background: var(--accent-soft); border-left-color: var(--accent); color: var(--accent) !important; font-weight: 700; }
.bb-sidebar-footer { padding: 10px 16px; font-size: 0.6rem; color: var(--text-faded); border-top: 1px solid var(--border); text-align: center; }
.bb-cmd-bar { background: var(--bg-panel); border-bottom: 1px solid var(--border); padding: 8px 16px; display: flex; align-items: center; gap: 12px; font-size: 0.8rem; margin-bottom: 1px; }
.bb-cmd-prompt { color: var(--accent); font-weight: 700; }
.bb-panel { background: var(--bg-panel); border: 1px solid var(--border); margin-bottom: 1px; }
.bb-panel-header { background: var(--bg-hover); border-bottom: 1px solid var(--border); padding: 8px 12px; }
.bb-panel-title { font-size: 0.75rem; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: 1px; }
.bb-panel-body { padding: 16px; }
.bb-panel-accent { border-top: 2px solid var(--accent); }
.stButton > button { background: var(--accent) !important; color: var(--text-inverse) !important; border: none !important; border-radius: var(--radius-sm) !important; font-family: var(--font) !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; font-size: 0.75rem !important; }
.stButton > button:hover { background: var(--accent-dim) !important; box-shadow: 0 0 12px var(--accent-glow) !important; }
.stTextInput > div > div { background: var(--bg-input) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; }
.stTextInput > div > div > input { color: var(--text) !important; font-family: var(--font) !important; }
.stTabs [data-baseweb="tab-list"] { gap: 0 !important; border-bottom: 1px solid var(--border) !important; background: var(--bg-panel) !important; }
.stTabs [data-baseweb="tab"] { border-radius: 0 !important; padding: 10px 16px !important; font-weight: 600 !important; font-size: 0.75rem !important; color: var(--text-dim) !important; border: none !important; text-transform: uppercase; }
.stTabs [data-baseweb="tab-highlight"] { background: var(--accent) !important; height: 2px !important; }
.stTabs [aria-selected="true"] { color: var(--accent) !important; background: var(--accent-soft) !important; }
.strength-weak { color: var(--negative); font-weight: 700; font-size: 0.8rem; }
.strength-medium { color: #f59e0b; font-weight: 700; font-size: 0.8rem; }
.strength-strong { color: var(--positive); font-weight: 700; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

if st.session_state.get("logged_in"):
    st.markdown(f'<div class="bb-panel bb-panel-accent"><div class="bb-panel-body"><span style="color:var(--positive);font-weight:700;">✓ AUTHENTICATED</span> <span style="color:var(--text-dim)">as {st.session_state["user"]["username"].upper()}</span></div></div>', unsafe_allow_html=True)
    if st.button("◫ GO TO PORTFOLIO →", type="primary"):
        st.switch_page("pages/2_Portfolio.py")
    st.stop()

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

with st.sidebar:
    st.markdown('<div class="bb-sidebar-header"><h1>▶ AI PORTFOLIO OPTIMIZER</h1></div>', unsafe_allow_html=True)
    st.markdown('<div class="bb-section"><div class="bb-section-title">Market Data</div>', unsafe_allow_html=True)
    for name, data in market_data.items():
        cls = "bb-ticker-change-pos" if data["change"] >= 0 else "bb-ticker-change-neg"
        sign = "+" if data["change"] >= 0 else ""
        st.markdown(f'<div class="bb-ticker-row"><span class="bb-ticker-symbol">{name}</span><div><span class="bb-ticker-price">{data["price"]:,.2f}</span> <span class="{cls}">{sign}{data["change"]:.2f}%</span></div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="bb-section"><div class="bb-section-title">Account</div><div class="bb-nav-item active">🔐 LOGIN / REGISTER</div><p style="font-size:0.7rem;color:var(--text-faded);margin-top:8px;">Sign in to save portfolios and unlock AI analytics.</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="bb-sidebar-footer">TERMINAL EDITION v5.0</div>', unsafe_allow_html=True)

st.markdown('<div class="bb-cmd-bar"><span class="bb-cmd-prompt">➜</span><span style="color:var(--text-dim);">AUTHENTICATION MODULE</span></div>', unsafe_allow_html=True)
st.markdown('<div style="padding:16px 0;"><span style="font-size:1.4rem;font-weight:800;color:var(--text);letter-spacing:-1px;">🔐 SECURE ACCESS</span><br><span style="font-size:0.8rem;color:var(--text-dim);">AUTHENTICATE TO ACCESS PORTFOLIO SYSTEMS</span></div>', unsafe_allow_html=True)

tab_login, tab_register, tab_forgot = st.tabs(["▶ LOGIN", "+ REGISTER", "? RESET"])

with tab_login:
    st.markdown('<div class="bb-panel bb-panel-accent"><div class="bb-panel-header"><span class="bb-panel-title">▶ Existing User</span></div><div class="bb-panel-body">', unsafe_allow_html=True)
    username = st.text_input("USERNAME", key="login_username", placeholder="enter_username")
    password = st.text_input("PASSWORD", type="password", key="login_password", placeholder="enter_password")
    if st.button("▶ AUTHENTICATE", type="primary"):
        if not username or not password:
            st.error("CREDENTIALS REQUIRED")
        else:
            user = get_user(username.strip(), password)
            if user:
                st.session_state["logged_in"] = True
                st.session_state["user"] = user
                st.session_state.pop("current_portfolio", None)
                st.success(f"WELCOME BACK, {user['username'].upper()}")
                st.switch_page("pages/2_Portfolio.py")
            else:
                st.error("INVALID CREDENTIALS")
    st.markdown('</div></div>', unsafe_allow_html=True)

with tab_register:
    st.markdown('<div class="bb-panel bb-panel-green"><div class="bb-panel-header"><span class="bb-panel-title">+ New Account</span></div><div class="bb-panel-body">', unsafe_allow_html=True)
    new_username = st.text_input("USERNAME", key="reg_username", placeholder="min_3_chars")
    new_email = st.text_input("EMAIL", key="reg_email", placeholder="user@domain.com")
    new_password = st.text_input("PASSWORD", type="password", key="reg_password", placeholder="min_6_chars")
    confirm_pass = st.text_input("CONFIRM", type="password", key="reg_confirm", placeholder="re_enter")
    if new_password:
        score = sum([len(new_password) >= 8, any(c.isdigit() for c in new_password), any(c.isupper() for c in new_password), any(not c.isalnum() for c in new_password)])
        label, css_class = [("WEAK — ADD LENGTH+NUMBER+SYMBOL", "strength-weak"), ("WEAK — ADD LENGTH+NUMBER+SYMBOL", "strength-weak"), ("MEDIUM — ADD UPPERCASE/SYMBOL", "strength-medium"), ("STRONG", "strength-strong"), ("STRONG", "strength-strong")][score]
        st.markdown(f'<span class="{css_class}">{label}</span>', unsafe_allow_html=True)
    if st.button("+ CREATE ACCOUNT",  type="primary"):
        if not new_username or not new_password:
            st.error("USERNAME AND PASSWORD REQUIRED")
        elif not new_email or not new_email.strip():
            st.error("EMAIL REQUIRED FOR RECOVERY")
        elif len(new_username) < 3:
            st.error("USERNAME: MIN 3 CHARACTERS")
        elif len(new_password) < 6:
            st.error("PASSWORD: MIN 6 CHARACTERS")
        elif new_password != confirm_pass:
            st.error("PASSWORDS DO NOT MATCH")
        else:
            user = create_user(new_username.strip(), new_email.strip(), new_password)
            if user:
                create_portfolio(user["id"], "My Portfolio", "Default portfolio")
                st.session_state["logged_in"] = True
                st.session_state["user"] = user
                st.success("ACCOUNT CREATED — REDIRECTING...")
                st.switch_page("pages/2_Portfolio.py")
            else:
                st.error("USERNAME ALREADY EXISTS")
    st.markdown('</div></div>', unsafe_allow_html=True)

with tab_forgot:
    st.markdown('<div class="bb-panel bb-panel-red"><div class="bb-panel-header"><span class="bb-panel-title">? Password Reset</span></div><div class="bb-panel-body">', unsafe_allow_html=True)
    st.caption("VERIFY IDENTITY TO RESET PASSWORD")
    fp_username = st.text_input("USERNAME", key="fp_username", placeholder="your_username")
    fp_email = st.text_input("EMAIL", key="fp_email", placeholder="email_on_file")
    if st.button("? VERIFY"  ):
        if not fp_username or not fp_email:
            st.error("BOTH FIELDS REQUIRED")
        else:
            from src.database.db import verify_identity
            if verify_identity(fp_username.strip(), fp_email.strip()):
                st.session_state["fp_verified"] = True
                st.session_state["fp_verified_username"] = fp_username.strip()
                st.session_state["fp_verified_email"] = fp_email.strip()
                st.success("IDENTITY VERIFIED")
            else:
                st.session_state["fp_verified"] = False
                st.error("NO MATCHING ACCOUNT")
    if st.session_state.get("fp_verified"):
        st.markdown("---")
        new_pw = st.text_input("NEW PASSWORD", type="password", key="fp_new_password", placeholder="min_6_chars")
        confirm_pw = st.text_input("CONFIRM NEW", type="password", key="fp_confirm_password", placeholder="re_enter")
        if st.button("▶ RESET PASSWORD", type="primary"):
            if not new_pw or len(new_pw) < 6:
                st.error("PASSWORD: MIN 6 CHARACTERS")
            elif new_pw != confirm_pw:
                st.error("PASSWORDS DO NOT MATCH")
            else:
                ok = reset_password(st.session_state["fp_verified_username"], st.session_state["fp_verified_email"], new_pw)
                if ok:
                    for key in ["fp_verified", "fp_verified_username", "fp_verified_email"]:
                        st.session_state.pop(key, None)
                    st.success("PASSWORD RESET — LOGIN WITH NEW CREDENTIALS")
                else:
                    st.error("RESET FAILED")
    st.markdown('</div></div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("AI PORTFOLIO OPTIMIZER | Terminal Edition | Built by Parmod")
