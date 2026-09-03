"""
Axiom Design System v2.1
Institutional-grade dark UI tokens for Streamlit.
Dynamically generated from tokens.py — single source of truth.
"""
import streamlit as st
from types import SimpleNamespace

from .tokens import COLORS

# Compatibility layer for the old theme API that expected a TOKENS object.
TOKENS = SimpleNamespace(
    color=SimpleNamespace(
        bg_base=COLORS["bg"],
        bg_elevated=COLORS["surface"],
        bg_surface=COLORS["surface_2"],
        accent_primary=COLORS["primary"],
        accent_secondary=COLORS["info"],
        accent_info=COLORS["info"],
        accent_success=COLORS["positive"],
        accent_danger=COLORS["negative"],
        accent_warning=COLORS["warning"],
        text_primary=COLORS["text"],
        text_secondary=COLORS["muted"],
        text_tertiary=COLORS["subtle"],
        text_inverse="#070A0F",
        border_subtle=COLORS["border_soft"],
        border_default=COLORS["border"],
        border_accent=COLORS["primary"],
    ),
    typography=SimpleNamespace(
        font_sans="'Inter', system-ui, sans-serif",
        font_mono="'JetBrains Mono', monospace",
    ),
    border=SimpleNamespace(
        radius_lg="14px",
        radius_md="12px",
        radius_sm="8px",
    ),
    shadow=SimpleNamespace(
        shadow_sm="0 8px 20px rgba(0,0,0,0.18)",
        shadow_md="0 12px 30px rgba(0,0,0,0.2)",
        shadow_lg="0 18px 42px rgba(0,0,0,0.22)",
        shadow_glow_primary="0 0 18px rgba(108,140,255,0.25)",
        shadow_glow_success="0 0 18px rgba(66,211,164,0.22)",
        shadow_glow_danger="0 0 18px rgba(255,107,122,0.22)",
    ),
)


def get_css_variables() -> dict:
    """Backward-compatible CSS variable lookup for legacy theme consumers."""
    return {
        "bg_primary": TOKENS.color.bg_base,
        "bg_secondary": TOKENS.color.bg_elevated,
        "bg_tertiary": TOKENS.color.bg_surface,
        "accent": TOKENS.color.accent_primary,
        "text_primary": TOKENS.color.text_primary,
        "text_secondary": TOKENS.color.text_secondary,
        "text_tertiary": TOKENS.color.text_tertiary,
        "border_subtle": TOKENS.color.border_subtle,
        "border_default": TOKENS.color.border_default,
    }


def get_color(name: str, default: str = "") -> str:
    """Backward-compatible color accessor."""
    return getattr(TOKENS.color, name, default)


