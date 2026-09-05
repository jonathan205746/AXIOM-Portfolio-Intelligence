"""
Axiom Report Generator V1.0.0
Self-contained HTML reports in institutional glassmorphic aesthetic.
"""
from datetime import datetime
from html import escape

import bleach
import markdown
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.optimization.health_score import HealthScoreEngine
from src.utils.sentiment import (
    SentimentLabel,
    classify_sentiment,
)
from src.optimization.rebalancing import (
    classify_model_adjustment,
)


ALLOWED_AI_HTML_TAGS = [
    "p",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
    "br",
]


def render_ai_commentary(commentary: str) -> str:
    """Convert AI Markdown to a small, sanitized HTML subset."""

    converted = markdown.markdown(
        commentary or "",
        extensions=[],
    )

    return bleach.clean(
        converted,
        tags=ALLOWED_AI_HTML_TAGS,
        attributes={},
        protocols=[],
        strip=True,
    )


def get_report_sentiment(
    score: float | None,
    colors: dict,
) -> tuple[str, str, str, int]:
    """Return canonical label, color, display score and bar width."""

    sentiment = classify_sentiment(score)

    color_by_label = {
        SentimentLabel.POSITIVE: colors["green"],
        SentimentLabel.NEGATIVE: colors["red"],
        SentimentLabel.NEUTRAL: colors["text_secondary"],
        SentimentLabel.INSUFFICIENT_EVIDENCE: colors["amber"],
    }

    if score is None:
        return (
            sentiment.value,
            color_by_label[sentiment],
            "N/A",
            50,
        )

    numeric_score = float(score)
    bar_width = int((numeric_score + 1.0) / 2.0 * 100)
    bar_width = max(0, min(100, bar_width))

    return (
        sentiment.value,
        color_by_label[sentiment],
        f"{numeric_score:+.3f}",
        bar_width,
    )

