from __future__ import annotations

APP_NAME = "Axiom Portfolio Intelligence"
APP_VERSION = "1.0.0"

COLORS = {
    "bg": "#070A0F",
    "surface": "#0D1118",
    "surface_2": "#111722",
    "surface_3": "#151D29",
    "border": "#202836",
    "border_soft": "#18202B",
    "text": "#E7ECF4",
    "muted": "#8E99AA",
    "subtle": "#5F6A79",
    "primary": "#6C8CFF",
    "primary_soft": "rgba(108,140,255,.12)",
    "positive": "#42D3A4",
    "warning": "#FFB44C",
    "negative": "#FF6B7A",
    "info": "#5CC8FF",
}

CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap');

:root {
  --bg:#070A0F; --surface:#0D1118; --surface-2:#111722; --surface-3:#151D29;
  --border:#202836; --border-soft:#18202B; --text:#E7ECF4; --muted:#8E99AA;
  --subtle:#5F6A79; --primary:#6C8CFF; --primary-soft:rgba(108,140,255,.12);
  --positive:#42D3A4; --warning:#FFB44C; --negative:#FF6B7A; --info:#5CC8FF;
  --shadow:0 12px 36px rgba(0,0,0,.18); --radius:14px; --radius-sm:10px;
}
html, body, [data-testid="stAppViewContainer"] { background:var(--bg); color:var(--text); }
* { font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
code, pre, .mono { font-family:"JetBrains Mono",monospace !important; }
.block-container { max-width: 1560px; padding-top: 1.1rem; padding-bottom: 3rem; }
[data-testid="stSidebar"] { border-right:1px solid var(--border-soft); }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap:.65rem; }

h1,h2,h3 { letter-spacing:-.025em; }
h1 { font-size:1.9rem !important; }
h2 { font-size:1.25rem !important; }

.ax-topbar{
  display:flex; align-items:center; justify-content:space-between; gap:16px;
  padding:10px 14px; margin-bottom:18px; border:1px solid var(--border-soft);
  background:rgba(13,17,24,.82); backdrop-filter:blur(12px); border-radius:12px;
}
.ax-brand{display:flex;align-items:center;gap:10px;font-weight:700;font-size:.9rem}
.ax-mark{
  width:28px;height:28px;border-radius:8px;display:grid;place-items:center;
  background:linear-gradient(135deg,#6C8CFF,#8C6CFF);color:white;font-weight:800;
  box-shadow:0 6px 18px rgba(108,140,255,.24)
}
.ax-status{display:flex;gap:8px;align-items:center;color:var(--muted);font-size:.78rem}
.ax-dot{width:7px;height:7px;border-radius:50%;background:var(--positive);box-shadow:0 0 10px rgba(66,211,164,.55)}

.ax-pagehead{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;margin:6px 0 20px}
.ax-eyebrow{color:var(--primary);font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.11em;margin-bottom:6px}
.ax-title{font-size:1.72rem;font-weight:700;letter-spacing:-.035em;color:var(--text);line-height:1.15}
.ax-subtitle{color:var(--muted);font-size:.88rem;margin-top:6px;max-width:760px;line-height:1.55}

.ax-card{
  border:1px solid var(--border);background:linear-gradient(180deg,rgba(17,23,34,.96),rgba(13,17,24,.96));
  border-radius:var(--radius); padding:16px; box-shadow:var(--shadow);
}
.ax-card-flat{border:1px solid var(--border-soft);background:var(--surface);border-radius:var(--radius-sm);padding:14px}
.ax-card-title{font-size:.8rem;font-weight:650;color:var(--text);margin-bottom:4px}
.ax-card-caption{font-size:.73rem;color:var(--muted);line-height:1.45}

.ax-metric-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:14px}
.ax-metric{border:1px solid var(--border);background:var(--surface);border-radius:12px;padding:14px 15px}
.ax-metric-label{font-size:.69rem;color:var(--muted);font-weight:650;letter-spacing:.055em;text-transform:uppercase}
.ax-metric-value{font-size:1.62rem;line-height:1.15;font-weight:700;color:var(--text);margin-top:8px;letter-spacing:-.035em}
.ax-metric-meta{font-size:.72rem;color:var(--muted);margin-top:6px}
.ax-up{color:var(--positive)} .ax-down{color:var(--negative)} .ax-warn{color:var(--warning)} .ax-primary{color:var(--primary)}

