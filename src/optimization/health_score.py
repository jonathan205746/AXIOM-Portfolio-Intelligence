"""
health_score.py
---------------
AI Portfolio Health Score v3.

Explainable 0-100 scoring that rewards balanced risk-adjusted performance,
not just raw return. A 90+ score requires strength across Sharpe/Sortino,
drawdown, tail risk, diversification, concentration, correlation, and data
quality.
"""
from __future__ import annotations

from typing import Dict, Any, Iterable


WEIGHTS = {
    "risk_adjusted_return": 0.18,
    "sortino": 0.10,
    "volatility_control": 0.10,
    "drawdown_control": 0.10,
    "tail_risk": 0.10,
    "diversification": 0.10,
    "concentration_control": 0.10,
    "correlation_diversification": 0.05,
    "sentiment_quality": 0.05,
    "optimization_gain": 0.05,
    "data_quality": 0.04,
    "stability": 0.03,
}


def _clip(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, float(x)))


def _piecewise(x: float, points: Iterable[tuple[float, float]]) -> float:
    pts = sorted((float(a), float(b)) for a, b in points)
    if not pts:
        return 0.0
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            if x1 == x0:
                return y1
            t = (x - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return pts[-1][1]


def _label(score: float) -> str:
    if score >= 95: return "ELITE"
    if score >= 90: return "EXCELLENT"
    if score >= 85: return "VERY GOOD"
    if score >= 75: return "GOOD"
    if score >= 65: return "HEALTHY"
    if score >= 55: return "FAIR"
    if score >= 40: return "WEAK"
    return "CRITICAL"


def _grade(score: float) -> str:
    if score >= 95: return "A+"
    if score >= 90: return "A"
    if score >= 85: return "A-"
    if score >= 80: return "B+"
    if score >= 75: return "B"
    if score >= 70: return "B-"
    if score >= 65: return "C+"
    if score >= 60: return "C"
    if score >= 50: return "D"
    return "F"


def calculate_health_score(
    *,
    sharpe: float,
    volatility: float,
    var95: float,
    max_drawdown_pct: float,
    sentiment_scores: Dict[str, float],
    final_weights: Dict[str, float],
    risk_report: Dict[str, Any] | None = None,
    baseline_sharpe: float | None = None,
    news_counts: Dict[str, int] | None = None,
    sortino: float | None = None,
    expected_shortfall95: float | None = None,
    candidate_scores: list[float] | None = None,
) -> Dict[str, Any]:
    risk_report = risk_report or {}
    weights = [max(0.0, float(w)) for w in final_weights.values()]
    n = len(weights)
    total = sum(weights)
    if total > 0:
        weights = [w / total for w in weights]

    sharpe_score = _piecewise(float(sharpe), [
        (-0.25, 0), (0.0, 15), (0.5, 45), (1.0, 70),
        (1.25, 80), (1.5, 88), (1.75, 94), (2.0, 97), (2.5, 100),
    ])

    if sortino is None:
        sortino = risk_report.get("downside", {}).get("sortino_ratio")
    sortino_val = float(sortino) if sortino is not None else float(sharpe)
    sortino_score = _piecewise(sortino_val, [
        (-0.25, 0), (0.0, 15), (0.75, 55), (1.0, 70), (1.5, 84),
        (2.0, 92), (2.5, 97), (3.0, 100),
    ])

    volatility_score = _piecewise(abs(float(volatility)), [
        (0.08, 100), (0.12, 97), (0.15, 93), (0.18, 86),
        (0.20, 80), (0.22, 73), (0.25, 62), (0.30, 45), (0.40, 20), (0.60, 0),
    ])

    dd = abs(float(max_drawdown_pct))
    drawdown_score = _piecewise(dd, [
        (3, 100), (5, 98), (8, 94), (10, 90), (12, 86),
        (15, 80), (18, 73), (20, 68), (25, 55), (35, 32), (50, 10), (70, 0),
    ])

    var_abs = abs(float(var95))
    var_score = _piecewise(var_abs, [
        (0.005, 100), (0.010, 96), (0.015, 90), (0.020, 82),
        (0.025, 72), (0.030, 60), (0.040, 40), (0.060, 10), (0.10, 0),
    ])
    if expected_shortfall95 is None:
        expected_shortfall95 = risk_report.get("tail_risk", {}).get("expected_shortfall_95", {}).get("es_pct")
    if expected_shortfall95 is not None:
        es_score = _piecewise(abs(float(expected_shortfall95)), [
            (0.008, 100), (0.015, 96), (0.022, 90), (0.030, 82),
            (0.040, 70), (0.050, 55), (0.070, 30), (0.10, 5),
        ])
        tail_score = 0.55 * var_score + 0.45 * es_score
    else:
        es_score = None
        tail_score = var_score

    if n >= 2:
        hhi = sum(w * w for w in weights)
        min_hhi = 1.0 / n
        hhi_norm = (hhi - min_hhi) / max(1e-9, 1.0 - min_hhi)
        diversification_score = 100.0 * (1.0 - _clip(hhi_norm, 0, 1))
    elif n == 1:
        hhi, min_hhi, diversification_score = 1.0, 1.0, 0.0
    else:
        hhi, min_hhi, diversification_score = 1.0, 1.0, 0.0

    sorted_w = sorted(weights, reverse=True)
    max_weight = sorted_w[0] if sorted_w else 1.0
    top2 = sum(sorted_w[:2]) if sorted_w else 1.0
    max_weight_score = _piecewise(max_weight, [
        (0.15, 100), (0.20, 99), (0.25, 95), (0.275, 91), (0.30, 86),
        (0.325, 78), (0.35, 68), (0.40, 48), (0.50, 20), (1.00, 0),
    ])
    top2_score = _piecewise(top2, [
        (0.30, 100), (0.40, 96), (0.50, 90), (0.55, 84), (0.60, 76),
        (0.70, 55), (0.80, 30), (1.00, 0),
    ])
    concentration_score = 0.65 * max_weight_score + 0.35 * top2_score

    corr = risk_report.get("correlation", {}).get("matrix", {}) or {}
    high_corr_pairs = risk_report.get("correlation", {}).get("high_correlation_pairs", []) or []
    pair_values: list[float] = []
    if isinstance(corr, dict):
        keys = list(corr.keys())
        for i, a in enumerate(keys):
            row = corr.get(a, {}) if isinstance(corr.get(a, {}), dict) else {}
            for b in keys[i + 1:]:
                try:
                    pair_values.append(abs(float(row.get(b, 0.0))))
                except Exception:
                    pass
    avg_abs_corr = sum(pair_values) / len(pair_values) if pair_values else 0.0
    correlation_score = _piecewise(avg_abs_corr, [
        (0.05, 100), (0.15, 96), (0.25, 90), (0.35, 82),
        (0.45, 70), (0.60, 50), (0.75, 25), (0.90, 5),
    ])
    correlation_score -= min(12.0, len(high_corr_pairs) * 2.0)

    if news_counts is None:
        sent_vals = [
            float(value)
            for value in sentiment_scores.values()
            if value is not None
        ]
    else:
        sent_vals = [
            float(sentiment_scores[ticker])
            for ticker in final_weights
            if sentiment_scores.get(ticker) is not None
            and news_counts.get(ticker, 0) > 0
        ]

    avg_sent = sum(sent_vals) / len(sent_vals) if sent_vals else 0.0
    coverage = (len(sent_vals) / n) if n else 0.0
    directional = _piecewise(avg_sent, [
        (-1.0, 25), (-0.5, 45), (-0.2, 62), (-0.05, 74),
        (0.0, 78), (0.10, 85), (0.25, 92), (0.50, 97), (1.0, 100),
    ])
    dispersion = 0.0
    if len(sent_vals) > 1:
        mean = avg_sent
        dispersion = (sum((x - mean) ** 2 for x in sent_vals) / len(sent_vals)) ** 0.5
    consistency_factor = _piecewise(dispersion, [(0.0, 1.0), (0.20, 0.98), (0.40, 0.92), (0.70, 0.82), (1.0, 0.75)])
    sentiment_score = directional * (0.85 + 0.15 * _clip(coverage, 0, 1)) * consistency_factor

    if baseline_sharpe is None:
        optimization_score = 75.0
        sharpe_gain = None
    else:
        sharpe_gain = float(sharpe) - float(baseline_sharpe)
        optimization_score = _piecewise(sharpe_gain, [
            (-0.5, 20), (-0.1, 50), (0.0, 65), (0.2, 78),
            (0.5, 90), (0.8, 97), (1.2, 100),
        ])

    completeness_keys = ["volatility", "value_at_risk", "drawdown", "concentration", "correlation", "downside", "tail_risk"]
    risk_completeness = sum(1 for k in completeness_keys if risk_report.get(k)) / len(completeness_keys)
    news_depth = 1.0
    if news_counts is not None and n:
        depths = [min(max(int(news_counts.get(t, 0)), 0), 10) / 10.0 for t in final_weights]
        news_depth = sum(depths) / len(depths) if depths else 0.0
    data_quality_score = 100.0 * (0.40 * _clip(coverage, 0, 1) + 0.40 * risk_completeness + 0.20 * news_depth)

    # Stability asks: is the selected solution robust across nearby cap choices?
    if candidate_scores and len(candidate_scores) > 1:
        cmean = sum(candidate_scores) / len(candidate_scores)
        spread = (sum((x - cmean) ** 2 for x in candidate_scores) / len(candidate_scores)) ** 0.5
        stability_score = _piecewise(spread, [(0, 100), (1.5, 96), (3, 90), (5, 80), (8, 65), (12, 45), (20, 20)])
    else:
        spread = None
        stability_score = 78.0

    components = {
        "risk_adjusted_return": _clip(sharpe_score),
        "sortino": _clip(sortino_score),
        "volatility_control": _clip(volatility_score),
        "drawdown_control": _clip(drawdown_score),
        "tail_risk": _clip(tail_score),
        "diversification": _clip(diversification_score),
        "concentration_control": _clip(concentration_score),
        "correlation_diversification": _clip(correlation_score),
        "sentiment_quality": _clip(sentiment_score),
        "optimization_gain": _clip(optimization_score),
        "data_quality": _clip(data_quality_score),
        "stability": _clip(stability_score),
    }

    base_score = sum(components[k] * WEIGHTS[k] for k in WEIGHTS)
    penalties = []
    penalty_total = 0.0
    if max_weight > 0.40:
        p = min(10.0, 4.0 + (max_weight - 0.40) * 50.0)
        penalties.append({"name": "single_position_concentration", "points": round(p, 2)})
        penalty_total += p
    elif max_weight > 0.35:
        p = 3.0
        penalties.append({"name": "single_position_concentration", "points": p})
        penalty_total += p
    if top2 > 0.75:
        p = min(8.0, 3.0 + (top2 - 0.75) * 20.0)
        penalties.append({"name": "top_two_concentration", "points": round(p, 2)})
        penalty_total += p
    if len(high_corr_pairs) >= 3:
        p = min(4.0, float(len(high_corr_pairs) - 2))
        penalties.append({"name": "correlation_cluster", "points": p})
        penalty_total += p

    final_score = _clip(base_score - penalty_total)

    ordered = sorted(components.items(), key=lambda kv: kv[1])
    improvements: list[str] = []
    if max_weight > 0.30:
        improvements.append(f"Reduce the largest position from {max_weight*100:.1f}% toward 25-30%.")
    if top2 > 0.55:
        improvements.append(f"Reduce top-two exposure from {top2*100:.1f}% toward 45-55%.")
    if dd > 12:
        improvements.append(f"Improve drawdown control; current max drawdown is {dd:.1f}%.")
    if volatility > 0.18:
        improvements.append(f"Lower annualized volatility from {volatility*100:.1f}% toward 15-18%.")
    if avg_sent < 0:
        improvements.append(f"News sentiment is slightly negative ({avg_sent:+.3f}); avoid overweighting weak-sentiment names.")
    for name, value in ordered:
        if value < 78 and len(improvements) < 6:
            pretty = name.replace("_", " ").title()
            msg = f"Improve {pretty} (currently {value:.0f}/100)."
            if msg not in improvements:
                improvements.append(msg)

    # Transparent upside estimate: cap each weak component at a realistic 90.
    upside = 0.0
    for k, value in components.items():
        target = 90.0 if k not in {"data_quality", "stability"} else 95.0
        upside += max(0.0, target - value) * WEIGHTS[k]
    potential_score = min(100.0, final_score + upside)

    return {
        "score": round(final_score, 2),
        "base_score": round(base_score, 2),
        "potential_score": round(potential_score, 2),
        "label": _label(final_score),
        "grade": _grade(final_score),
        "version": "3.0",
        "components": {k: round(v, 2) for k, v in components.items()},
        "component_weights": WEIGHTS.copy(),
        "penalties": penalties,
        "penalty_total": round(penalty_total, 2),
        "diagnostics": {
            "hhi": round(hhi, 6),
            "min_possible_hhi": round(min_hhi, 6),
            "max_weight": round(max_weight, 6),
            "top_two_weight": round(top2, 6),
            "avg_abs_correlation": round(avg_abs_corr, 6),
            "avg_sentiment": round(avg_sent, 6),
            "sentiment_dispersion": round(dispersion, 6),
            "sentiment_coverage": round(coverage, 4),
            "sortino_ratio": round(sortino_val, 6),
            "expected_shortfall_95": None if expected_shortfall95 is None else round(float(expected_shortfall95), 6),
            "candidate_score_spread": None if spread is None else round(spread, 4),
            "sharpe_gain_vs_equal_weight": None if sharpe_gain is None else round(sharpe_gain, 6),
        },
        "improvements": improvements[:6],
    }


class HealthScoreEngine:
    @staticmethod
    def calculate(
        *,
        sharpe: float,
        volatility: float,
        var95: float,
        max_drawdown_pct: float,
        sentiment_scores: Dict[str, float],
        final_weights: Dict[str, float],
        risk_report: Dict[str, Any] | None = None,
        baseline_sharpe: float | None = None,
        news_counts: Dict[str, int] | None = None,
        sortino: float | None = None,
        expected_shortfall95: float | None = None,
        candidate_scores: list[float] | None = None,
    ) -> Dict[str, Any]:
        return calculate_health_score(
            sharpe=sharpe,
            volatility=volatility,
            var95=var95,
            max_drawdown_pct=max_drawdown_pct,
            sentiment_scores=sentiment_scores,
            final_weights=final_weights,
            risk_report=risk_report,
            baseline_sharpe=baseline_sharpe,
            news_counts=news_counts,
            sortino=sortino,
            expected_shortfall95=expected_shortfall95,
            candidate_scores=candidate_scores,
        )
