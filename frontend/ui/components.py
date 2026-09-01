"""
Axiom UI Components v2.1
Reusable glassmorphic layout primitives.
"""
import html
import streamlit as st
from typing import List, Dict, Optional, Any

APP_NAME = "AXIOM"
APP_VERSION = "2.1"

# ── Core Injection ──────────────────────────────────────────

def inject_design_system():
    from .theme import inject_theme
    inject_theme()

# ── Layout Primitives ───────────────────────────────────────

def glass_panel(title: str, subtitle: str = "", accent: str = "primary", content: str = "") -> str:
    """Generate a glassmorphic panel HTML string."""
    accent_map = {
        "primary": ("#FF6B35", "rgba(255,107,53,0.15)"),
        "cyan": ("#00D9FF", "rgba(0,217,255,0.12)"),
        "green": ("#10B981", "rgba(16,185,129,0.12)"),
        "red": ("#F43F5E", "rgba(244,63,94,0.12)"),
        "violet": ("#8B5CF6", "rgba(139,92,246,0.12)"),
        "amber": ("#F59E0B", "rgba(245,158,11,0.12)"),
    }
    color, glow = accent_map.get(accent, accent_map["primary"])

    subtitle_html = f'''<div style="font-size:0.65rem;color:#4a4a5e;letter-spacing:0.06em;text-transform:uppercase;font-weight:600;">{html.escape(subtitle)}</div>''' if subtitle else ""

    return f'''
    <div style="
        background: rgba(18,18,26,0.72);
        border: 1px solid rgba(255,255,255,0.06);
        border-top: 2px solid {color};
        border-radius: 12px;
        backdrop-filter: blur(20px);
        margin-bottom: 12px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.04);
        transition: all 0.2s ease;
        overflow: hidden;
    " class="glass-panel">
        <div style="
            background: linear-gradient(90deg, {glow}, transparent);
            padding: 12px 16px;
            border-bottom: 1px solid rgba(255,255,255,0.04);
            display: flex;
            justify-content: space-between;
            align-items: center;
        ">
            <div style="font-size:0.75rem;font-weight:700;color:{color};text-transform:uppercase;letter-spacing:0.08em;font-family:'Inter',sans-serif;">
                {html.escape(title)}
            </div>
            {subtitle_html}
        </div>
        <div style="padding: 16px;">
            {content}
        </div>
    </div>
    '''


def render_glass_panel(title: str, subtitle: str = "", accent: str = "primary"):
    """Render a glass panel header; use with st.markdown inside."""
    st.markdown(glass_panel(title, subtitle, accent, ""), unsafe_allow_html=True)


def glass_container(accent: str = "primary"):
    """Reserved visual hook for content rendered in subsequent Streamlit elements.

    Streamlit elements cannot be wrapped by an HTML tag emitted in a previous
    ``st.markdown`` call, so this intentionally does not open a cross-element
    ``<div>``.
    """
    return None


# ── Navigation ──────────────────────────────────────────────

def sidebar_brand():
    st.markdown("""
    <div style="
        padding: 20px 16px 16px;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        margin-bottom: 8px;
    ">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
            <div style="
                width: 28px; height: 28px; 
                background: linear-gradient(135deg, #FF6B35, #CC4F25);
                border-radius: 8px;
                display:flex;align-items:center;justify-content:center;
                font-family:'JetBrains Mono',monospace;
                font-size:0.7rem;font-weight:800;color:#020202;
                box-shadow: 0 0 12px rgba(255,107,53,0.3);
            ">A</div>
            <div style="font-size:0.9rem;font-weight:700;color:#f0f0f5;letter-spacing:-0.02em;font-family:'Inter',sans-serif;">
                AXIOM
            </div>
        </div>
        <div style="font-size:0.6rem;color:#4a4a5e;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;">
            Portfolio Intelligence
        </div>
    </div>
    """, unsafe_allow_html=True)