# ── Theme Presets ───────────────────────────────────────────
THEMES = {
    "axiom": {
        "bg_primary": TOKENS.color.bg_base,
        "bg_secondary": TOKENS.color.bg_elevated,
        "bg_tertiary": TOKENS.color.bg_surface,
        "bg_glass": "rgba(18, 18, 26, 0.72)",
        "accent": TOKENS.color.accent_primary,
        "accent_dim": "#CC4F25",
        "accent_glow": "rgba(255, 107, 53, 0.20)",
        "cyan": TOKENS.color.accent_secondary,
        "cyan_glow": "rgba(0, 217, 255, 0.15)",
        "violet": TOKENS.color.accent_info,
        "positive": TOKENS.color.accent_success,
        "positive_glow": "rgba(16, 185, 129, 0.15)",
        "negative": TOKENS.color.accent_danger,
        "negative_glow": "rgba(244, 63, 94, 0.15)",
        "warning": TOKENS.color.accent_warning,
        "text_primary": TOKENS.color.text_primary,
        "text_secondary": TOKENS.color.text_secondary,
        "text_tertiary": TOKENS.color.text_tertiary,
        "text_inverse": TOKENS.color.text_inverse,
        "border_subtle": TOKENS.color.border_subtle,
        "border_active": TOKENS.color.border_default,
        "border_glow": TOKENS.color.border_accent,
        "font_sans": TOKENS.typography.font_sans,
        "font_mono": TOKENS.typography.font_mono,
        "radius": TOKENS.border.radius_lg,
        "radius_sm": TOKENS.border.radius_md,
        "radius_xs": TOKENS.border.radius_sm,
        "shadow_sm": TOKENS.shadow.shadow_sm,
        "shadow_md": TOKENS.shadow.shadow_md,
        "shadow_lg": TOKENS.shadow.shadow_lg,
        "shadow_glow_primary": TOKENS.shadow.shadow_glow_primary,
        "shadow_glow_success": TOKENS.shadow.shadow_glow_success,
        "shadow_glow_danger": TOKENS.shadow.shadow_glow_danger,
    },
    "legacy": {
        "bg_primary": "#050505",
        "bg_secondary": "#0a0a0a",
        "bg_tertiary": "#0d0d0d",
        "bg_glass": "rgba(10, 10, 10, 0.95)",
        "accent": "#ff6600",
        "accent_dim": "#cc5200",
        "accent_glow": "rgba(255, 102, 0, 0.25)",
        "cyan": "#00d084",
        "cyan_glow": "rgba(0, 208, 132, 0.15)",
        "violet": "#8b5cf6",
        "positive": "#00d084",
        "positive_glow": "rgba(0, 208, 132, 0.15)",
        "negative": "#ff3333",
        "negative_glow": "rgba(255, 51, 51, 0.15)",
        "warning": "#f59e0b",
        "text_primary": "#e5e5e5",
        "text_secondary": "#888888",
        "text_tertiary": "#555555",
        "text_inverse": "#050505",
        "border_subtle": "#2a2a2a",
        "border_active": "#3a3a3a",
        "border_glow": "rgba(255, 102, 0, 0.30)",
        "font_sans": "'JetBrains Mono', monospace",
        "font_mono": "'JetBrains Mono', monospace",
        "radius": "0px",
        "radius_sm": "2px",
        "radius_xs": "2px",
        "shadow_sm": "0 1px 2px rgba(0,0,0,0.3)",
        "shadow_md": "0 4px 6px rgba(0,0,0,0.4)",
        "shadow_lg": "0 10px 15px rgba(0,0,0,0.5)",
        "shadow_glow_primary": "0 0 12px rgba(255,102,0,0.25)",
        "shadow_glow_success": "0 0 12px rgba(0,208,132,0.15)",
        "shadow_glow_danger": "0 0 12px rgba(255,51,51,0.15)",
    }
}

# ── Active Theme Accessor ───────────────────────────────────
def get_active_theme():
    """Get the currently active theme preset."""
    theme_name = st.session_state.get("axiom_theme", "axiom")
    return THEMES.get(theme_name, THEMES["axiom"])


def t(key: str) -> str:
    """Shorthand to get a token value from the active theme."""
    return get_active_theme().get(key, "")


# ── Plotly Theme ────────────────────────────────────────────
def get_plotly_template():
    """Generate Plotly template from active theme tokens."""
    return {
        "layout": {
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {
                "family": t("font_mono"),
                "color": t("text_primary"),
                "size": 11
            },
            "margin": {"l": 16, "r": 16, "t": 40, "b": 16},
            "xaxis": {
                "gridcolor": "rgba(255,255,255,0.04)",
                "linecolor": "rgba(255,255,255,0.08)",
                "zerolinecolor": "rgba(255,255,255,0.06)",
                "tickfont": {"size": 10, "color": t("text_tertiary")},
            },
            "yaxis": {
                "gridcolor": "rgba(255,255,255,0.04)",
                "linecolor": "rgba(255,255,255,0.08)",
                "zerolinecolor": "rgba(255,255,255,0.06)",
                "tickfont": {"size": 10, "color": t("text_tertiary")},
            },
            "legend": {
                "bgcolor": "rgba(0,0,0,0)",
                "bordercolor": "rgba(255,255,255,0.06)",
                "borderwidth": 1,
                "font": {"size": 10},
            },
            "colorway": [
                t("accent"), t("cyan"), t("violet"), t("positive"),
                t("negative"), t("warning"), "#EC4899", "#6366F1"
            ],
        }
    }

PLOTLY_TEMPLATE = get_plotly_template()