def generate_axiom_report(portfolio, results, display_names):
    """Generate a self-contained HTML report in Axiom glassmorphic style."""
    opt_result = results.get("opt_result", {})
    baseline = results.get("baseline", {})
    final_weights = results.get("final_weights", {})
    sentiment_scores = results.get("sentiment_scores", {})
    risk_report = results.get("risk_report", {})
    recommendations = results.get("recommendations", [])
    combined = results.get("combined", {})
    rebalance_plan = results.get("rebalance_plan", {})
    current_allocation = results.get(
        "current_allocation",
        {},
    )
    frontier_df = results.get(
        "frontier_df",
        pd.DataFrame(),
    )
    returns_df = results.get("returns", pd.DataFrame())
    correlation_matrix = results.get("correlation_matrix")
    available = results.get("tickers", [])
    all_news = results.get("all_news", {}) or results.get("news", {}) or results.get("articles", {})

    sharpe = opt_result.get("sharpe_ratio", 0)
    var95 = risk_report.get("value_at_risk", {}).get("historical_95", {})
    var99 = risk_report.get("value_at_risk", {}).get("historical_99", {})
    vol = risk_report.get("volatility", {}).get("portfolio_annualized", 0)
    mdd = risk_report.get("drawdown", {}).get("portfolio", {})
    available_sentiments = [
        float(score)
        for score in sentiment_scores.values()
        if score is not None
    ]

    avg_sent = (
        sum(available_sentiments)
        / len(available_sentiments)
        if available_sentiments
        else None
    )

    news_counts = {t: len(all_news.get(t, [])) for t in available}
    health = results.get("health_score") or HealthScoreEngine.calculate(
        sharpe=sharpe, volatility=vol,
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

    pf_curr = portfolio.get("currency", "USD")
    currency_symbol = "₹" if pf_curr == "INR" else "$"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    gen_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pf_name = portfolio.get("name", "PORTFOLIO").upper()

    # ── Color System (Axiom V1.0.0) ───────────────────────────
    C = {
        "bg_base": "#020202",
        "bg_elevated": "#0a0a0f",
        "bg_surface": "#12121a",
        "bg_glass": "rgba(18, 18, 26, 0.72)",
        "accent": "#FF6B35",
        "accent_dim": "#CC4F25",
        "accent_glow": "rgba(255, 107, 53, 0.20)",
        "cyan": "#00D9FF",
        "green": "#10B981",
        "red": "#F43F5E",
        "violet": "#8B5CF6",
        "amber": "#F59E0B",
        "text_primary": "#f0f0f5",
        "text_secondary": "#8b8b9e",
        "text_tertiary": "#4a4a5e",
        "text_inverse": "#020202",
        "border_subtle": "rgba(255, 255, 255, 0.05)",
        "border_active": "rgba(255, 255, 255, 0.10)",
    }
    # ── Weights Table ────────────────────────────────────────
    weights_rows = []

    for ticker in available:
        optimized_weight = float(
            opt_result
            .get("weights", {})
            .get(ticker, 0.0)
        )
        final_weight = float(
            final_weights.get(ticker, 0.0)
        )

        optimized_pct = optimized_weight * 100
        final_pct = final_weight * 100
        model_change_pct = (
            final_weight - optimized_weight
        ) * 100

        model_action = classify_model_adjustment(
            optimized_weight,
            final_weight,
        )

        plan_entry = rebalance_plan.get(ticker, {})
        current_weight = plan_entry.get("current_weight")
        rebalance_gap = plan_entry.get("gap")
        rebalance_action = plan_entry.get(
            "action",
            "UNAVAILABLE",
        )
        reason = plan_entry.get(
            "reason",
            "Current allocation data is unavailable",
        )

        current_text = (
            f"{float(current_weight) * 100:.2f}%"
            if current_weight is not None
            else "N/A"
        )
        gap_text = (
            f"{float(rebalance_gap) * 100:+.2f}%"
            if rebalance_gap is not None
            else "N/A"
        )

        if rebalance_action == "BUY":
            action_color = C["green"]
        elif rebalance_action == "SELL":
            action_color = C["red"]
        else:
            action_color = C["text_secondary"]

        if model_action == "INCREASE":
            model_color = C["green"]
        elif model_action == "DECREASE":
            model_color = C["red"]
        else:
            model_color = C["text_secondary"]

        if rebalance_gap is None:
            gap_color = C["text_secondary"]
        elif float(rebalance_gap) >= 0:
            gap_color = C["green"]
        else:
            gap_color = C["red"]

        weights_rows.append(f"""
        <tr>
          <td style="padding:8px 10px;border-bottom:1px solid {C['border_subtle']};color:{C['text_primary']};font-weight:600;">{escape(str(display_names.get(ticker, ticker)))}</td>
          <td style="padding:8px 10px;border-bottom:1px solid {C['border_subtle']};text-align:right;color:{C['text_primary']};font-family:'JetBrains Mono',monospace;">{current_text}</td>
          <td style="padding:8px 10px;border-bottom:1px solid {C['border_subtle']};text-align:right;color:{C['text_secondary']};font-family:'JetBrains Mono',monospace;">{optimized_pct:.2f}%</td>
          <td style="padding:8px 10px;border-bottom:1px solid {C['border_subtle']};text-align:right;color:{C['accent']};font-weight:700;font-family:'JetBrains Mono',monospace;">{final_pct:.2f}%</td>
          <td style="padding:8px 10px;border-bottom:1px solid {C['border_subtle']};text-align:right;color:{model_color};font-family:'JetBrains Mono',monospace;">{model_change_pct:+.2f}%</td>
          <td style="padding:8px 10px;border-bottom:1px solid {C['border_subtle']};text-align:right;color:{model_color};font-weight:600;">{model_action}</td>
          <td style="padding:8px 10px;border-bottom:1px solid {C['border_subtle']};text-align:right;color:{gap_color};font-family:'JetBrains Mono',monospace;">{gap_text}</td>
          <td style="padding:8px 10px;border-bottom:1px solid {C['border_subtle']};text-align:right;color:{action_color};font-weight:700;">{rebalance_action}</td>
          <td style="padding:8px 10px;border-bottom:1px solid {C['border_subtle']};color:{C['text_tertiary']};font-size:0.70rem;">{escape(str(reason))}</td>
        </tr>
        """)

    weights_html = "\n".join(weights_rows)

    # ── Sentiment Rows ────────────────────────────────────────
    sentiment_rows = []
    for t in available:
        score = sentiment_scores.get(t)
        label, color, score_text, bar_width = get_report_sentiment(
          score,
          C,
        )
        sentiment_rows.append(f"""
        <tr>
            <td style="padding:8px 12px;border-bottom:1px solid {C['border_subtle']};color:{C['text_primary']};font-weight:600;font-family:'Inter',sans-serif;">{display_names.get(t, t)}</td>
            <td style="padding:8px 12px;border-bottom:1px solid {C['border_subtle']};width:120px;">
                <div style="background:{C['bg_elevated']};height:6px;border-radius:3px;overflow:hidden;">
                    <div style="background:linear-gradient(90deg, {color}, {color}80);height:100%;width:{bar_width}%;border-radius:3px;box-shadow:0 0 8px {color}40;"></div>
                </div>
            </td>
            <td style="padding:8px 12px;border-bottom:1px solid {C['border_subtle']};text-align:right;color:{color};font-weight:700;font-family:'JetBrains Mono',monospace;">{score_text}</td>
            <td style="padding:8px 12px;border-bottom:1px solid {C['border_subtle']};text-align:right;color:{color};font-size:0.75rem;font-weight:600;">{label}</td>
        </tr>""")
    sentiment_html = "\n".join(sentiment_rows)

    # ── Risk Per Ticker ───────────────────────────────────────
    vols = (
        risk_report
        .get("volatility", {})
        .get("per_ticker_annualized", {})
    )


    risk_rows = []
    for t in available:
        v = vols.get(t, 0) * 100
        c = C["red"] if v > vol * 100 else C["green"]
        risk_rows.append(f"""
        <tr>
            <td style="padding:8px 12px;border-bottom:1px solid {C['border_subtle']};color:{C['text_primary']};font-family:'Inter',sans-serif;">{display_names.get(t, t)}</td>
            <td style="padding:8px 12px;border-bottom:1px solid {C['border_subtle']};text-align:right;color:{c};font-family:'JetBrains Mono',monospace;font-weight:600;">{v:.2f}%</td>
        </tr>""")
    risk_html = "\n".join(risk_rows)

    # ── Recommendations ───────────────────────────────────────
        # ── AI Research Commentary ─────────────────────────────────
    rec_parts = []

    if recommendations:
        for rec in recommendations:
            ticker = rec.get("ticker", "")
            score = rec.get("sentiment_score")

            label, color, score_text, _ = get_report_sentiment(
                score,
                C,
            )

            optimizer_weight_pct = escape(
                str(rec.get("portfolio_weight_pct", "N/A"))
            )
            commentary_html = render_ai_commentary(
                str(rec.get("recommendation", ""))
            )

            glow_by_label = {
                SentimentLabel.POSITIVE.value: (
                    "rgba(16,185,129,0.08)"
                ),
                SentimentLabel.NEGATIVE.value: (
                    "rgba(244,63,94,0.08)"
                ),
                SentimentLabel.NEUTRAL.value: (
                    "rgba(255,255,255,0.02)"
                ),
                SentimentLabel.INSUFFICIENT_EVIDENCE.value: (
                    "rgba(245,158,11,0.08)"
                ),
            }
            glow = glow_by_label[label]

            ticker_name = escape(
                str(display_names.get(ticker, ticker))
            )

            rec_parts.append(
                f"""
                <div style="
                    margin-bottom:12px;
                    padding:14px;
                    background:{glow};
                    border:1px solid {C['border_subtle']};
                    border-left:3px solid {color};
                    border-radius:0 12px 12px 0;
                ">
                    <div style="
                        display:flex;
                        justify-content:space-between;
                        align-items:center;
                        margin-bottom:6px;
                    ">
                        <span style="
                            font-size:0.85rem;
                            font-weight:700;
                            color:{C['text_primary']};
                            font-family:'Inter',sans-serif;
                        ">
                            {ticker_name}
                        </span>
                        <span style="
                            background:{color}15;
                            color:{color};
                            padding:2px 8px;
                            border-radius:6px;
                            font-size:0.65rem;
                            font-weight:700;
                        ">
                            {label}
                        </span>
                    </div>
                    <div style="
                        font-size:0.75rem;
                        color:{C['text_secondary']};
                        margin-bottom:4px;
                    ">
                        Optimizer target:
                        <strong style="
                            color:{C['text_primary']};
                            font-family:'JetBrains Mono',monospace;
                        ">
                            {optimizer_weight_pct}%
                        </strong>
                        · Sentiment:
                        <strong style="
                            color:{color};
                            font-family:'JetBrains Mono',monospace;
                        ">
                            {score_text}
                        </strong>
                    </div>
                    <div style="
                        font-size:0.78rem;
                        color:{C['text_secondary']};
                        line-height:1.6;
                    ">
                        {commentary_html}
                    </div>
                </div>
                """
            )

    if rec_parts:
        rec_html = "\n".join(rec_parts)
    else:
        rec_html = (
            f'<div style="color:{C["text_tertiary"]};'
            'font-size:0.8rem;padding:12px;">'
            "AI research commentary was not generated. "
            "Quantitative results remain available."
            "</div>"
        )

    # ── News ──────────────────────────────────────────────────
    news_parts = []

    for ticker in available:
        articles = all_news.get(ticker, [])

        if not articles:
            continue

        ticker_name = escape(
            str(display_names.get(ticker, ticker))
        )

        news_parts.append(
            f'<div style="margin-bottom:14px;">'
            f'<div style="font-size:0.78rem;font-weight:700;'
            f'color:{C["accent"]};margin-bottom:6px;'
            f'font-family:\'Inter\',sans-serif;">'
            f"{ticker_name} — {len(articles)} articles"
            "</div>"
        )

        for article in articles[:5]:
            title = escape(
                str(article.get("title", ""))
            )

            news_parts.append(
                f'<div style="font-size:0.74rem;'
                f'color:{C["text_secondary"]};padding:3px 0;'
                f'border-bottom:1px solid '
                f'{C["border_subtle"]};">'
                f"• {title}"
                "</div>"
            )

        news_parts.append("</div>")

    if news_parts:
        news_html = "\n".join(news_parts)
    else:
        news_html = (
            f'<div style="color:{C["text_tertiary"]};'
            'font-size:0.75rem;">'
            "No ticker-specific news data is available."
            "</div>"
        )

    # ── Charts ────────────────────────────────────────────────

    final_sharpe = float(
        opt_result.get("sharpe_ratio", 0.0)
    )
    baseline_sharpe = float(
        baseline.get("sharpe_ratio", 0.0)
    )
    frontier_div = ""
    frontier_fig = None
    if not frontier_df.empty:
        try:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=frontier_df["volatility"]*100, y=frontier_df["return"]*100, mode='markers',
                marker=dict(color=frontier_df["sharpe"], colorscale=[[0, C["red"]], [0.5, C["accent"]], [1, C["green"]]], size=4, opacity=0.5),
                name="Frontier"
            ))
            fig.add_trace(go.Scatter(
                x=[opt_result.get("volatility", 0) * 100],
                y=[
                    opt_result.get(
                        "expected_return",
                        0,
                    ) * 100
                ],
                mode="markers+text",
                marker=dict(
                    color=C["accent"],
                    size=14,
                    symbol="star",
                    line=dict(
                        color="white",
                        width=1,
                    ),
                ),
                text=[
                    f"FINAL<br>Sharpe {final_sharpe:.3f}"
                ],
                textposition="top center",
                name=(
                    f"Final "
                    f"(Sharpe={final_sharpe:.3f})"
                ),
            ))
            fig.add_trace(go.Scatter(
                x=[
                    baseline.get(
                        "volatility",
                        0,
                    ) * 100
                ],
                y=[
                    baseline.get(
                        "expected_return",
                        0,
                    ) * 100
                ],
                mode="markers+text",
                marker=dict(
                    color=C["text_secondary"],
                    size=10,
                    symbol="diamond",
                ),
                text=[
                    (
                        "BASELINE"
                        f"<br>Sharpe {baseline_sharpe:.3f}"
                    )
                ],
                textposition="bottom center",
                name=(
                    f"Baseline "
                    f"<br>Sharpe {baseline_sharpe:.3f}"
                ),
            ))
            fig.update_layout(
                title="EFFICIENT FRONTIER", xaxis_title="VOLATILITY (%)", yaxis_title="RETURN (%)",
                height=400, paper_bgcolor=C["bg_elevated"], plot_bgcolor=C["bg_elevated"],
                font=dict(family="JetBrains Mono, monospace", color=C["text_primary"], size=10),
                margin=dict(l=60, r=35, t=75, b=50),
                uniformtext_minsize=8,
                uniformtext_mode="show",
                xaxis=dict(gridcolor=C["border_subtle"], linecolor=C["border_active"],automargin=True,),
                yaxis=dict(gridcolor=C["border_subtle"], linecolor=C["border_active"],automargin=True,),
                legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=C["border_subtle"], borderwidth=1, font=dict(size=9))
            )
            frontier_fig = fig
            frontier_div = fig.to_html(full_html=False, include_plotlyjs=False)
        except Exception:
            frontier_div = ""

    weights_bar_div = ""
    weights_bar_fig = None
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
                orientation='h', marker=dict(color=C["accent"], line=dict(color=C["accent"], width=1)),
                text=[f"{v:.1f}%" for v in final_vals], textposition='outside',
                textfont=dict(color=C["text_primary"], size=9)
            ), row=1, col=1)
            fig_w.add_trace(go.Bar(
                y=[display_names.get(t, t) for t in tickers_list], x=equal_vals,
                orientation='h', marker=dict(color=C["text_secondary"], line=dict(color=C["text_secondary"], width=1)),
                text=[f"{v:.1f}%" for v in equal_vals], textposition='outside',
                textfont=dict(color=C["text_primary"], size=9)
            ), row=1, col=2)
            fig_w.update_layout(
                showlegend=False, height=max(320, 45 * len(tickers_list)),
                paper_bgcolor=C["bg_elevated"], plot_bgcolor=C["bg_elevated"],
                font=dict(family="JetBrains Mono, monospace", color=C["text_primary"], size=10),
                margin=dict(l=100, r=20, t=40, b=40)
            )
            fig_w.update_xaxes(title_text="WEIGHT (%)", gridcolor=C["border_subtle"], linecolor=C["border_active"])
            fig_w.update_yaxes(gridcolor=C["border_subtle"], linecolor=C["border_active"])
            weights_bar_fig = fig_w
            weights_bar_div = fig_w.to_html(full_html=False, include_plotlyjs=False)
        except Exception:
            weights_bar_div = ""

    corr_div = ""
    corr_fig = None
    if correlation_matrix is None and isinstance(returns_df, pd.DataFrame) and not returns_df.empty:
        correlation_matrix = returns_df.corr()
    if isinstance(correlation_matrix, pd.DataFrame) and not correlation_matrix.empty:
        try:
            corr = correlation_matrix.copy()
            corr.columns = [display_names.get(t, t) for t in corr.columns]
            corr.index = corr.columns
            fig_c = go.Figure(go.Heatmap(
                z=corr.values,
                x=corr.columns.tolist(),
                y=corr.index.tolist(),
                colorscale=[[0, C["red"]], [0.5, C["bg_elevated"]], [1, C["green"]]],
                zmin=-1,
                zmax=1,
                text=corr.round(2).values,
                texttemplate="%{text}",
                textfont=dict(size=8, color=C["text_primary"]),
                colorbar=dict(
                    title=dict(text="Correlation", font=dict(color=C["text_secondary"])),
                    tickfont=dict(color=C["text_secondary"]),
                ),
            ))
            fig_c.update_layout(
                title="CORRELATION MATRIX", height=350,
                paper_bgcolor=C["bg_elevated"], plot_bgcolor=C["bg_elevated"],
                font=dict(family="JetBrains Mono, monospace", color=C["text_primary"], size=10),
                margin=dict(l=50, r=20, t=50, b=40),
            )
            corr_fig = fig_c
            corr_div = fig_c.to_html(full_html=False, include_plotlyjs=False)
        except Exception:
            corr_div = ""

    # The allocation chart is placed first in the report, so it must carry
    # the inline Plotly library. This keeps reports fully offline-capable and
    # ensures Plotly is defined before any chart script executes.
    if weights_bar_fig is not None:
        weights_bar_div = weights_bar_fig.to_html(full_html=False, include_plotlyjs="inline")
    elif frontier_fig is not None:
        frontier_div = frontier_fig.to_html(full_html=False, include_plotlyjs="inline")
    elif corr_fig is not None:
        corr_div = corr_fig.to_html(full_html=False, include_plotlyjs="inline")

    # ── Score Breakdown ───────────────────────────────────────
    score_breakdown_rows = "\n".join(
        f'<tr><td style="padding:8px 12px;border-bottom:1px solid {C["border_subtle"]};color:{C["text_primary"]};font-family:\'Inter\',sans-serif;">{k.replace("_", " ").title()}</td>'
        f'<td style="padding:8px 12px;border-bottom:1px solid {C["border_subtle"]};text-align:right;color:{C["accent"]};font-weight:700;font-family:\'JetBrains Mono\',monospace;">{v:.1f}/100</td>'
        f'<td style="padding:8px 12px;border-bottom:1px solid {C["border_subtle"]};text-align:right;color:{C["text_tertiary"]};font-family:\'JetBrains Mono\',monospace;">{health.get("component_weights", {}).get(k, 0)*100:.0f}%</td></tr>'
        for k, v in health.get("components", {}).items()
    )

    score_improvements_html = "\n".join(
        f'<div style="padding:4px 0;color:{C["text_secondary"]};font-size:0.75rem;">• {tip}</div>' 
        for tip in health.get("improvements", [])
    )

    adaptive_candidates = results.get("adaptive_candidates", []) or []
    selected_cap = results.get("selected_cap")
    adaptive_rows = "\n".join(
        f'<tr><td style="padding:8px 12px;border-bottom:1px solid {C["border_subtle"]};color:{C["text_primary"]};font-family:\'JetBrains Mono\',monospace;">{c.get("max_weight_cap", 0)*100:.1f}%</td>'
        f'<td style="padding:8px 12px;border-bottom:1px solid {C["border_subtle"]};text-align:right;color:{C["accent"]};font-weight:700;font-family:\'JetBrains Mono\',monospace;">{c.get("health_score", 0):.1f}</td>'
        f'<td style="padding:8px 12px;border-bottom:1px solid {C["border_subtle"]};text-align:right;color:{C["text_primary"]};font-family:\'JetBrains Mono\',monospace;">{c.get("sharpe_ratio", 0):.3f}</td>'
        f'<td style="padding:8px 12px;border-bottom:1px solid {C["border_subtle"]};text-align:right;color:{C["text_primary"]};font-family:\'JetBrains Mono\',monospace;">{c.get("volatility", 0)*100:.1f}%</td></tr>'
        for c in adaptive_candidates
    )

    adaptive_html = (
        f'<div style="margin-top:16px;padding:12px;background:{C["bg_surface"]};border-radius:10px;">'
        f'<div style="color:{C["accent"]};font-weight:700;margin-bottom:8px;font-family:\'Inter\',sans-serif;font-size:0.8rem;">ADAPTIVE CAP SEARCH</div>'
        f'<table style="width:100%;font-size:0.75rem;"><thead><tr><th style="text-align:left;color:{C["text_tertiary"]};font-weight:600;">MAX WEIGHT</th>'
        f'<th style="text-align:right;color:{C["text_tertiary"]};font-weight:600;">HEALTH</th>'
        f'<th style="text-align:right;color:{C["text_tertiary"]};font-weight:600;">SHARPE</th>'
        f'<th style="text-align:right;color:{C["text_tertiary"]};font-weight:600;">VOL</th></tr></thead>'
        f'<tbody>{adaptive_rows}</tbody></table>'
        f'<div style="margin-top:8px;color:{C["text_secondary"]};font-size:0.72rem;font-family:\'JetBrains Mono\',monospace;">'
        f'SELECTED CAP: <strong style="color:{C["text_primary"]}">{(selected_cap or 0)*100:.1f}%</strong> | '
        f'POTENTIAL SCORE: <strong style="color:{C["text_primary"]}">{health.get("potential_score", ai_score):.1f}/100</strong></div></div>'
        if adaptive_candidates else ''
    )

    exp_ret = opt_result.get("expected_return", 0)
    exp_ret_cls = "pos" if exp_ret > 0 else "neg"
    if avg_sent is None:
        avg_sent_cls = "accent"
        avg_sent_text = "N/A"
    elif avg_sent > 0.05:
        avg_sent_cls = "pos"
        avg_sent_text = f"{avg_sent:+.3f}"
    elif avg_sent < -0.05:
        avg_sent_cls = "neg"
        avg_sent_text = f"{avg_sent:+.3f}"
    else:
        avg_sent_cls = "accent"
        avg_sent_text = f"{avg_sent:+.3f}"


    risk_currency_symbol = "$"


    # ── HTML Assembly ─────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AXIOM REPORT — {pf_name}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ 
    font-family:'Inter', system-ui, sans-serif; 
    background: {C["bg_base"]}; 
    color: {C["text_primary"]}; 
    font-size:0.82rem; 
    line-height:1.6;
    background-image: 
      radial-gradient(ellipse 80% 50% at 50% -20%, rgba(255,107,53,0.06), transparent),
      radial-gradient(ellipse 60% 40% at 80% 80%, rgba(0,217,255,0.03), transparent);
  }}

  .page {{ max-width:1000px; margin:0 auto; padding:32px 24px; }}

  /* Header */
  .header {{ 
    background: {C["bg_glass"]}; 
    border: 1px solid {C["border_subtle"]}; 
    border-radius: 16px; 
    backdrop-filter: blur(20px);
    padding: 24px; 
    margin-bottom: 24px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.04);
  }}
  .header-top {{ display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px; }}
  .header h1 {{ font-size:1.6rem; font-weight:800; color:{C["accent"]}; letter-spacing:-0.03em; font-family:'Inter',sans-serif; }}
  .header .meta {{ font-size:0.75rem; color:{C["text_secondary"]}; margin-top:4px; font-family:'JetBrains Mono',monospace; }}
  .header .badge {{ 
    background: linear-gradient(135deg, {C["accent"]}, {C["accent_dim"]}); 
    color:{C["text_inverse"]}; 
    padding:4px 10px; 
    border-radius: 6px; 
    font-size:0.65rem; 
    font-weight:800; 
    letter-spacing:0.04em;
    box-shadow: 0 2px 8px {C["accent_glow"]};
  }}
  .header-info {{ display:flex; gap:24px; margin-top:12px; padding-top:12px; border-top:1px solid {C["border_subtle"]}; font-size:0.75rem; color:{C["text_secondary"]}; font-family:'JetBrains Mono',monospace; }}
  .header-info strong {{ color:{C["text_primary"]}; }}

  /* Glass Panel */
  .panel {{ 
    background: {C["bg_glass"]}; 
    border: 1px solid {C["border_subtle"]}; 
    border-radius: 16px; 
    backdrop-filter: blur(20px);
    margin-bottom: 20px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.04);
    overflow: hidden;
    transition: all 0.2s ease;
  }}
  .panel:hover {{ border-color: {C["border_active"]}; }}
  .panel-header {{ 
    background: linear-gradient(90deg, {C["accent_glow"]}, transparent); 
    padding: 14px 20px; 
    border-bottom: 1px solid {C["border_subtle"]};
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .panel-header.green {{ background: linear-gradient(90deg, rgba(16,185,129,0.08), transparent); }}
  .panel-header.red {{ background: linear-gradient(90deg, rgba(244,63,94,0.08), transparent); }}
  .panel-header.cyan {{ background: linear-gradient(90deg, rgba(0,217,255,0.08), transparent); }}
  .panel-header.violet {{ background: linear-gradient(90deg, rgba(139,92,246,0.08), transparent); }}
  .panel-title {{ font-size:0.78rem; font-weight:700; color:{C["accent"]}; text-transform:uppercase; letter-spacing:0.08em; font-family:'Inter',sans-serif; }}
  .panel-title.green {{ color: {C["green"]}; }}
  .panel-title.red {{ color: {C["red"]}; }}
  .panel-title.cyan {{ color: {C["cyan"]}; }}
  .panel-title.violet {{ color: {C["violet"]}; }}
  .panel-sub {{ font-size:0.65rem; color:{C["text_tertiary"]}; font-weight:500; letter-spacing:0.04em; }}
  .panel-body {{ padding: 20px; }}

  /* KPI Grid */
  .kpi-grid {{ display:grid; grid-template-columns:repeat(4, 1fr); gap:1px; background:{C["border_subtle"]}; border:1px solid {C["border_subtle"]}; border-radius: 12px; overflow: hidden; }}
  .kpi-cell {{ background: {C["bg_surface"]}; padding: 16px; text-align: center; transition: all 0.15s ease; }}
  .kpi-cell:hover {{ background: rgba(255,255,255,0.03); }}
  .kpi-value {{ font-size:1.4rem; font-weight:700; color:{C["text_primary"]}; font-family:'JetBrains Mono',monospace; line-height:1; letter-spacing:-0.02em; }}
  .kpi-value.accent {{ color: {C["accent"]}; text-shadow: 0 0 20px {C["accent_glow"]}; }}
  .kpi-value.pos {{ color: {C["green"]}; }}
  .kpi-value.neg {{ color: {C["red"]}; }}
  .kpi-value.cyan {{ color: {C["cyan"]}; }}
  .kpi-label {{ font-size:0.6rem; color:{C["text_tertiary"]}; text-transform:uppercase; letter-spacing:0.08em; font-weight:600; margin-top:6px; font-family:'Inter',sans-serif; }}

  /* Tables */
  table {{ width:100%; border-collapse:collapse; font-size:0.78rem; }}
  th {{ background: rgba(255,255,255,0.02); color:{C["accent"]}; text-align:left; padding:10px 12px; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.06em; font-weight:700; font-family:'Inter',sans-serif; border-bottom:1px solid {C["border_subtle"]}; }}
  td {{ padding:8px 12px; }}
  tr {{ transition: all 0.15s ease; }}
  tr:hover {{ background: rgba(255,255,255,0.02); }}

  /* Chart Container */
  .chart-container {{ margin: 16px 0; background: {C["bg_elevated"]}; border-radius: 12px; padding: 12px; border: 1px solid {C["border_subtle"]}; }}

  /* Status Badges */
  .badge-pos {{ background: rgba(16,185,129,0.12); color:{C["green"]}; padding:2px 8px; border-radius:6px; font-size:0.65rem; font-weight:700; border:1px solid rgba(16,185,129,0.2); }}
  .badge-neg {{ background: rgba(244,63,94,0.12); color:{C["red"]}; padding:2px 8px; border-radius:6px; font-size:0.65rem; font-weight:700; border:1px solid rgba(244,63,94,0.2); }}
  .badge-neutral {{ background: rgba(255,255,255,0.04); color:{C["text_secondary"]}; padding:2px 8px; border-radius:6px; font-size:0.65rem; font-weight:700; border:1px solid rgba(255,255,255,0.06); }}

  /* Disclaimer */
  .disclaimer {{ 
    background: {C["bg_glass"]}; 
    border: 1px solid {C["border_subtle"]}; 
    border-radius: 16px; 
    backdrop-filter: blur(20px);
    padding: 20px; 
    margin-top: 32px; 
    font-size:0.72rem; 
    color:{C["text_tertiary"]}; 
    line-height:1.7;
    box-shadow: 0 4px 24px rgba(0,0,0,0.2);
  }}
  .disclaimer strong {{ color: {C["accent"]}; }}

  /* Animations */
  @keyframes fadeInUp {{ from {{ opacity: 0; transform: translateY(16px); }} to {{ opacity: 1; transform: translateY(0); }} }}
  .animate-in {{ animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards; }}

  @media print {{ body {{ background: #fff; color: #000; }} .panel {{ border-color: #ccc; background: #fff; }} }}
  @media (max-width: 768px) {{ .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }} .page {{ padding: 16px; }} }}
</style>
</head>
<body>
<div class="page">

  <!-- Header -->
  <div class="header animate-in">
    <div class="header-top">
      <div>
        <h1>◈ AXIOM PORTFOLIO INTELLIGENCE</h1>
        <div class="meta">TERMINAL EDITION V1.0.0 · QUANTITATIVE ANALYSIS REPORT</div>
      </div>
      <div class="badge">CONFIDENTIAL</div>
    </div>
    <div class="header-info">
      <div>PORTFOLIO: <strong>{pf_name}</strong></div>
      <div>CURRENCY: <strong>{pf_curr}</strong></div>
      <div>GENERATED: <strong>{now_str}</strong></div>
    </div>
  </div>

  <!-- Health Score -->
  <div class="panel animate-in">
    <div class="panel-header">
      <span class="panel-title">◈ Portfolio Health Score</span>
      <span class="panel-sub">COMPOSITE METRIC · 0-100 SCALE</span>
    </div>
    <div class="panel-body">
      <div class="kpi-grid">
        <div class="kpi-cell">
          <div class="kpi-value accent">{ai_score:.0f}</div>
          <div class="kpi-label">Portfolio Health · {score_label}</div>
        </div>
        <div class="kpi-cell">
          <div class="kpi-value cyan">{sharpe:.3f}</div>
          <div class="kpi-label">Sharpe Ratio</div>
        </div>
        <div class="kpi-cell">
          <div class="kpi-value {exp_ret_cls}">{exp_ret*100:.2f}%</div>
          <div class="kpi-label">Exp Return</div>
        </div>
        <div class="kpi-cell">
          <div class="kpi-value neg">{vol*100:.2f}%</div>
          <div class="kpi-label">Volatility</div>
        </div>
        <div class="kpi-cell">
          <div class="kpi-value neg">{risk_currency_symbol}{abs(var95.get("var_usd", 0)):,.0f}</div>
          <div class="kpi-label">95% VaR · 1 DAY · USD</div>
        </div>
        <div class="kpi-cell">
          <div class="kpi-value neg">{risk_currency_symbol}{abs(var99.get("var_usd", 0)):,.0f}</div>
          <div class="kpi-label">99% VaR · 1 DAY · USD</div>
        </div>
        <div class="kpi-cell">
          <div class="kpi-value neg">{mdd.get("max_drawdown_pct", 0):.2f}%</div>
          <div class="kpi-label">Max Drawdown</div>
        </div>
        <div class="kpi-cell">
          <div class="kpi-value {avg_sent_cls}">{avg_sent_text}</div>
          <div class="kpi-label">Avg Sentiment</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Health Breakdown -->
  <div class="panel animate-in">
    <div class="panel-header">
      <span class="panel-title">◈ Portfolio Health Score v3 Breakdown</span>
      <span class="panel-sub">EXPLAINABLE MODEL</span>
    </div>
    <div class="panel-body">
      <table>
        <thead><tr><th>COMPONENT</th><th style="text-align:right">SCORE</th><th style="text-align:right">WEIGHT</th></tr></thead>
        <tbody>{score_breakdown_rows}</tbody>
      </table>
      <div style="margin-top:14px;padding:10px 14px;background:{C["bg_elevated"]};border-radius:8px;font-size:0.74rem;color:{C["text_secondary"]};font-family:'JetBrains Mono',monospace;border:1px solid {C["border_subtle"]};">
        BASE: <strong style="color:{C['text_primary']}">{health.get("base_score", 0):.1f}</strong> | 
        PENALTIES: <strong style="color:{C['red']}">-{health.get("penalty_total", 0):.1f}</strong> | 
        FINAL: <strong style="color:{C['accent']}">{ai_score:.1f}/100</strong>
      </div>
      <div style="margin-top:10px;">{score_improvements_html}</div>
      {adaptive_html}
    </div>
  </div>

  <!-- Weight Allocation -->
  <div class="panel animate-in">
    <div class="panel-header cyan">
      <span class="panel-title cyan">◫ Portfolio Allocation</span>
      <span class="panel-sub">OPTIMIZED VS EQUAL WEIGHT</span>
    </div>
    <div class="panel-body">
      <div class="chart-container">{weights_bar_div or f'<div style="color:{C["text_tertiary"]};font-size:0.75rem;">Chart not available</div>'}</div>
    </div>
  </div>

  <!-- Composition Table -->
  <div class="panel animate-in">
    <div class="panel-header violet">
      <span class="panel-title violet">◫ Portfolio Composition</span>
      <span class="panel-sub">CURRENT VS QUANTITATIVE VS FINAL TARGETS</span>
    </div>
    <div class="panel-body">
      <table>
        <thead>
            <tr>
                <th>TICKER</th>
                    <th style="text-align:right">CURRENT</th>
                    <th style="text-align:right">QUANT</th>
                    <th style="text-align:right">FINAL</th>
                    <th style="text-align:right">MODEL SHIFT</th>
                    <th style="text-align:right">MODEL ADJUSTMENT</th>
                    <th style="text-align:right">REBALANCE GAP</th>
                    <th style="text-align:right">ACTION</th>
                    <th>REASON</th>
                </tr>
            </thead>
        <tbody>{weights_html}</tbody>
      </table>
    </div>
  </div>

  <!-- Efficient Frontier -->
  <div class="panel animate-in">
    <div class="panel-header">
      <span class="panel-title">◈ Efficient Frontier</span>
      <span class="panel-sub">RISK VS RETURN</span>
    </div>
    <div class="panel-body">
      <div class="chart-container">{frontier_div or f'<div style="color:{C["text_tertiary"]};font-size:0.75rem;">Chart not available</div>'}</div>
    </div>
  </div>

  <!-- Risk Breakdown -->
  <div class="panel animate-in">
    <div class="panel-header red">
      <span class="panel-title red">◫ Risk Breakdown</span>
      <span class="panel-sub">PER-TICKER VOLATILITY</span>
    </div>
    <div class="panel-body">
      <table>
        <thead><tr><th>TICKER</th><th style="text-align:right">ANN VOLATILITY</th></tr></thead>
        <tbody>{risk_html}</tbody>
      </table>
      <div style="margin-top:14px;padding:10px 14px;background:{C["bg_elevated"]};border-radius:8px;font-size:0.74rem;color:{C["text_secondary"]};font-family:'JetBrains Mono',monospace;border:1px solid {C["border_subtle"]};">
        PORTFOLIO VOLATILITY: <strong style="color:{C['text_primary']}">{vol*100:.2f}%</strong> | 
        CONCENTRATION RISK: <strong style="color:{C['text_primary']}">{risk_report.get("concentration", {}).get("label", "N/A")}</strong>
      </div>
    </div>
  </div>

  <!-- Correlation -->
  <div class="panel animate-in">
    <div class="panel-header green">
      <span class="panel-title green">◫ Correlation Matrix</span>
      <span class="panel-sub">RETURN CORRELATIONS</span>
    </div>
    <div class="panel-body">
      <div class="chart-container">{corr_div or f'<div style="color:{C["text_tertiary"]};font-size:0.75rem;">Chart not available</div>'}</div>
    </div>
  </div>

  <!-- Sentiment -->
  <div class="panel animate-in">
    <div class="panel-header cyan">
      <span class="panel-title cyan">◉ Sentiment Analysis</span>
      <span class="panel-sub">FINBERT NLP SCORES</span>
    </div>
    <div class="panel-body">
      <table>
        <thead><tr><th>TICKER</th><th>BAR</th><th style="text-align:right">SCORE</th><th style="text-align:right">LABEL</th></tr></thead>
        <tbody>{sentiment_html}</tbody>
      </table>
    </div>
  </div>

  <!-- News -->
  <div class="panel animate-in">
    <div class="panel-header">
      <span class="panel-title">◫ Recent Headlines</span>
      <span class="panel-sub">NEWS FEED</span>
    </div>
    <div class="panel-body">{news_html}</div>
  </div>

  <!-- AI Research Commentary  -->
  <div class="panel animate-in">
    <div class="panel-header violet">
      <span class="panel-title violet">◉ AI Research Commentary</span>
      <span class="panel-sub">CONFIGURED GROQ MODEL</span>
    </div>
    <div class="panel-body">{rec_html}</div>
  </div>

  <!-- Disclaimer -->
  <div class="disclaimer animate-in">
    <strong>DISCLAIMER:</strong>
      AXIOM is provided for research and educational purposes only and
      does not constitute financial, investment, tax, or legal advice.
      Market data, news, sentiment, model outputs, and generated commentary
      may be incomplete, delayed, or inaccurate. Historical performance
      does not guarantee future results. Consult a qualified professional
      before making financial decisions.<br><br>
    <span style="color:{C['text_tertiary']};font-family:'JetBrains Mono',monospace;">
      AXIOM Portfolio Intelligence V1.0.0 · Generated {gen_str}
    </span>
  </div>

</div>
</body>
</html>"""
    return html


# Backward compatibility alias
generate_bloomberg_report = generate_axiom_report