def sidebar_user(username: str, role: str = "Investor"):
    initials = "".join([p[0] for p in username.split()[:2]]).upper() or "U"
    st.markdown(f'''
    <div style="
        margin: 12px 16px;
        padding: 12px;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 10px;
        display: flex;
        align-items: center;
        gap: 10px;
    ">
        <div style="
            width: 32px; height: 32px;
            background: linear-gradient(135deg, #8B5CF6, #6366F1);
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 0.7rem; font-weight: 700; color: white;
            font-family: 'JetBrains Mono', monospace;
            box-shadow: 0 0 12px rgba(139,92,246,0.3);
        ">{html.escape(initials)}</div>
        <div>
            <div style="font-size:0.8rem;font-weight:600;color:#f0f0f5;">{html.escape(username.upper())}</div>
            <div style="font-size:0.6rem;color:#4a4a5e;font-weight:500;letter-spacing:0.05em;text-transform:uppercase;">{html.escape(role)}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)


def sidebar_nav_item(label: str, icon: str, active: bool = False, href: str = ""):
    color = "#FF6B35" if active else "#8b8b9e"
    bg = "rgba(255,107,53,0.08)" if active else "transparent"
    border = "2px solid #FF6B35" if active else "2px solid transparent"
    glow = "box-shadow: 0 0 12px rgba(255,107,53,0.1);" if active else ""

    if active:
        return f'''
        <div style="
            display: flex; align-items: center; gap: 10px;
            padding: 8px 12px; margin: 2px 12px;
            background: {bg};
            border-left: {border};
            border-radius: 0 8px 8px 0;
            color: {color};
            font-size: 0.78rem;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
            letter-spacing: 0.02em;
            {glow}
        ">{icon}&nbsp;&nbsp;{html.escape(label)}</div>
        '''
    else:
        return f'''
        <a href="{html.escape(href)}" style="
            display: flex; align-items: center; gap: 10px;
            padding: 8px 12px; margin: 2px 12px;
            background: {bg};
            border-left: {border};
            border-radius: 0 8px 8px 0;
            color: {color};
            font-size: 0.78rem;
            font-weight: 500;
            font-family: 'Inter', sans-serif;
            letter-spacing: 0.02em;
            text-decoration: none;
            transition: all 0.15s ease;
        ">
            {icon}&nbsp;&nbsp;{html.escape(label)}
        </a>
        '''


def page_sidebar(current_page: str, user: Optional[dict] = None, market_data: Optional[dict] = None):
    """Render the complete Axiom sidebar with brand, markets, user, nav, footer."""
    with st.sidebar:
        sidebar_brand()

        # Market Data
        if market_data:
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
                st.markdown(f'''
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
                ''', unsafe_allow_html=True)
            st.markdown("<div style='border-top:1px solid rgba(255,255,255,0.06);margin:12px 0;'></div>", unsafe_allow_html=True)

        # User & Navigation
        if user:
            sidebar_user(user.get("username", "User"), "Portfolio Manager")
            st.markdown("""
            <div style="padding: 0 16px; margin-bottom: 8px;">
                <div style="font-size:0.6rem;color:#4a4a5e;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;">
                    Navigation
                </div>
            </div>
            """, unsafe_allow_html=True)

            pages = [
                ("app.py", "◈", "Dashboard"),
                ("pages/2_Portfolio.py", "◫", "Portfolio"),
                ("pages/3_Analysis.py", "▣", "Analysis"),
                ("pages/4_History.py", "◫", "History"),
                ("pages/5_Compare.py", "⚖", "Benchmark")
            ]
            for page, icon, label in pages:
                is_active = page == current_page
                if is_active:
                    st.markdown(sidebar_nav_item(label, icon, active=True), unsafe_allow_html=True)
                else:
                    st.page_link(page, label=f"{icon}  {label}", width='stretch')

            st.markdown("<div style='border-top:1px solid rgba(255,255,255,0.06);margin:12px 0;'></div>", unsafe_allow_html=True)
            if st.button("◀ Logout", key=f"logout_{current_page.replace('/', '_')}"):
                for k in ["logged_in", "user", "current_portfolio", "results"]:
                    st.session_state.pop(k, None)
                st.switch_page("app.py")
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

        # Footer
        st.markdown("""
        <div style="padding:  25px 20px 10px 20px; margin-top: auto; border-top: 1px solid rgba(255,255,255,0.06);">
            <div style="font-size:0.6rem;color:#4a4a5e;text-align:center;letter-spacing:0.05em;">
                AXIOM v2.1 · Portfolio Intelligence
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── Command Bar & Ticker ────────────────────────────────────

def command_bar(path: str, detail: str = ""):
    suffix = f" <span style='color:#4a4a5e;margin-left:8px;'>// {html.escape(detail)}</span>" if detail else ""
    st.markdown(f'''
    <div style="
        background: rgba(10,10,15,0.9);
        border-bottom: 1px solid rgba(255,255,255,0.06);
        padding: 10px 16px;
        display: flex;
        align-items: center;
        gap: 10px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
    ">
        <span style="color:#FF6B35;font-weight:700;">➜</span>
        <span style="color:#8b8b9e;">{html.escape(path)}</span>
        {suffix}
        <span style="margin-left:auto;font-size:0.65rem;color:#4a4a5e;text-transform:uppercase;letter-spacing:0.06em;">
            {html.escape(APP_NAME)} v{APP_VERSION}
        </span>
    </div>
    ''', unsafe_allow_html=True)


def ticker_tape(items: List[Dict[str, Any]]):
    """items: [{"name": "AAPL", "price": 150.0, "change": 1.2}, ...]"""
    cells = ""
    for item in items:
        name = item.get("name", "")
        price = item.get("price", 0)
        change = item.get("change", 0)
        is_up = change >= 0
        color = "#10B981" if is_up else "#F43F5E"
        icon = "▲" if is_up else "▼"
        sign = "+" if is_up else ""
        cells += f'''
        <span style="display:inline-flex;align-items:center;gap:6px;margin-right:32px;white-space:nowrap;">
            <strong style="color:#f0f0f5;font-weight:600;">{html.escape(name)}</strong>
            <span style="color:#8b8b9e;font-family:'JetBrains Mono',monospace;">{price:,.2f}</span>
            <span style="color:{color};font-weight:700;font-size:0.75rem;">{icon} {sign}{change:.2f}%</span>
        </span>
        '''

    st.html(f'''
    <div style="
        background: rgba(10,10,15,0.8);
        border-bottom: 1px solid rgba(255,255,255,0.06);
        padding: 8px 0;
        overflow: hidden;
        white-space: nowrap;
        font-size: 0.8rem;
        backdrop-filter: blur(10px);
    ">
        <div style="display:inline-block;animation:ticker 40s linear infinite;padding-left:100%;">
            {cells}
        </div>
        <div style="display:inline-block;animation:ticker 40s linear infinite;padding-left:20px;">
            {cells}
        </div>
    </div>
    <style>
    @keyframes ticker {{
        0% {{ transform: translateX(0); }}
        100% {{ transform: translateX(-100%); }}
    }}
    </style>
    ''')


# ── Data Components ─────────────────────────────────────────

def metric_card(label: str, value: str, delta: str = "", tone: str = "neutral", icon: str = ""):
    """tone: neutral, positive, negative, accent, cyan"""
    tone_map = {
        "neutral": ("#f0f0f5", ""),
        "positive": ("#10B981", "rgba(16,185,129,0.15)"),
        "negative": ("#F43F5E", "rgba(244,63,94,0.15)"),
        "accent": ("#FF6B35", "rgba(255,107,53,0.15)"),
        "cyan": ("#00D9FF", "rgba(0,217,255,0.15)"),
        "violet": ("#8B5CF6", "rgba(139,92,246,0.15)"),
        "amber": ("#F59E0B", "rgba(245,158,11,0.15)"),
    }
    color, glow = tone_map.get(tone, tone_map["neutral"])
    delta_html = f'''<div style="font-size:0.7rem;color:{color};font-weight:600;margin-top:4px;font-family:'JetBrains Mono',monospace;">{html.escape(delta)}</div>''' if delta else ""
    icon_html = f'''<span style="font-size:1.1rem;margin-bottom:4px;display:block;">{icon}</span>''' if icon else ""
    glow_shadow = f", 0 0 20px {glow}" if glow else ""

    return f'''
    <div style="
        background: rgba(18,18,26,0.72);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        backdrop-filter: blur(20px);
        padding: 16px;
        text-align: center;
        transition: all 0.2s ease;
        box-shadow: 0 4px 24px rgba(0,0,0,0.2){glow_shadow};
    ">
        {icon_html}
        <div style="font-size:1.5rem;font-weight:700;color:{color};font-family:'JetBrains Mono',monospace;line-height:1;letter-spacing:-0.02em;">
            {html.escape(value)}
        </div>
        <div style="font-size:0.6rem;color:#4a4a5e;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;margin-top:8px;">
            {html.escape(label)}
        </div>
        {delta_html}
    </div>
    '''


def metric_grid(items: List[Dict[str, Any]], columns: int = 4):
    """items: [{"label": "", "value": "", "delta": "", "tone": "", "icon": ""}, ...]"""
    cells = [metric_card(**item) for item in items]
    grid_style = f"display:grid;grid-template-columns:repeat({columns},1fr);gap:12px;"
    st.html(f'''<div style="{grid_style}">{"".join(cells)}</div>''')


def section_header(title: str, subtitle: str = "", accent: str = "primary"):
    color = {"primary": "#FF6B35", "cyan": "#00D9FF", "green": "#10B981", "red": "#F43F5E", "violet": "#8B5CF6", "amber": "#F59E0B"}.get(accent, "#FF6B35")
    subtitle_html = f'''<div style="font-size:0.7rem;color:#4a4a5e;margin-top:2px;font-weight:500;">{html.escape(subtitle)}</div>''' if subtitle else ""
    st.markdown(f'''
    <div style="margin: 24px 0 12px;">
        <div style="display:flex;align-items:center;gap:8px;">
            <div style="width:4px;height:18px;background:{color};border-radius:2px;box-shadow:0 0 8px {color}40;"></div>
            <div style="font-size:0.95rem;font-weight:700;color:#f0f0f5;letter-spacing:-0.01em;font-family:'Inter',sans-serif;">{html.escape(title)}</div>
        </div>
        {subtitle_html}
    </div>
    ''', unsafe_allow_html=True)


def badge(label: str, tone: str = "neutral") -> str:
    tone_map = {
        "neutral": ("#8b8b9e", "rgba(255,255,255,0.04)"),
        "positive": ("#10B981", "rgba(16,185,129,0.12)"),
        "negative": ("#F43F5E", "rgba(244,63,94,0.12)"),
        "warning": ("#F59E0B", "rgba(245,158,11,0.12)"),
        "accent": ("#FF6B35", "rgba(255,107,53,0.12)"),
        "cyan": ("#00D9FF", "rgba(0,217,255,0.12)"),
        "violet": ("#8B5CF6", "rgba(139,92,246,0.12)"),
    }
    color, bg = tone_map.get(tone, tone_map["neutral"])
    return f'''<span style="background:{bg};color:{color};padding:2px 8px;border-radius:6px;font-size:0.65rem;font-weight:700;letter-spacing:0.04em;text-transform:uppercase;border:1px solid {color}30;">{html.escape(label)}</span>'''


def info_card(title: str, body: str, badge_html: str = "", accent: str = "primary"):
    color = {"primary": "#FF6B35", "cyan": "#00D9FF", "green": "#10B981", "amber": "#F59E0B", "violet": "#8B5CF6"}.get(accent, "#FF6B35")
    st.markdown(f'''
    <div style="
        background: rgba(18,18,26,0.72);
        border: 1px solid rgba(255,255,255,0.06);
        border-left: 3px solid {color};
        border-radius: 0 12px 12px 0;
        backdrop-filter: blur(20px);
        padding: 14px 16px;
        margin-bottom: 10px;
        transition: all 0.2s ease;
    ">
        <div style="display:flex;justify-content:space-between;align-items:start;gap:8px;">
            <div>
                <div style="font-size:0.82rem;font-weight:600;color:#f0f0f5;margin-bottom:4px;font-family:'Inter',sans-serif;">{html.escape(title)}</div>
                <div style="font-size:0.75rem;color:#8b8b9e;line-height:1.5;">{html.escape(body)}</div>
            </div>
            {badge_html}
        </div>
    </div>
    ''', unsafe_allow_html=True)


# ── Table Components ────────────────────────────────────────

def data_table_header(columns: List[str], flexes: Optional[List[int]] = None) -> str:
    flexes = flexes or [1] * len(columns)
    cells = ""
    for col, flex in zip(columns, flexes):
        cells += f'''<div style="flex:{flex};color:#FF6B35;font-size:0.6rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;font-family:'Inter',sans-serif;">{html.escape(col)}</div>'''
    return f'''<div style="display:flex;background:rgba(255,255,255,0.02);border-bottom:1px solid rgba(255,255,255,0.06);padding:8px 12px;border-radius:8px 8px 0 0;">{cells}</div>'''


def data_table_row(cells: List[str], flexes: Optional[List[int]] = None, highlight: bool = False) -> str:
    flexes = flexes or [1] * len(cells)
    bg = "rgba(255,107,53,0.03)" if highlight else "transparent"
    html_cells = ""
    for cell, flex in zip(cells, flexes):
        html_cells += f'''<div style="flex:{flex};color:#8b8b9e;font-size:0.78rem;font-family:'JetBrains Mono',monospace;padding:2px 0;">{cell}</div>'''
    return f'''<div style="display:flex;padding:8px 12px;background:{bg};border-bottom:1px solid rgba(255,255,255,0.03);transition:all 0.15s;">{html_cells}</div>'''


# ── Status & Loading ────────────────────────────────────────

def live_dot() -> str:
    return '''<span style="display:inline-block;width:6px;height:6px;background:#10B981;border-radius:50%;box-shadow:0 0 8px rgba(16,185,129,0.5);margin-right:6px;animation:pulse 2s infinite;"></span>'''


def status_pill(status: str, environment: str = "Production"):
    st.markdown(f'''
    <div style="
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 4px 10px;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 20px;
        font-size: 0.65rem;
        color: #8b8b9e;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    ">
        {live_dot()}
        <span>{html.escape(status)} · {html.escape(environment)}</span>
    </div>
    ''', unsafe_allow_html=True)


def loading_skeleton(height: int = 120, lines: int = 3):
    """Render a skeleton loading placeholder."""
    bars = ""
    for i in range(lines):
        width = 100 - (i * 15)
        bars += f'''<div style="height:10px;width:{width}%;background:linear-gradient(90deg,rgba(255,255,255,0.03),rgba(255,255,255,0.08),rgba(255,255,255,0.03));background-size:200% 100%;border-radius:4px;margin-bottom:10px;animation:shimmer 1.5s infinite;"></div>'''
    st.markdown(f'''
    <div style="padding:16px;background:rgba(18,18,26,0.5);border:1px solid rgba(255,255,255,0.04);border-radius:12px;min-height:{height}px;">
        {bars}
    </div>
    <style>
    @keyframes shimmer {{
        0% {{ background-position: -200% 0; }}
        100% {{ background-position: 200% 0; }}
    }}
    </style>
    ''', unsafe_allow_html=True)


# ── Toast & Modal ───────────────────────────────────────────

def toast_notification(message: str, tone: str = "accent"):
    tone_map = {
        "accent": ("#FF6B35", "rgba(255,107,53,0.12)"),
        "positive": ("#10B981", "rgba(16,185,129,0.12)"),
        "negative": ("#F43F5E", "rgba(244,63,94,0.12)"),
        "cyan": ("#00D9FF", "rgba(0,217,255,0.12)"),
    }
    color, bg = tone_map.get(tone, tone_map["accent"])
    st.markdown(f'''
    <div style="
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        background: {bg};
        border: 1px solid {color}40;
        border-radius: 10px;
        padding: 12px 16px;
        backdrop-filter: blur(20px);
        color: {color};
        font-weight: 600;
        font-size: 0.8rem;
        animation: fadeInUp 0.4s ease-out;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    ">
        {html.escape(message)}
    </div>
    <style>
    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(-10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    </style>
    ''', unsafe_allow_html=True)


def modal_overlay(title: str, content: str, accent: str = "primary"):
    color = {"primary": "#FF6B35", "cyan": "#00D9FF", "green": "#10B981", "red": "#F43F5E"}.get(accent, "#FF6B35")
    st.markdown(f'''
    <div style="
        background: rgba(18,18,26,0.9);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        backdrop-filter: blur(30px);
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 8px 40px rgba(0,0,0,0.5);
    ">
        <div style="font-size:1rem;font-weight:700;color:{color};margin-bottom:12px;font-family:'Inter',sans-serif;">{html.escape(title)}</div>
        <div style="color:#8b8b9e;font-size:0.85rem;line-height:1.6;">{content}</div>
    </div>
    ''', unsafe_allow_html=True)


# ── Chart Wrapper ───────────────────────────────────────────

def chart_container(title: str, subtitle: str = ""):
    section_header(title, subtitle)


# ── Command Palette ─────────────────────────────────────────

def command_palette():
    """
    Render a Command Palette search interface.
    In Streamlit, true global keyboard shortcuts are limited, so this renders
    a prominent search bar that acts as the command hub.
    """
    st.markdown("""
    <style>
    .cmd-palette-container {
        position: relative;
        margin-bottom: 16px;
    }
    .cmd-palette-input {
        background: rgba(18,18,26,0.9) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
        padding: 12px 16px 12px 44px !important;
        color: #f0f0f5 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
        width: 100% !important;
        backdrop-filter: blur(20px);
        transition: all 0.2s ease;
        box-shadow: 0 4px 24px rgba(0,0,0,0.2);
    }
    .cmd-palette-input:focus {
        border-color: #FF6B35 !important;
        box-shadow: 0 0 0 3px rgba(255,107,53,0.15), 0 4px 24px rgba(0,0,0,0.3) !important;
        outline: none !important;
    }
    .cmd-palette-icon {
        position: absolute;
        left: 16px;
        top: 50%;
        transform: translateY(-50%);
        color: #4a4a5e;
        font-size: 0.9rem;
        pointer-events: none;
    }
    .cmd-palette-kbd {
        position: absolute;
        right: 16px;
        top: 50%;
        transform: translateY(-50%);
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.65rem;
        color: #4a4a5e;
        font-family: 'JetBrains Mono', monospace;
        pointer-events: none;
    }
    </style>
    <div class="cmd-palette-container">
        <span class="cmd-palette-icon">⌘</span>
        <input type="text" class="cmd-palette-input" placeholder="Search commands, pages, actions..." readonly onclick="document.querySelector('[data-testid=\'stTextInput\'] input').focus()">
        <span class="cmd-palette-kbd">CTRL+K</span>
    </div>
    """, unsafe_allow_html=True)


def command_palette_modal():
    """
    Render a modal-style command palette with quick actions.
    Call this at the top of any page to enable the palette.
    """
    # Use a session state key to track if palette is open
    if "cmd_palette_open" not in st.session_state:
        st.session_state["cmd_palette_open"] = False

    # The search input that triggers the palette feel
    query = st.text_input(
        "",
        placeholder="⌘ Type a command... (e.g. 'run analysis', 'go to portfolio')",
        key="cmd_palette_query",
        label_visibility="collapsed"
    )

    if query:
        query_lower = query.lower().strip()
        actions = []

        # Navigation commands
        nav_map = {
            "dashboard": ("app.py", "◈ Dashboard"),
            "portfolio": ("pages/2_Portfolio.py", "◫ Portfolio"),
            "analysis": ("pages/3_Analysis.py", "▣ Analysis"),
            "history": ("pages/4_History.py", "◫ History"),
            "compare": ("pages/5_Compare.py", "⚖ Benchmark"),
            "login": ("pages/1_Login.py", "🔐 Login"),
        }

        for keyword, (page, label) in nav_map.items():
            if keyword in query_lower or query_lower in keyword:
                actions.append(("nav", page, label))

        # Action commands
        if any(k in query_lower for k in ["run", "optimize", "analysis"]):
            actions.append(("action", "run_analysis", "▶ Run Portfolio Optimization"))
        if any(k in query_lower for k in ["logout", "sign out"]):
            actions.append(("action", "logout", "◀ Logout"))
        if any(k in query_lower for k in ["theme", "dark", "light", "terminal"]):
            actions.append(("action", "toggle_theme", "◈ Toggle Theme (Axiom / Legacy)"))
        if any(k in query_lower for k in ["report", "export", "download"]):
            actions.append(("action", "export_report", "◉ Export Full Report"))

        if actions:
            st.markdown("""
            <div style="
                background: rgba(18,18,26,0.95);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px;
                backdrop-filter: blur(30px);
                padding: 8px;
                margin-top: 4px;
                margin-bottom: 16px;
                box-shadow: 0 8px 40px rgba(0,0,0,0.5);
                max-height: 300px;
                overflow-y: auto;
            ">
            """, unsafe_allow_html=True)

            for i, (atype, target, label) in enumerate(actions[:6]):
                icon = "→" if atype == "nav" else "⚡"
                color = "#FF6B35" if atype == "nav" else "#00D9FF"
                st.markdown(f"""
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    padding: 8px 12px;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.15s ease;
                    font-size: 0.8rem;
                    color: #f0f0f5;
                ">
                    <span style="color: {color}; font-weight: 700;">{icon}</span>
                    <span style="font-family: 'Inter', sans-serif;">{label}</span>
                    <span style="margin-left: auto; font-size: 0.65rem; color: #4a4a5e; font-family: 'JetBrains Mono', monospace;">{atype.upper()}</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            # Execute the first action if Enter is pressed (simulated via button)
            for atype, target, label in actions[:1]:
                if atype == "nav":
                    if st.button(f"Go to {label}", key="cmd_nav", width='stretch'):
                        st.switch_page(target)
                elif atype == "action":
                    if target == "logout":
                        if st.button("Logout", key="cmd_logout", width='stretch'):
                            for k in ["logged_in", "user", "current_portfolio", "results"]:
                                st.session_state.pop(k, None)
                            st.switch_page("app.py")
                    elif target == "toggle_theme":
                        from frontend.ui.theme import theme_toggle
                        theme_toggle()
                    elif target == "run_analysis":
                        if st.button("▶ Run Analysis", key="cmd_run", type="primary", width='stretch'):
                            st.switch_page("pages/3_Analysis.py")
        else:
            st.markdown("""
            <div style="
                background: rgba(18,18,26,0.9);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 12px;
                padding: 12px;
                margin-bottom: 16px;
                font-size: 0.78rem;
                color: #4a4a5e;
                text-align: center;
            ">
                No commands found. Try: "go to portfolio", "run analysis", "toggle theme"
            </div>
            """, unsafe_allow_html=True)


# ── Theme Toggle in Sidebar ─────────────────────────────────

def sidebar_theme_toggle():
    """Render a compact theme toggle in the sidebar."""
    current = st.session_state.get("axiom_theme", "axiom")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("◈ Axiom", width='stretch', type="primary" if current == "axiom" else "secondary"):
            st.session_state["axiom_theme"] = "axiom"
            st.rerun()
    with col2:
        if st.button("◫ Terminal", width='stretch', type="primary" if current == "legacy" else "secondary"):
            st.session_state["axiom_theme"] = "legacy"
            st.rerun()