# ── CSS Design System (Dynamic from Tokens) ────────────────
def generate_css() -> str:
    """Generate complete CSS from active theme tokens."""
    th = get_active_theme()
    is_axiom = st.session_state.get("axiom_theme", "axiom") == "axiom"

    # Gradient backgrounds only for Axiom theme
    bg_gradients = """
    background-image: 
      radial-gradient(ellipse 80% 50% at 50% -20%, rgba(255,107,53,0.08), transparent),
      radial-gradient(ellipse 60% 40% at 80% 80%, rgba(0,217,255,0.04), transparent);
    """ if is_axiom else ""

    # Font import only for Axiom (Inter + JetBrains Mono)
    font_import = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');
    """ if is_axiom else """
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700;800&display=swap');
    """

    return f"""
<style>


/* Keep Streamlit's header because it owns the sidebar reopen control. */
header[data-testid="stHeader"] {{
  display: block !important;
  background: transparent !important;
  border-bottom: none !important;
}}

[data-testid="stSidebar"] {{
  background: linear-gradient(
    180deg,
    var(--bg-secondary) 0%,
    var(--bg-primary) 100%
  ) !important;
  border-right: 1px solid var(--border-subtle) !important;
}}

[data-testid="stSidebar"] > div:first-child {{
  padding: 0 !important;
  background: transparent !important;
}}

[data-testid="stSidebarNav"] {{
  display: none !important;
}}

.stApp {{
  margin-top: 0 !important;
}}


{font_import}

:root {{
  /* Colors */
  --bg-primary: {th["bg_primary"]};
  --bg-secondary: {th["bg_secondary"]};
  --bg-tertiary: {th["bg_tertiary"]};
  --bg-glass: {th["bg_glass"]};
  --border-subtle: {th["border_subtle"]};
  --border-active: {th["border_active"]};
  --border-glow: {th["border_glow"]};
  --accent: {th["accent"]};
  --accent-dim: {th["accent_dim"]};
  --accent-glow: {th["accent_glow"]};
  --cyan: {th["cyan"]};
  --cyan-glow: {th["cyan_glow"]};
  --violet: {th["violet"]};
  --positive: {th["positive"]};
  --positive-glow: {th["positive_glow"]};
  --negative: {th["negative"]};
  --negative-glow: {th["negative_glow"]};
  --warning: {th["warning"]};
  --text-primary: {th["text_primary"]};
  --text-secondary: {th["text_secondary"]};
  --text-tertiary: {th["text_tertiary"]};
  --text-inverse: {th["text_inverse"]};
  --font-sans: {th["font_sans"]};
  --font-mono: {th["font_mono"]};
  --radius: {th["radius"]};
  --radius-sm: {th["radius_sm"]};
  --radius-xs: {th["radius_xs"]};
  --shadow-sm: {th["shadow_sm"]};
  --shadow-md: {th["shadow_md"]};
  --shadow-lg: {th["shadow_lg"]};
  --shadow-glow-primary: {th["shadow_glow_primary"]};
  --shadow-glow-success: {th["shadow_glow_success"]};
  --shadow-glow-danger: {th["shadow_glow_danger"]};
}}

/* ── Base Reset ──────────────────────────────────────────── */
* {{ 
  font-family: var(--font-sans); 
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}}

html, body, [class*="css"] {{ 
  font-family: var(--font-sans) !important; 
}}

[data-testid="stAppViewContainer"] {{
  background: var(--bg-primary) !important;
  {bg_gradients}
}}

.block-container {{
  padding: 1.5rem 2rem 4rem !important;
  max-width: 1400px !important;
}}

/* ── Sidebar ─────────────────────────────────────────────── */
[data-testid="stSidebar"] {{
  background: linear-gradient(
    180deg,
    var(--bg-secondary) 0%,
    var(--bg-primary) 100%
  ) !important;
  border-right: 1px solid var(--border-subtle) !important;
}}

[data-testid="stSidebar"][aria-expanded="true"] {{
  min-width: 280px !important;
  width: 280px !important;
  max-width: 320px !important;
}}


[data-testid="stSidebar"] > div:first-child {{
  padding: 0 !important;
  background: transparent !important;
}}