.ax-section-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:22px 0 10px}
.ax-section-title{font-size:.88rem;font-weight:700;color:var(--text)}
.ax-section-sub{font-size:.72rem;color:var(--muted)}

.ax-badge{display:inline-flex;align-items:center;gap:6px;padding:4px 8px;border:1px solid var(--border);border-radius:999px;font-size:.68rem;font-weight:650;color:var(--muted);background:var(--surface)}
.ax-badge.good{color:var(--positive);border-color:rgba(66,211,164,.25);background:rgba(66,211,164,.07)}
.ax-badge.warn{color:var(--warning);border-color:rgba(255,180,76,.25);background:rgba(255,180,76,.07)}
.ax-badge.bad{color:var(--negative);border-color:rgba(255,107,122,.25);background:rgba(255,107,122,.07)}

.ax-row{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:9px 0;border-bottom:1px solid var(--border-soft)}
.ax-row:last-child{border-bottom:0}
.ax-symbol{font-family:"JetBrains Mono",monospace;font-size:.78rem;font-weight:600}
.ax-muted{color:var(--muted);font-size:.74rem}

.ax-command{
  display:flex;gap:8px;align-items:center;padding:9px 11px;border-radius:10px;border:1px solid var(--border-soft);
  background:#090D13;color:var(--muted);font-size:.75rem
}
.ax-command strong{color:var(--primary);font-family:"JetBrains Mono",monospace}

[data-testid="stMetric"]{
  border:1px solid var(--border)!important;background:var(--surface)!important;
  border-radius:12px!important;padding:12px 14px!important
}
[data-testid="stMetricLabel"] p{color:var(--muted)!important;font-size:.72rem!important}
[data-testid="stMetricValue"]{letter-spacing:-.03em}

.stButton>button, .stDownloadButton>button{
  border-radius:10px!important; min-height:40px!important; font-weight:650!important;
  border:1px solid var(--border)!important; transition:.16s ease!important
}
.stButton>button[kind="primary"], .stDownloadButton>button[kind="primary"]{
  background:linear-gradient(135deg,#6C8CFF,#806CFF)!important;color:#fff!important;border:0!important;
  box-shadow:0 8px 20px rgba(108,140,255,.22)!important
}
.stButton>button:hover,.stDownloadButton>button:hover{transform:translateY(-1px)}
div[data-baseweb="input"]>div, div[data-baseweb="select"]>div, textarea{
  border-radius:10px!important;border-color:var(--border)!important;background:var(--surface)!important
}
[data-testid="stTabs"] [data-baseweb="tab-list"]{gap:6px;border-bottom:1px solid var(--border-soft)}
[data-testid="stTabs"] [data-baseweb="tab"]{border-radius:9px 9px 0 0;padding:8px 12px;color:var(--muted)}
[data-testid="stTabs"] [aria-selected="true"]{color:var(--text);background:var(--surface-2)}
[data-testid="stDataFrame"]{border:1px solid var(--border);border-radius:12px;overflow:hidden}
hr{border-color:var(--border-soft)!important}
a{color:#8EA5FF}

@media(max-width:1100px){.ax-metric-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:700px){
 .block-container{padding-left:.75rem;padding-right:.75rem}
 .ax-metric-grid{grid-template-columns:1fr 1fr}
 .ax-pagehead{display:block}
 .ax-topbar{align-items:flex-start}
}
</style>
"""
