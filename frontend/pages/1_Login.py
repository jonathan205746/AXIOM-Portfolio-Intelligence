"""
Axiom Authentication v2.0
Secure access with glassmorphic terminal aesthetic.
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from src.database.db import create_user, get_user, create_portfolio, reset_password, init_db

init_db()

st.set_page_config(page_title="Authenticate | Axiom", page_icon="🔐", layout="wide")

from frontend.ui.theme import inject_theme
from frontend.ui.components import (
    sidebar_brand, sidebar_nav_item, command_bar, 
    section_header, info_card, badge
)
inject_theme()

# ── Sidebar ─────────────────────────────────────────────────
with st.sidebar:
    sidebar_brand()
    st.markdown("""
    <div style="padding: 0 16px; margin: 12px 0;">
        <div style="font-size:0.6rem;color:#4a4a5e;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px;">
            Account
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(sidebar_nav_item("Authenticate", "🔐", active=True), unsafe_allow_html=True)
    st.markdown("""
    <div style="padding: 8px 16px; font-size: 0.7rem; color: #4a4a5e; line-height: 1.5;">
        Secure terminal access for portfolio analytics.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style="padding: 12px 16px; margin-top: auto; border-top: 1px solid rgba(255,255,255,0.06);">
        <div style="font-size:0.6rem;color:#4a4a5e;text-align:center;letter-spacing:0.05em;">
            AXIOM v2.0 · Portfolio Intelligence
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Auth Check ──────────────────────────────────────────────
if st.session_state.get("logged_in"):
    st.markdown("""
    <div style="
        background: rgba(16,185,129,0.08);
        border: 1px solid rgba(16,185,129,0.2);
        border-radius: 12px;
        padding: 16px;
        margin: 16px 0;
        backdrop-filter: blur(20px);
    ">
        <div style="color:#10B981;font-weight:700;font-size:0.9rem;margin-bottom:4px;">✓ AUTHENTICATED</div>
        <div style="color:#8b8b9e;font-size:0.8rem;">Session active for <strong style="color:#f0f0f5;">{}</strong></div>
    </div>
    """.format(st.session_state["user"]["username"].upper()), unsafe_allow_html=True)
    if st.button("◫ Go to Dashboard →", type="primary", use_container_width=True):
        st.switch_page("app.py")
    st.stop()

# ── Command Bar ─────────────────────────────────────────────
command_bar("AXIOM / AUTH", "IDENTITY VERIFICATION")

st.markdown("""
<div style="padding: 20px 0 12px;">
    <div style="font-size:1.6rem;font-weight:800;color:#f0f0f5;letter-spacing:-0.03em;font-family:'Inter',sans-serif;">
        Secure Access
    </div>
    <div style="font-size:0.85rem;color:#8b8b9e;margin-top:6px;">
        Authenticate to unlock portfolio systems and AI analytics
    </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ────────────────────────────────────────────────────
tab_login, tab_register, tab_forgot = st.tabs(["▶ LOGIN", "+ REGISTER", "? RESET"])

with tab_login:
    st.markdown("""
    <div style="
        background: rgba(18,18,26,0.72);
        border: 1px solid rgba(255,255,255,0.06);
        border-top: 2px solid #FF6B35;
        border-radius: 12px;
        backdrop-filter: blur(20px);
        padding: 20px;
        margin-bottom: 12px;
    ">
        <div style="font-size:0.75rem;font-weight:700;color:#FF6B35;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:16px;">
            ▶ Existing User
        </div>
    """, unsafe_allow_html=True)
    
    username = st.text_input("USERNAME", key="login_username", placeholder="enter_username")
    password = st.text_input("PASSWORD", type="password", key="login_password", placeholder="enter_password")
    
    if st.button("▶ AUTHENTICATE", type="primary", use_container_width=True):
        if not username or not password:
            st.error("Credentials required")
        else:
            user = get_user(username.strip(), password)
            if user:
                st.session_state["logged_in"] = True
                st.session_state["user"] = user
                st.session_state.pop("current_portfolio", None)
                st.success(f"Welcome back, {user['username'].upper()}")
                st.switch_page("app.py")
            else:
                st.error("Invalid credentials")
    st.markdown("</div>", unsafe_allow_html=True)

with tab_register:
    st.markdown("""
    <div style="
        background: rgba(18,18,26,0.72);
        border: 1px solid rgba(255,255,255,0.06);
        border-top: 2px solid #10B981;
        border-radius: 12px;
        backdrop-filter: blur(20px);
        padding: 20px;
        margin-bottom: 12px;
    ">
        <div style="font-size:0.75rem;font-weight:700;color:#10B981;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:16px;">
            + New Account
        </div>
    """, unsafe_allow_html=True)
    
    new_username = st.text_input("USERNAME", key="reg_username", placeholder="min_3_chars")
    new_email = st.text_input("EMAIL", key="reg_email", placeholder="user@domain.com")
    new_password = st.text_input("PASSWORD", type="password", key="reg_password", placeholder="min_6_chars")
    confirm_pass = st.text_input("CONFIRM", type="password", key="reg_confirm", placeholder="re_enter")
    
    if new_password:
        score = sum([
            len(new_password) >= 8,
            any(c.isdigit() for c in new_password),
            any(c.isupper() for c in new_password),
            any(not c.isalnum() for c in new_password)
        ])
        labels = [
            ("WEAK — Add length, number, symbol", "#F43F5E"),
            ("WEAK — Add length, number, symbol", "#F43F5E"),
            ("MEDIUM — Add uppercase or symbol", "#F59E0B"),
            ("STRONG", "#10B981"),
            ("STRONG", "#10B981")
        ]
        label, color = labels[score]
        st.markdown(f'<div style="color:{color};font-weight:700;font-size:0.8rem;margin-bottom:10px;">{label}</div>', unsafe_allow_html=True)
    
    if st.button("+ CREATE ACCOUNT", type="primary", use_container_width=True):
        if not new_username or not new_password:
            st.error("Username and password required")
        elif not new_email or not new_email.strip():
            st.error("Email required for recovery")
        elif len(new_username) < 3:
            st.error("Username: min 3 characters")
        elif len(new_password) < 6:
            st.error("Password: min 6 characters")
        elif new_password != confirm_pass:
            st.error("Passwords do not match")
        else:
            user = create_user(new_username.strip(), new_email.strip(), new_password)
            if user:
                create_portfolio(user["id"], "My Portfolio", "Default portfolio")
                st.session_state["logged_in"] = True
                st.session_state["user"] = user
                st.success("Account created — redirecting...")
                st.switch_page("app.py")
            else:
                st.error("Username already exists")
    st.markdown("</div>", unsafe_allow_html=True)

with tab_forgot:
    st.markdown("""
    <div style="
        background: rgba(18,18,26,0.72);
        border: 1px solid rgba(255,255,255,0.06);
        border-top: 2px solid #F43F5E;
        border-radius: 12px;
        backdrop-filter: blur(20px);
        padding: 20px;
        margin-bottom: 12px;
    ">
        <div style="font-size:0.75rem;font-weight:700;color:#F43F5E;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:16px;">
            ? Password Reset
        </div>
    """, unsafe_allow_html=True)
    
    st.caption("Verify identity to reset password")
    fp_username = st.text_input("USERNAME", key="fp_username", placeholder="your_username")
    fp_email = st.text_input("EMAIL", key="fp_email", placeholder="email_on_file")
    
    if st.button("? VERIFY", use_container_width=True):
        if not fp_username or not fp_email:
            st.error("Both fields required")
        else:
            from src.database.db import verify_identity
            if verify_identity(fp_username.strip(), fp_email.strip()):
                st.session_state["fp_verified"] = True
                st.session_state["fp_verified_username"] = fp_username.strip()
                st.session_state["fp_verified_email"] = fp_email.strip()
                st.success("Identity verified")
            else:
                st.session_state["fp_verified"] = False
                st.error("No matching account")
    
    if st.session_state.get("fp_verified"):
        st.markdown("<div style='border-top:1px solid rgba(255,255,255,0.06);margin:16px 0;'></div>", unsafe_allow_html=True)
        new_pw = st.text_input("NEW PASSWORD", type="password", key="fp_new_password", placeholder="min_6_chars")
        confirm_pw = st.text_input("CONFIRM NEW", type="password", key="fp_confirm_password", placeholder="re_enter")
        if st.button("▶ RESET PASSWORD", type="primary", use_container_width=True):
            if not new_pw or len(new_pw) < 6:
                st.error("Password: min 6 characters")
            elif new_pw != confirm_pw:
                st.error("Passwords do not match")
            else:
                ok = reset_password(st.session_state["fp_verified_username"], st.session_state["fp_verified_email"], new_pw)
                if ok:
                    for key in ["fp_verified", "fp_verified_username", "fp_verified_email"]:
                        st.session_state.pop(key, None)
                    st.success("Password reset — login with new credentials")
                else:
                    st.error("Reset failed")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
<div style="border-top:1px solid rgba(255,255,255,0.06);margin-top:32px;padding-top:16px;">
    <div style="font-size:0.65rem;color:#4a4a5e;text-align:center;letter-spacing:0.05em;">
        AXIOM Portfolio Intelligence · Terminal Edition
    </div>
</div>
""", unsafe_allow_html=True)