[data-testid="stSidebarNav"] {{ display: none !important; }}

/* ── Scrollbar ───────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--border-active); border-radius: 10px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--text-tertiary); }}

/* ── Typography ──────────────────────────────────────────── */
h1, h2, h3 {{ 
  font-family: var(--font-sans) !important; 
  font-weight: 700 !important; 
  letter-spacing: -0.02em !important;
  color: var(--text-primary) !important;
}}

/* ── Buttons ─────────────────────────────────────────────── */
.stButton > button {{
  background: linear-gradient(135deg, var(--accent), var(--accent-dim)) !important;
  color: var(--text-inverse) !important;
  border: none !important;
  border-radius: var(--radius-sm) !important;
  font-family: var(--font-sans) !important;
  font-weight: 600 !important;
  font-size: 0.8rem !important;
  letter-spacing: 0.02em !important;
  padding: 0.6rem 1.2rem !important;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
  box-shadow: 0 2px 8px var(--accent-glow) !important;
}}

.stButton > button:hover {{
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 20px var(--accent-glow) !important;
  filter: brightness(1.1) !important;
}}

.stButton > button:active {{
  transform: translateY(0) !important;
}}

.stButton > button[kind="secondary"] {{
  background: var(--bg-tertiary) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border-subtle) !important;
  box-shadow: none !important;
}}

.stButton > button[kind="secondary"]:hover {{
  border-color: var(--border-active) !important;
  background: var(--bg-glass) !important;
  box-shadow: 0 2px 12px rgba(0,0,0,0.3) !important;
}}

/* ── Inputs ──────────────────────────────────────────────── */
.stTextInput > div > div, 
.stNumberInput > div > div,
.stSelectbox > div > div,
.stDateInput > div > div {{
  background: var(--bg-tertiary) !important;
  border: 1px solid var(--border-subtle) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text-primary) !important;
  transition: all 0.2s ease !important;
}}

.stTextInput > div > div:focus-within,
.stNumberInput > div > div:focus-within,
.stSelectbox > div > div:focus-within {{
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px var(--accent-glow) !important;
}}

.stTextInput > div > div > input,
.stNumberInput > div > div > input {{
  color: var(--text-primary) !important;
  font-family: var(--font-mono) !important;
  font-size: 0.85rem !important;
}}

/* ── Tabs ────────────────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {{
  gap: 0 !important;
  border-bottom: 1px solid var(--border-subtle) !important;
  background: transparent !important;
  padding: 0 4px !important;
}}

[data-testid="stTabs"] [data-baseweb="tab"] {{
  border-radius: var(--radius-xs) var(--radius-xs) 0 0 !important;
  padding: 10px 18px !important;
  font-weight: 500 !important;
  font-size: 0.78rem !important;
  color: var(--text-secondary) !important;
  border: none !important;
  letter-spacing: 0.02em !important;
  transition: all 0.2s ease !important;
  background: transparent !important;
}}

[data-testid="stTabs"] [data-baseweb="tab"]:hover {{
  color: var(--text-primary) !important;
  background: rgba(255,255,255,0.02) !important;
}}

[data-testid="stTabs"] [aria-selected="true"] {{
  color: var(--accent) !important;
  background: linear-gradient(180deg, var(--accent-glow), transparent) !important;
}}

[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{
  background: var(--accent) !important;
  height: 2px !important;
  box-shadow: 0 0 8px var(--accent-glow) !important;
}}

/* ── Metrics ─────────────────────────────────────────────── */
[data-testid="stMetric"] {{
  background: var(--bg-glass) !important;
  border: 1px solid var(--border-subtle) !important;
  border-radius: var(--radius) !important;
  backdrop-filter: blur(12px) !important;
  padding: 1rem !important;
  transition: all 0.2s ease !important;
}}

[data-testid="stMetric"]:hover {{
  border-color: var(--border-active) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}}

[data-testid="stMetricValue"] {{
  font-family: var(--font-mono) !important;
  font-weight: 700 !important;
  font-size: 1.4rem !important;
  color: var(--text-primary) !important;
  letter-spacing: -0.02em !important;
}}

