import streamlit as st
from frontend.ui.theme import inject_theme
from frontend.ui.components import page_header, status_strip, section_header, metric_card

st.set_page_config(page_title="AI Quant Terminal", page_icon="📊", layout="wide")
inject_theme()

results = st.session_state.get("results") or {}
health = results.get("health_score") or {}
opt = results.get("opt_result") or {}
risk = results.get("risk_report") or {}

page_header(
    "Portfolio Intelligence",
    "Risk-adjusted optimization, portfolio risk, validation and market intelligence.",
    right='<span class="q-pill ok">SYSTEM ONLINE</span>',
)

status_strip([
    ("HEALTH SCORE v3", "accent"),
    ("VALIDATION v4", "accent"),
    ("MARKET DATA", "ok"),
    ("FINBERT", "ok"),
])

section_header("Portfolio health", "LATEST ANALYSIS")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    metric_card(
        "Health score",
        f"{float(health.get('score', 0)):.0f}",
        f"{health.get('label','Not analyzed')} · {health.get('grade','—')}",
        "accent",
    )
with c2:
    metric_card("Sharpe", f"{float(opt.get('sharpe_ratio',0)):.3f}", "risk-adjusted return")
with c3:
    metric_card("Expected return", f"{float(opt.get('expected_return',0))*100:.1f}%", "annualized", "pos")
with c4:
    vol = float(risk.get("volatility",{}).get("portfolio_annualized",0))
    metric_card("Volatility", f"{vol*100:.1f}%", "annualized", "warn")
with c5:
    mdd = float(risk.get("drawdown",{}).get("portfolio",{}).get("max_drawdown_pct",0))
    metric_card("Max drawdown", f"{mdd:.1f}%", "historical", "neg")

section_header("Decision workspace", "WHAT NEEDS ATTENTION")
a,b,c = st.columns(3)
with a:
    metric_card("Concentration", "TOP-2", "Show top-two exposure, HHI and binding constraints", "warn")
with b:
    metric_card("Validation", "OOS", "Walk-forward Sharpe, turnover and net return", "accent")
with c:
    metric_card("Data confidence", "NEWS", "Relevance-filtered sentiment + source quality", "pos")
