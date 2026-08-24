"""
report_generator.py — Bloomberg Terminal Style HTML Report
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from src.optimization.health_score import HealthScoreEngine


def generate_bloomberg_report(portfolio, results, display_names):
    """Generate a self-contained HTML report in Bloomberg Terminal style."""
    opt_result = results.get("opt_result", {})
    baseline = results.get("baseline", {})
    final_weights = results.get("final_weights", {})
    sentiment_scores = results.get("sentiment_scores", {})
    risk_report = results.get("risk_report", {})
    recommendations = results.get("recommendations", [])
    combined = results.get("combined", {})
    frontier_df = results.get("frontier_df", pd.DataFrame())
    returns_df = results.get("returns", pd.DataFrame())
    available = results.get("tickers", [])
    # Defensive fallback: news may live under several keys
    all_news = (
        results.get("all_news", {})
        or results.get("news", {})
        or results.get("articles", {})
    )

    sharpe = opt_result.get("sharpe_ratio", 0)
    var95 = risk_report.get("value_at_risk", {}).get("historical_95", {})
    var99 = risk_report.get("value_at_risk", {}).get("historical_99", {})
    vol = risk_report.get("volatility", {}).get("portfolio_annualized", 0)
    mdd = risk_report.get("drawdown", {}).get("portfolio", {})
    avg_sent = sum(sentiment_scores.values()) / len(sentiment_scores) if sentiment_scores else 0

    news_counts = {t: len(all_news.get(t, [])) for t in available}
    health = results.get("health_score") or HealthScoreEngine.calculate(
        sharpe=sharpe,
        volatility=vol,
        var95=var95.get("var_pct", 0.0),
        max_drawdown_pct=mdd.get("max_drawdown_pct", 0.0),
        sentiment_scores=sentiment_scores,
        final_weights=final_weights,
        risk_report=risk_report,
        baseline_sharpe=baseline.get("sharpe_ratio"),
        news_counts=news_counts,
    )
    ai_score = health["score"]
    score_label = f'{health["label"]} · {health["grade"]}'

    # Currency symbol
    pf_curr = portfolio.get("currency", "USD")
    currency_symbol = "₹" if pf_curr == "INR" else "$"

    # Weights table
    weights_rows = []
    vols = risk_report.get("volatility", {}).get("per_ticker_annualized", {})
    max_vol = max(vols.values()) if vols else 0
    for t in available:
        w_opt = opt_result.get("weights", {}).get(t, 0) * 100
        w_final = final_weights.get(t, 0) * 100
        wc = combined.get("weight_changes", {}).get(t, {})
        change = wc.get("change", 0) * 100

        # Action logic: tiny changes (<1%) are HOLD, not BUY/SELL
        if w_opt < 0.1 and w_final < 0.1:
            action = "EXCLUDE"
            action_color = "#888888"
        elif abs(change) < 1.0:
            action = "HOLD"
            action_color = "#888888"
        else:
            action = wc.get("action", "HOLD")
            action_color = "#00d084" if action == "BUY" else ("#ff3333" if action == "SELL" else "#888888")

        change_color = "#00d084" if change >= 0 else "#ff3333"

        # Exclusion / adjustment reason
        reason = ""
        if action == "EXCLUDE":
            reasons = []
            if w_opt < 0.1:
                reasons.append("Low Sharpe contribution")
            sent = sentiment_scores.get(t, 0)
            if sent < -0.1:
                reasons.append(f"Negative sentiment ({sent:+.2f})")
            if vols.get(t, 0) >= max_vol * 0.95:
                reasons.append("High volatility")
            reason = "; ".join(reasons) if reasons else "Suboptimal risk/return"
        elif action == "HOLD" and abs(change) < 1.0:
            reason = "Within rebalancing threshold"
        elif action == "BUY":
            reason = "Sentiment / diversification boost"
        elif action == "SELL":
            reason = "Reduce concentration / sentiment drag"

        weights_rows.append(f"""<tr>
            <td style="padding:6px 10px;border-bottom:1px dotted #2a2a2a;color:#e5e5e5;font-weight:600;">{display_names.get(t, t)}</td>
            <td style="padding:6px 10px;border-bottom:1px dotted #2a2a2a;color:#888;text-align:right;">{w_opt:.2f}%</td>
            <td style="padding:6px 10px;border-bottom:1px dotted #2a2a2a;color:#ff6600;text-align:right;font-weight:700;">{w_final:.2f}%</td>
            <td style="padding:6px 10px;border-bottom:1px dotted #2a2a2a;text-align:right;color:{change_color};">{change:+.2f}%</td>
            <td style="padding:6px 10px;border-bottom:1px dotted #2a2a2a;text-align:right;color:{action_color};font-weight:700;">{action}</td>
            <td style="padding:6px 10px;border-bottom:1px dotted #2a2a2a;text-align:right;color:#555;font-size:0.7rem;">{reason}</td>
        </tr>""")
    weights_html = "\n".join(weights_rows)

    # Sentiment rows — fixed threshold ±0.05
    sentiment_rows = []
    for t in available:
        score = sentiment_scores.get(t, 0)
        label = "POSITIVE" if score >= 0.05 else ("NEGATIVE" if score <= -0.05 else "NEUTRAL")
        color = "#00d084" if score >= 0.05 else ("#ff3333" if score <= -0.05 else "#888888")
        bar_width = int((score + 1) / 2 * 100)
        sentiment_rows.append(f"""<tr>
            <td style="padding:6px 10px;border-bottom:1px dotted #2a2a2a;color:#e5e5e5;font-weight:600;">{display_names.get(t, t)}</td>
            <td style="padding:6px 10px;border-bottom:1px dotted #2a2a2a;">
                <div style="background:#1a1a1a;height:4px;width:100px;"><div style="background:{color};height:100%;width:{bar_width}%;"></div></div>
            </td>
            <td style="padding:6px 10px;border-bottom:1px dotted #2a2a2a;text-align:right;color:{color};font-weight:700;">{score:+.3f}</td>
            <td style="padding:6px 10px;border-bottom:1px dotted #2a2a2a;text-align:right;color:{color};">{label}</td>
        </tr>""")
    sentiment_html = "\n".join(sentiment_rows)

    # Risk per ticker
    risk_rows = []
    for t in available:
        v = vols.get(t, 0) * 100
        c = "#ff3333" if v > vol * 100 else "#00d084"
        risk_rows.append(f"""<tr>
            <td style="padding:6px 10px;border-bottom:1px dotted #2a2a2a;color:#e5e5e5;">{display_names.get(t, t)}</td>
            <td style="padding:6px 10px;border-bottom:1px dotted #2a2a2a;text-align:right;color:{c};">{v:.2f}%</td>
        </tr>""")
    risk_html = "\n".join(risk_rows)

    # Recommendations
    rec_parts = []
    if recommendations:
        for rec in recommendations:
            t = rec.get("ticker", "")
            score = rec.get("sentiment_score", 0)
            label = rec.get("sentiment_label", "NEUTRAL")
            weight_pct = rec.get("portfolio_weight_pct", "0")
            text = rec.get("recommendation", "")
            # Use same threshold as sentiment table
            color = "#00d084" if score >= 0.05 else ("#ff3333" if score <= -0.05 else "#888888")
            rec_parts.append(f"""<div style="margin-bottom:16px;padding:12px;background:#0d0d0d;border-left:2px solid {color};">
                <div style="font-size:0.8rem;font-weight:700;color:#e5e5e5;margin-bottom:4px;">{display_names.get(t, t)} — WEIGHT: {weight_pct}% | SENTIMENT: <span style="color:{color}">{score:+.3f} ({label})</span></div>
                <div style="font-size:0.75rem;color:#888;line-height:1.5;">{text}</div>
            </div>""")
    rec_html = "\n".join(rec_parts) if rec_parts else '<div style="color:#888;font-size:0.8rem;">NO LLM RECOMMENDATIONS GENERATED</div>'

    # News
    news_parts = []
    for t in available:
        articles = all_news.get(t, [])
        if articles:
            news_parts.append(f'<div style="margin-bottom:12px;"><div style="font-size:0.75rem;font-weight:700;color:#ff6600;margin-bottom:4px;">{display_names.get(t, t)} — {len(articles)} ARTICLES</div>')
            for a in articles[:5]:
                news_parts.append(f'<div style="font-size:0.72rem;color:#888;padding:2px 0;">• {a.get("title", "")}</div>')
            news_parts.append('</div>')
    news_html = "\n".join(news_parts) if news_parts else '<div style="color:#555;font-size:0.75rem;">NO NEWS DATA</div>'

    # Charts
    frontier_div = ""
    if not frontier_df.empty:
        try:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=frontier_df["volatility"]*100, y=frontier_df["return"]*100, mode='markers', marker=dict(color=frontier_df["sharpe"], colorscale=[[0,'#ff3333'],[0.5,'#ff6600'],[1,'#00d084']], size=4, opacity=0.5), name="FRONTIER"))
            fig.add_trace(go.Scatter(x=[opt_result.get("volatility",0)*100], y=[opt_result.get("expected_return",0)*100], mode='markers+text', marker=dict(color='#ff6600', size=14, symbol='star'), text=["OPTIMAL"], textposition="top center", name="OPTIMAL"))
            fig.add_trace(go.Scatter(x=[baseline.get("volatility",0)*100], y=[baseline.get("expected_return",0)*100], mode='markers+text', marker=dict(color='#888888', size=10, symbol='diamond'), text=["BASELINE"], textposition="bottom center", name="BASELINE"))
            fig.update_layout(
                title="EFFICIENT FRONTIER", xaxis_title="VOLATILITY (%)", yaxis_title="RETURN (%)",
                height=400, paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a",
                font=dict(family="JetBrains Mono, monospace", color="#e5e5e5", size=10),
                margin=dict(l=50, r=20, t=50, b=40),
                xaxis=dict(gridcolor="#2a2a2a", linecolor="#3a3a3a"),
                yaxis=dict(gridcolor="#2a2a2a", linecolor="#3a3a3a"),
                legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#2a2a2a", borderwidth=1, font=dict(size=9))
            )
            frontier_div = fig.to_html(full_html=False, include_plotlyjs=False)
        except Exception:
            frontier_div = ""
    weights_bar_div = ""
    if final_weights and baseline:
        try:
            from plotly.subplots import make_subplots
            tickers_list = list(final_weights.keys())
            final_vals = [final_weights.get(t, 0) * 100 for t in tickers_list]
            equal_val = 100 / len(tickers_list) if tickers_list else 0
            equal_vals = [equal_val] * len(tickers_list)

            fig_w = make_subplots(rows=1, cols=2, subplot_titles=(
                "FINAL WEIGHTS",
                f"EQUAL WEIGHT (SHARPE={baseline.get('sharpe_ratio', 0):.3f})"
            ))
            fig_w.add_trace(go.Bar(
                y=[display_names.get(t, t) for t in tickers_list], x=final_vals,
                orientation='h', marker=dict(color='#ff6600'),
                text=[f"{v:.1f}%" for v in final_vals], textposition='outside'
            ), row=1, col=1)
            fig_w.add_trace(go.Bar(
                y=[display_names.get(t, t) for t in tickers_list], x=equal_vals,
                orientation='h', marker=dict(color='#888888'),
                text=[f"{v:.1f}%" for v in equal_vals], textposition='outside'
            ), row=1, col=2)
            fig_w.update_layout(
                showlegend=False, height=max(300, 40 * len(tickers_list)),
                paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a",
                font=dict(family="JetBrains Mono, monospace", color="#e5e5e5", size=10),
                margin=dict(l=100, r=20, t=40, b=40)
            )
            fig_w.update_xaxes(title_text="WEIGHT (%)", gridcolor="#2a2a2a", linecolor="#3a3a3a")
            fig_w.update_yaxes(gridcolor="#2a2a2a", linecolor="#3a3a3a")
            weights_bar_div = fig_w.to_html(full_html=False, include_plotlyjs=False)
        except Exception:
            weights_bar_div = ""

    corr_div = ""
    if not returns_df.empty:
        try:
            corr = returns_df.corr()
            corr.columns = [display_names.get(t, t) for t in corr.columns]
            corr.index = corr.columns
            fig_c = px.imshow(corr, color_continuous_scale=[[0,'#ff3333'],[0.5,'#111111'],[1,'#00d084']], aspect="auto")
            fig_c.update_traces(texttemplate="%{z:.2f}", textfont=dict(size=8, color="#e5e5e5"))
            fig_c.update_layout(
                title="CORRELATION MATRIX", height=350,
                paper_bgcolor="#0a0a0a", plot_bgcolor="#0a0a0a",
                font=dict(family="JetBrains Mono, monospace", color="#e5e5e5", size=10),
                margin=dict(l=50, r=20, t=50, b=40),
                coloraxis_colorbar=dict(tickfont=dict(color="#888"), titlefont=dict(color="#888"))
            )
            corr_div = fig_c.to_html(full_html=False, include_plotlyjs=False)
        except Exception:
            corr_div = ""

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    gen_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pf_name = portfolio.get("name", "PORTFOLIO").upper()
    exp_ret = opt_result.get("expected_return", 0)
    exp_ret_cls = "pos" if exp_ret > 0 else "neg"
    avg_sent_cls = "pos" if avg_sent > 0.05 else ("neg" if avg_sent < -0.05 else "accent")

    score_breakdown_rows = "".join(
        f'<tr><td style="padding:6px 10px;border-bottom:1px dotted #2a2a2a;">{k.replace("_", " ").title()}</td>'
        f'<td style="padding:6px 10px;border-bottom:1px dotted #2a2a2a;text-align:right;color:#ff6600;font-weight:700;">{v:.1f}/100</td>'
        f'<td style="padding:6px 10px;border-bottom:1px dotted #2a2a2a;text-align:right;color:#888;">{health.get("component_weights", {}).get(k, 0)*100:.0f}%</td></tr>'
        for k, v in health.get("components", {}).items()
    )
    score_improvements_html = "".join(
        f'<div style="padding:3px 0;color:#888;">• {tip}</div>' for tip in health.get("improvements", [])
    )
    adaptive_candidates = results.get("adaptive_candidates", []) or []
    selected_cap = results.get("selected_cap")
    adaptive_rows = "".join(
        f'<tr><td style="padding:6px 10px;border-bottom:1px dotted #2a2a2a;">{c.get("max_weight_cap", 0)*100:.1f}%</td>'
        f'<td style="padding:6px 10px;border-bottom:1px dotted #2a2a2a;text-align:right;color:#ff6600;">{c.get("health_score", 0):.1f}</td>'
        f'<td style="padding:6px 10px;border-bottom:1px dotted #2a2a2a;text-align:right;">{c.get("sharpe_ratio", 0):.3f}</td>'
        f'<td style="padding:6px 10px;border-bottom:1px dotted #2a2a2a;text-align:right;">{c.get("volatility", 0)*100:.1f}%</td></tr>'
        for c in adaptive_candidates
    )
    adaptive_html = (
        '<div style="margin-top:14px;"><div style="color:#ff6600;font-weight:700;margin-bottom:6px;">ADAPTIVE CAP SEARCH</div>'
        '<table><thead><tr><th>MAX WEIGHT</th><th style="text-align:right">HEALTH</th><th style="text-align:right">SHARPE</th><th style="text-align:right">VOL</th></tr></thead>'
        f'<tbody>{adaptive_rows}</tbody></table>'
        f'<div style="margin-top:8px;color:#888;">SELECTED CAP: <strong style="color:#e5e5e5;">{(selected_cap or 0)*100:.1f}%</strong> | POTENTIAL SCORE: <strong style="color:#e5e5e5;">{health.get("potential_score", ai_score):.1f}/100</strong></div></div>'
        if adaptive_candidates else ''
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI PORTFOLIO REPORT — {pf_name}</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<style><link href="https://fonts.googleapis.com/icon?family=Material+Icons"
      rel="stylesheet">
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'JetBrains Mono','Courier New',monospace; background:#050505; color:#e5e5e5; font-size:0.8rem; line-height:1.5; }}
  .page {{ max-width:900px; margin:0 auto; padding:24px; }}
  .header {{ border-bottom:2px solid #ff6600; padding-bottom:16px; margin-bottom:24px; }}
  .header-top {{ display:flex; justify-content:space-between; align-items:flex-start; }}
  .header h1 {{ font-size:1.4rem; font-weight:800; color:#ff6600; letter-spacing:-0.5px; }}
  .header .meta {{ font-size:0.7rem; color:#888; margin-top:4px; }}
  .header .badge {{ background:#ff6600; color:#050505; padding:2px 8px; font-size:0.65rem; font-weight:800; }}
  .section {{ margin-bottom:28px; border:1px solid #2a2a2a; }}
  .section-header {{ background:#0d0d0d; border-bottom:1px solid #2a2a2a; padding:8px 12px; display:flex; justify-content:space-between; align-items:center; }}
  .section-title {{ font-size:0.7rem; font-weight:700; color:#ff6600; text-transform:uppercase; letter-spacing:1px; }}
  .section-sub {{ font-size:0.6rem; color:#555; }}
  .section-body {{ padding:12px; background:#0a0a0a; }}
  table {{ width:100%; border-collapse:collapse; font-size:0.75rem; }}
  th {{ background:#141414; color:#ff6600; text-align:left; padding:8px 10px; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.5px; border-bottom:1px solid #3a3a3a; }}
  td {{ padding:6px 10px; }}
  .kpi-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:1px; background:#2a2a2a; border:1px solid #2a2a2a; }}
  .kpi-cell {{ background:#0a0a0a; padding:12px; text-align:center; }}
  .kpi-value {{ font-size:1.3rem; font-weight:700; color:#e5e5e5; }}
  .kpi-value.accent {{ color:#ff6600; }}
  .kpi-value.pos {{ color:#00d084; }}
  .kpi-value.neg {{ color:#ff3333; }}
  .kpi-label {{ font-size:0.55rem; color:#555; text-transform:uppercase; letter-spacing:1px; margin-top:4px; }}
  .disclaimer {{ border-top:1px solid #2a2a2a; padding-top:16px; margin-top:32px; font-size:0.65rem; color:#555; line-height:1.6; }}
  .chart-container {{ margin:12px 0; }}
  @media print {{ body {{ background:#fff; color:#000; }} .section {{ border-color:#ccc; }} }}
</style>
</head>
<body>
<div class="page">

  <div class="header">
    <div class="header-top">
      <div>
        <h1>▶ AI PORTFOLIO OPTIMIZER</h1>
        <div class="meta">TERMINAL EDITION v5.0 | PORTFOLIO ANALYSIS REPORT</div>
      </div>
      <div class="badge">CONFIDENTIAL</div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:12px;font-size:0.75rem;color:#888;">
      <div>PORTFOLIO: <strong style="color:#e5e5e5;">{pf_name}</strong></div>
      <div>CURRENCY: <strong style="color:#e5e5e5;">{pf_curr}</strong></div>
      <div>DATE: <strong style="color:#e5e5e5;">{now_str}</strong></div>
    </div>
  </div>

  <div class="section">
    <div class="section-header"><span class="section-title">◈ Portfolio Health Score</span><span class="section
    -sub">COMPOSITE METRIC</span></div>
    <div class="section-body">
      <div class="kpi-grid">
        <div class="kpi-cell"><div class="kpi-value accent">{ai_score:.0f}</div><div class="kpi-label">AI Score — {score_label}</div></div>
        <div class="kpi-cell"><div class="kpi-value">{sharpe:.3f}</div><div class="kpi-label">Sharpe Ratio</div></div>
        <div class="kpi-cell"><div class="kpi-value {exp_ret_cls}">{exp_ret*100:.2f}%</div><div class="kpi-label">Exp Return</div></div>
        <div class="kpi-cell"><div class="kpi-value neg">{vol*100:.2f}%</div><div class="kpi-label">Volatility</div></div>
        <div class="kpi-cell"><div class="kpi-value neg">{currency_symbol}{var95.get("var_usd", 0):,.0f}</div><div class="kpi-label">95% VaR</div></div>
        <div class="kpi-cell"><div class="kpi-value neg">{currency_symbol}{var99.get("var_usd", 0):,.0f}</div><div class="kpi-label">99% VaR</div></div>
        <div class="kpi-cell"><div class="kpi-value neg">{mdd.get("max_drawdown_pct", 0):.2f}%</div><div class="kpi-label">Max Drawdown</div></div>
        <div class="kpi-cell"><div class="kpi-value {avg_sent_cls}">{avg_sent:+.3f}</div><div class="kpi-label">Avg Sentiment</div></div>
      </div>
    </div>
  </div>
  
  <div class="section">
    <div class="section-header"><span class="section-title">◈ AI Health Score v3 Breakdown</span><span class="section-sub">EXPLAINABLE 0-100 MODEL</span></div>
    <div class="section-body">
      <table><thead><tr><th>COMPONENT</th><th style="text-align:right">SCORE</th><th style="text-align:right">WEIGHT</th></tr></thead><tbody>{score_breakdown_rows}</tbody></table>
      <div style="margin-top:12px;padding:8px;background:#0d0d0d;font-size:0.7rem;color:#888;">BASE: {health.get("base_score", 0):.1f} | PENALTIES: -{health.get("penalty_total", 0):.1f} | FINAL: <strong style="color:#ff6600;">{ai_score:.1f}/100</strong></div>
      <div style="margin-top:10px;font-size:0.7rem;">{score_improvements_html}</div>
      {adaptive_html}
    </div>
  </div>

  <div class="section">
    <div class="section-header"><span class="section-title">◈ High-Level Snapshot</span><span class="section-sub">FINAL vs EQUAL WEIGHT</span></div>
    <div class="section-body">
      <div class="chart-container">{weights_bar_div or '<div style="color:#555;font-size:0.75rem;">CHART NOT AVAILABLE</div>'}</div>
    </div>
  </div>

  <div class="section">
    <div class="section-header"><span class="section-title">◫ Portfolio Composition</span><span class="section-sub">OPTIMIZED WEIGHTS</span></div>
    <div class="section-body">
      <table>
        <thead><tr><th>TICKER</th><th style="text-align:right">OPTIMIZED</th><th style="text-align:right">FINAL</th><th style="text-align:right">CHANGE</th><th style="text-align:right">ACTION</th><th style="text-align:right">REASON</th></tr></thead>
        <tbody>{weights_html}</tbody>
      </table>
    </div>
  </div>

  <div class="section">
    <div class="section-header"><span class="section-title">◈ Efficient Frontier</span><span class="section-sub">RISK vs RETURN</span></div>
    <div class="section-body">
      <div class="chart-container">{frontier_div or '<div style="color:#555;font-size:0.75rem;">CHART NOT AVAILABLE</div>'}</div>
    </div>
  </div>

  <div class="section">
    <div class="section-header"><span class="section-title">◫ Risk Breakdown</span><span class="section-sub">PER-TICKER VOLATILITY</span></div>
    <div class="section-body">
      <table>
        <thead><tr><th>TICKER</th><th style="text-align:right">ANN VOLATILITY</th></tr></thead>
        <tbody>{risk_html}</tbody>
      </table>
      <div style="margin-top:12px;padding:8px;background:#0d0d0d;font-size:0.7rem;color:#888;">
        PORTFOLIO VOLATILITY: <strong style="color:#e5e5e5;">{vol*100:.2f}%</strong> |
        CONCENTRATION RISK: <strong style="color:#e5e5e5;">{risk_report.get("concentration", {}).get("label", "N/A")}</strong>
      </div>
    </div>
  </div>

  <div class="section">
    <div class="section-header"><span class="section-title">◫ Correlation Matrix</span><span class="section-sub">RETURN CORRELATIONS</span></div>
    <div class="section-body">
      <div class="chart-container">{corr_div or '<div style="color:#555;font-size:0.75rem;">CHART NOT AVAILABLE</div>'}</div>
    </div>
  </div>

  <div class="section">
    <div class="section-header"><span class="section-title">◉ Sentiment Analysis</span><span class="section-sub">FINBERT NLP SCORES</span></div>
    <div class="section-body">
      <table>
        <thead><tr><th>TICKER</th><th>BAR</th><th style="text-align:right">SCORE</th><th style="text-align:right">LABEL</th></tr></thead>
        <tbody>{sentiment_html}</tbody>
      </table>
    </div>
  </div>

  <div class="section">
    <div class="section-header"><span class="section-title">◫ Recent Headlines</span><span class="section-sub">NEWS FEED</span></div>
    <div class="section-body">{news_html}</div>
  </div>

  <div class="section">
    <div class="section-header"><span class="section-title">◉ AI Recommendations</span><span class="section-sub">GROQ LLAMA 3.3 70B</span></div>
    <div class="section-body">{rec_html}</div>
  </div>

  <div class="disclaimer">
    <strong style="color:#ff6600;">DISCLAIMER:</strong> This report is generated by an AI-powered portfolio optimization system for informational purposes only.
    It does not constitute investment advice. Past performance does not guarantee future results.
    All metrics are based on historical data and statistical models. Consult a qualified financial advisor before making investment decisions.<br><br>
    <span style="color:#555;">AI Portfolio Optimizer | Bloomberg Terminal Edition | Generated {gen_str}</span>
  </div>

</div>
</body>
</html>"""
    return html