[data-testid="stMetricLabel"] {{
  font-family: var(--font-sans) !important;
  color: var(--text-tertiary) !important;
  font-size: 0.65rem !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
}}

/* ── DataFrames / Tables ─────────────────────────────────── */
[data-testid="stDataFrame"] {{
  background: var(--bg-glass) !important;
  border: 1px solid var(--border-subtle) !important;
  border-radius: var(--radius) !important;
  backdrop-filter: blur(12px) !important;
}}

[data-testid="stDataFrame"] th {{
  background: rgba(255,255,255,0.03) !important;
  color: var(--accent) !important;
  font-family: var(--font-sans) !important;
  font-size: 0.65rem !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.06em !important;
  border-bottom: 1px solid var(--border-subtle) !important;
}}

[data-testid="stDataFrame"] td {{
  color: var(--text-secondary) !important;
  font-family: var(--font-mono) !important;
  font-size: 0.8rem !important;
  border-bottom: 1px solid rgba(255,255,255,0.02) !important;
}}

/* ── Expanders ───────────────────────────────────────────── */
[data-testid="stExpander"] {{
  background: var(--bg-glass) !important;
  border: 1px solid var(--border-subtle) !important;
  border-radius: var(--radius) !important;
  backdrop-filter: blur(12px) !important;
}}

[data-testid="stExpander"] > div:first-child {{
  background: rgba(255,255,255,0.02) !important;
  border-radius: var(--radius) var(--radius) 0 0 !important;
}}

/* ── Sliders ─────────────────────────────────────────────── */
.stSlider > div > div > div {{
  color: var(--accent) !important;
}}

/* ── Checkbox / Radio ────────────────────────────────────── */
.stCheckbox > div > div > div, .stRadio > div > div > div {{
  background: var(--bg-tertiary) !important;
  border-color: var(--border-subtle) !important;
}}

/* ── Toast / Alerts ──────────────────────────────────────── */
[data-testid="stToast"] {{
  background: var(--bg-glass) !important;
  border: 1px solid var(--border-subtle) !important;
  backdrop-filter: blur(20px) !important;
}}

/* ── Animations ──────────────────────────────────────────── */
@keyframes fadeInUp {{
  from {{ opacity: 0; transform: translateY(12px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

@keyframes pulse {{
  0%, 100% {{ opacity: 1; }}
  50% {{ opacity: 0.4; }}
}}

@keyframes ticker {{
  0% {{ transform: translateX(0); }}
  100% {{ transform: translateX(-50%); }}
}}

@keyframes shimmer {{
  0% {{ background-position: -200% 0; }}
  100% {{ background-position: 200% 0; }}
}}

@keyframes glow {{
  0%, 100% {{ box-shadow: 0 0 20px var(--accent-glow); }}
  50% {{ box-shadow: 0 0 40px var(--accent-glow), 0 0 60px rgba(255,107,53,0.08); }}
}}

.animate-fade-in {{
  animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}}

.animate-pulse {{
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}}

/* ── Mobile ──────────────────────────────────────────────── */
@media (max-width: 768px) {{
  .block-container {{ padding: 1rem !important; }}
  [data-testid="stSidebar"] {{ min-width: 240px !important; }}
}}
</style>
"""


def inject_theme():
    """Inject the Axiom design system into the current Streamlit page."""
    st.markdown(generate_css(), unsafe_allow_html=True)


def apply_plotly_theme(fig):
    """Apply the active dark theme to a Plotly figure."""
    template = get_plotly_template()
    fig.update_layout(**template["layout"])
    return fig


def theme_toggle():
    """Render a theme toggle switch in the sidebar footer area."""
    current = st.session_state.get("axiom_theme", "axiom")
    options = {"axiom": "◈ Axiom Glass", "legacy": "◫ Terminal Legacy"}

    selected = st.selectbox(
        "Theme",
        options=list(options.keys()),
        format_func=lambda x: options[x],
        index=0 if current == "axiom" else 1,
        key="theme_selector",
        label_visibility="collapsed"
    )

    if selected != current:
        st.session_state["axiom_theme"] = selected
        st.rerun()
