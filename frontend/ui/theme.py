from __future__ import annotations
import streamlit as st

PLOTLY_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"family": "Inter, JetBrains Mono, monospace", "color": "#d7dde8", "size": 11},
    "margin": {"l": 24, "r": 24, "t": 48, "b": 32},
    "xaxis": {"gridcolor": "#202835", "linecolor": "#2c3646"},
    "yaxis": {"gridcolor": "#202835", "linecolor": "#2c3646"},
}

CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
:root {
  --bg:#0b0f15; --panel:#101722; --panel2:#131c29; --input:#0d141e;
  --border:#263244; --border2:#1d2838; --text:#eef3f9; --text2:#aab6c6;
  --text3:#718096; --accent:#ff8a1f; --positive:#2bd99f; --negative:#ff5d6c;
  --warning:#f4bf4f; --info:#64a8ff; --radius:10px; --radius-sm:7px;
  --sans:'Inter',system-ui,sans-serif; --mono:'JetBrains Mono',monospace;
}
html,body,[class*="css"]{font-family:var(--sans);}
[data-testid="stAppViewContainer"]{background:var(--bg);color:var(--text);}
[data-testid="stHeader"]{background:rgba(11,15,21,.88);backdrop-filter:blur(10px);}
.block-container{max-width:1500px;padding:1rem 1.3rem 2rem;}
[data-testid="stSidebar"]{background:#0d131c;border-right:1px solid var(--border2);}
[data-testid="stSidebarNav"]{display:none;}

.q-header{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;
border:1px solid var(--border);border-radius:var(--radius);background:linear-gradient(180deg,#121b27,#0f1620);margin-bottom:12px;}
.q-eyebrow{font-family:var(--mono);font-size:.66rem;letter-spacing:.13em;text-transform:uppercase;color:var(--accent);font-weight:700;}
.q-title{font-size:1.25rem;font-weight:700;color:var(--text);margin-top:3px;}
.q-sub{font-size:.73rem;color:var(--text3);margin-top:3px;}
.q-status{display:flex;gap:7px;flex-wrap:wrap;padding:8px 10px;background:#0f1620;border:1px solid var(--border2);border-radius:var(--radius-sm);margin-bottom:12px;}
.q-pill{font-family:var(--mono);font-size:.64rem;padding:4px 8px;border:1px solid var(--border);border-radius:999px;color:var(--text2);}
.q-pill.ok{color:var(--positive);border-color:rgba(43,217,159,.35);}
.q-pill.warn{color:var(--warning);border-color:rgba(244,191,79,.35);}
.q-pill.bad{color:var(--negative);border-color:rgba(255,93,108,.35);}
.q-pill.accent{color:var(--accent);border-color:rgba(255,138,31,.4);}
.q-section{display:flex;justify-content:space-between;align-items:end;margin:18px 0 8px;}
.q-section strong{font-size:.92rem;color:var(--text);}
.q-section span{font-family:var(--mono);font-size:.66rem;color:var(--text3);}
.q-card{background:var(--panel);border:1px solid var(--border2);border-radius:var(--radius);padding:14px;min-height:100px;}
.q-label{font-size:.64rem;color:var(--text3);text-transform:uppercase;letter-spacing:.08em;font-weight:700;}
.q-value{font-family:var(--mono);font-size:1.5rem;color:var(--text);font-weight:700;margin-top:7px;line-height:1;}
.q-foot{font-size:.67rem;color:var(--text3);margin-top:8px;}
.pos{color:var(--positive)!important}.neg{color:var(--negative)!important}.warn{color:var(--warning)!important}.accent{color:var(--accent)!important}
.stButton>button,.stDownloadButton>button{border-radius:var(--radius-sm)!important;border:1px solid var(--border)!important;background:var(--panel2)!important;color:var(--text)!important;font-weight:600!important;min-height:38px;}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:var(--accent)!important;color:var(--accent)!important;}
[data-testid="stMetric"]{background:var(--panel);border:1px solid var(--border2);border-radius:var(--radius);padding:10px 12px;}
[data-testid="stMetricValue"]{font-family:var(--mono)!important;color:var(--text)!important;}
[data-testid="stMetricLabel"]{color:var(--text3)!important;}
.stTabs [data-baseweb="tab-list"]{gap:4px;border-bottom:1px solid var(--border2);}
.stTabs [data-baseweb="tab"]{padding:8px 13px;color:var(--text2);font-size:.76rem;}
.stTabs [aria-selected="true"]{color:var(--accent)!important;background:#121a25;}
div[data-baseweb="select"]>div,.stTextInput>div>div,.stNumberInput>div>div{background:var(--input)!important;border-color:var(--border)!important;border-radius:var(--radius-sm)!important;}
@media(max-width:900px){.block-container{padding:.7rem}.q-header{align-items:flex-start}.q-value{font-size:1.25rem}}
</style>
"""

def inject_theme():
    st.markdown(CSS, unsafe_allow_html=True)
