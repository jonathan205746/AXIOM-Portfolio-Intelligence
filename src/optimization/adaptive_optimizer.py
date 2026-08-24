"""Adaptive health-aware portfolio optimizer.

Searches several feasible concentration caps and selects the portfolio with the
highest AI Health Score v3 instead of blindly forcing one hard cap.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable
import numpy as np

from src.optimization.combined_signal import CombinedSignal
from src.optimization.health_score import HealthScoreEngine


DEFAULT_CAPS = (0.25, 0.275, 0.30, 0.325, 0.35)


class AdaptiveHealthOptimizer:
    def __init__(self, optimizer, risk_analyzer, sentiment_scores: Dict[str, float], news_counts: Dict[str, int] | None = None):
        self.optimizer = optimizer
        self.risk_analyzer = risk_analyzer
        self.sentiment_scores = sentiment_scores
        self.news_counts = news_counts or {}

    def _feasible_caps(self, caps: Iterable[float]) -> list[float]:
        n = max(1, len(self.optimizer.tickers))
        min_feasible = 1.0 / n
        values = sorted({round(max(float(c), min_feasible), 6) for c in caps})
        return values

    def search(self, *, alpha: float, portfolio_value: float, caps: Iterable[float] = DEFAULT_CAPS) -> Dict[str, Any]:
        baseline = self.optimizer.equal_weight_baseline()
        candidates: list[Dict[str, Any]] = []

        for cap in self._feasible_caps(caps):
            opt_result = self.optimizer.optimize(max_weight=cap)
            combiner = CombinedSignal(opt_result, self.sentiment_scores)
            combined = combiner.combine(alpha=alpha, max_weight=cap)
            final_weights = combined["final_weights"]

            arr = np.array([final_weights.get(t, 0.0) for t in self.optimizer.tickers], dtype=float)
            final_stats = {
                "expected_return": self.optimizer.portfolio_return(arr),
                "volatility": self.optimizer.portfolio_volatility(arr),
                "sharpe_ratio": self.optimizer.sharpe_ratio(arr),
            }
            risk_report = self.risk_analyzer.full_risk_report(final_weights, portfolio_value)
            health = HealthScoreEngine.calculate(
                sharpe=final_stats["sharpe_ratio"],
                volatility=risk_report.get("volatility", {}).get("portfolio_annualized", final_stats["volatility"]),
                var95=risk_report.get("value_at_risk", {}).get("historical_95", {}).get("var_pct", 0.0),
                max_drawdown_pct=risk_report.get("drawdown", {}).get("portfolio", {}).get("max_drawdown_pct", 0.0),
                sentiment_scores=self.sentiment_scores,
                final_weights=final_weights,
                risk_report=risk_report,
                baseline_sharpe=baseline.get("sharpe_ratio"),
                news_counts=self.news_counts,
            )
            candidates.append({
                "max_weight_cap": cap,
                "score": health["score"],
                "health_score": health,
                "opt_result": opt_result,
                "combined": combined,
                "final_weights": final_weights,
                "final_stats": final_stats,
                "risk_report": risk_report,
            })

        if not candidates:
            raise ValueError("No feasible adaptive optimization candidates")

        # Re-score with candidate stability now known.
        preliminary = [float(c["score"]) for c in candidates]
        for c in candidates:
            rr = c["risk_report"]
            fs = c["final_stats"]
            c["health_score"] = HealthScoreEngine.calculate(
                sharpe=fs["sharpe_ratio"],
                volatility=rr.get("volatility", {}).get("portfolio_annualized", fs["volatility"]),
                var95=rr.get("value_at_risk", {}).get("historical_95", {}).get("var_pct", 0.0),
                max_drawdown_pct=rr.get("drawdown", {}).get("portfolio", {}).get("max_drawdown_pct", 0.0),
                sentiment_scores=self.sentiment_scores,
                final_weights=c["final_weights"],
                risk_report=rr,
                baseline_sharpe=baseline.get("sharpe_ratio"),
                news_counts=self.news_counts,
                candidate_scores=preliminary,
            )
            c["score"] = c["health_score"]["score"]

        best = max(candidates, key=lambda c: (float(c["score"]), float(c["final_stats"]["sharpe_ratio"])))
        summary = [
            {
                "max_weight_cap": c["max_weight_cap"],
                "health_score": c["health_score"]["score"],
                "sharpe_ratio": round(float(c["final_stats"]["sharpe_ratio"]), 6),
                "volatility": round(float(c["final_stats"]["volatility"]), 6),
                "max_drawdown_pct": c["risk_report"].get("drawdown", {}).get("portfolio", {}).get("max_drawdown_pct", 0.0),
            }
            for c in candidates
        ]
        return {
            **best,
            "selected_cap": best["max_weight_cap"],
            "baseline": baseline,
            "candidates": summary,
        }
