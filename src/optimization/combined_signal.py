"""
combined_signal.py
------------------
Combines TWO signals into final portfolio recommendation:
  1. Quantitative signal — Sharpe ratio optimized weights (from portfolio.py)
  2. Sentiment signal    — FinBERT scores per ticker (from sentiment.py)

How combining works:
  final_weight = alpha * optimized_weight + (1 - alpha) * sentiment_weight
  where alpha controls how much you trust math vs news (default 0.6)

Sentiment → Weight conversion:
  Positive sentiment (+1.0) → overweight by up to 10%
  Negative sentiment (-1.0) → underweight by up to 10%
  Neutral (0.0)             → no adjustment

Usage:
    from src.optimization.combined_signal import CombinedSignal
    signal = CombinedSignal(optimized_result, sentiment_scores)
    final = signal.combine(alpha=0.6, max_weight=0.25)
    print(final)
"""

import numpy as np
from typing import Optional
from src.optimization.rebalancing import (
    classify_model_adjustment,
)

# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_ALPHA = 0.6         # 60% weight on quant, 40% on sentiment
MAX_SENTIMENT_SHIFT = 0.04  # v3: sentiment is a supporting signal, max ±4%
DEFAULT_MAX_WEIGHT = 0.25   # Target cap per ticker; caller should adapt for portfolios with <4 assets


# ── Helper Functions ──────────────────────────────────────────────────────────

def sentiment_to_weight_adjustment(sentiment_score: float,
                                    max_shift: float = MAX_SENTIMENT_SHIFT,
                                    confidence: float | None = None,
                                    relevance: float = 1.0) -> float:
    """
    Convert a FinBERT sentiment score to a weight adjustment.

    Score range: -1.0 to +1.0
    Output range: -max_shift to +max_shift

    Example:
        sentiment = +0.8 → adjustment = +0.08 (increase weight by 8%)
        sentiment = -0.5 → adjustment = -0.05 (decrease weight by 5%)
        sentiment =  0.0 → adjustment = 0.00 (no change)
    """
    # Confidence-aware damping: weak/neutral FinBERT signals should barely move weights.
    if confidence is None:
        confidence = 0.50 + 0.50 * min(abs(float(sentiment_score)) / 0.50, 1.0)
    confidence = max(0.0, min(1.0, float(confidence)))
    relevance = max(0.0, min(1.0, float(relevance)))
    return float(sentiment_score) * max_shift * confidence * relevance


def normalize_weights(weights: dict) -> dict:
    """
    Ensure weights sum to exactly 1.0 and all >= 0.
    Clips negative weights to 0 then renormalizes.
    """
    # Clip negatives
    clipped = {k: max(0.0, v) for k, v in weights.items()}

    total = sum(clipped.values())
    if total == 0:
        # Fallback: equal weight if everything is 0
        n = len(clipped)
        return {k: 1.0 / n for k in clipped}

    return {k: v / total for k, v in clipped.items()}


def _apply_max_weight(weights: dict, max_weight: float) -> dict:
    """
    Iteratively cap weights at max_weight and redistribute excess.

    The naive approach (cap then renormalize) fails because renormalizing
    pushes capped weights back above the limit. This waterfall approach
    repeatedly redistributes excess only to uncapped tickers.

    Args:
        weights: dict {ticker: weight}
        max_weight: hard cap per ticker (e.g. 0.25 for 25%)

    Returns:
        dict of capped + rebalanced weights summing to 1.0
    """
    weights = dict(weights)
    n = len(weights)

    for _ in range(n):  # max iterations = number of assets
        overage = {k: v - max_weight for k, v in weights.items() if v > max_weight}
        if not overage:
            break  # all weights within limit

        total_overage = sum(overage.values())
        # Lock capped tickers at max_weight
        for k in overage:
            weights[k] = max_weight

        uncapped = [k for k in weights if weights[k] < max_weight]
        if not uncapped:
            # Edge case: every ticker is capped — equalize
            weights = {k: 1.0 / n for k in weights}
            break

        # Distribute excess equally among uncapped tickers
        for k in uncapped:
            weights[k] += total_overage / len(uncapped)

    return normalize_weights(weights)


# ── Combined Signal Class ─────────────────────────────────────────────────────

class CombinedSignal:
    """
    Merges quantitative portfolio weights with sentiment signals.

    Args:
        optimized_result: Output dict from PortfolioOptimizer.optimize()
                          Must have keys: 'weights', 'tickers', 'sharpe_ratio', etc.

        sentiment_scores: Dict {ticker: sentiment_score}
                          Score range: -1.0 to +1.0 (from FinBERT)
                          Example: {"AAPL": 0.72, "MSFT": 0.55, "GOOGL": -0.15}
    """

    def __init__(self, optimized_result: dict, sentiment_scores: dict):
        self.optimized = optimized_result
        self.sentiment_scores = sentiment_scores
        self.tickers = optimized_result["tickers"]

        # Validate inputs
        missing = [t for t in self.tickers if t not in sentiment_scores]
        if missing:
            print(f"[CombinedSignal] WARNING: No sentiment for {missing}. Using 0.0 (neutral).")
            for t in missing:
                self.sentiment_scores[t] = 0.0

        print(f"[CombinedSignal] Initialized with {len(self.tickers)} assets.")

    def combine(self, alpha: float = DEFAULT_ALPHA,
                max_weight: Optional[float] = DEFAULT_MAX_WEIGHT) -> dict:
        """
        Combine optimized weights with sentiment-adjusted weights.

        Formula:
            sentiment_weight = optimized_weight + sentiment_adjustment
            final_weight = alpha * optimized_weight + (1 - alpha) * sentiment_weight
            (then normalize to sum = 1.0, optionally cap max weight)

        Args:
            alpha: float 0.0 to 1.0
                   - 1.0 = ignore sentiment, use pure Sharpe optimization
                   - 0.0 = ignore optimization, use pure sentiment signal
                   - 0.6 = 60% quant + 40% sentiment (recommended default)
            max_weight: hard cap per ticker (default 0.25 = 25%).
                        Set to None to disable capping (not recommended for
                        concentrated portfolios).

        Returns:
            dict with:
                - final_weights: {ticker: weight}
                - optimized_weights: original Sharpe weights
                - sentiment_adjusted_weights: weights after sentiment shift
                - sentiment_scores: input scores
                - alpha: blend ratio used
                - weight_changes: how much each weight changed from optimized
        """
        if not (0.0 <= alpha <= 1.0):
            raise ValueError(f"alpha must be between 0.0 and 1.0, got {alpha}")

        print(f"\n[CombinedSignal] Combining signals (alpha={alpha})...")
        print(f"  Alpha meaning: {alpha*100:.0f}% quant + {(1-alpha)*100:.0f}% sentiment")
        if max_weight is not None:
            print(f"  Max weight cap: {max_weight*100:.1f}% per ticker")

        optimized_weights = self.optimized["weights"]

        # Step 1: Compute sentiment-adjusted weights
        sentiment_adjusted = {}
        for ticker in self.tickers:
            opt_w = optimized_weights.get(ticker, 0.0)
            score = self.sentiment_scores.get(ticker, 0.0)
            adjustment = sentiment_to_weight_adjustment(score)
            sentiment_adjusted[ticker] = opt_w + adjustment

        # Normalize sentiment-adjusted weights (they may not sum to 1.0 after adjustments)
        sentiment_adjusted = normalize_weights(sentiment_adjusted)

        # Step 2: Blend optimized + sentiment-adjusted
        blended = {}
        for ticker in self.tickers:
            opt_w = optimized_weights.get(ticker, 0.0)
            sent_w = sentiment_adjusted.get(ticker, 0.0)
            blended[ticker] = alpha * opt_w + (1 - alpha) * sent_w

        # Step 3: Normalize final weights
        final_weights = normalize_weights(blended)

        # Step 4: Enforce max weight constraint (iterative waterfall)
        if max_weight is not None and max_weight > 0:
            final_weights = _apply_max_weight(final_weights, max_weight)

        # Step 5: Compute weight changes + exclusion reasons
        weight_changes = {}
        for ticker in self.tickers:
            original = optimized_weights.get(ticker, 0.0)
            final = final_weights.get(ticker, 0.0)
            change = final - original
            direction = "↑" if change > 0.005 else ("↓" if change < -0.005 else "→")

            # Build exclusion reason for zero-weight tickers
            reason = ""
            if final == 0.0:
                reasons = []
                if original == 0.0:
                    reasons.append("Zero in optimal portfolio")
                sent = self.sentiment_scores.get(ticker, 0.0)
                if sent < -0.1:
                    reasons.append(f"Negative sentiment ({sent:+.2f})")
                reason = "; ".join(reasons) if reasons else "Suboptimal risk/return"

            weight_changes[ticker] = {
                "from": round(original, 4),
                "to": round(final, 4),
                "change": round(change, 4),
                "direction": direction,
                "old_weight": round(original, 4),
                "new_weight": round(final, 4),
                "action": classify_model_adjustment(
                    original,
                    final,
                ),
                "exclusion_reason": reason
            }

        # Print summary
        print(f"\n  {'Ticker':<8} {'Sentiment':>10} {'Opt Weight':>12} {'Final Weight':>13} {'Change':>8}")
        print("  " + "─" * 55)
        for ticker in self.tickers:
            score = self.sentiment_scores[ticker]
            opt = optimized_weights[ticker]
            final = final_weights[ticker]
            chg = weight_changes[ticker]
            print(f"  {ticker:<8} {score:>+10.3f} {opt*100:>11.1f}% {final*100:>12.1f}% "
                  f"  {chg['direction']} {chg['change']*100:+.1f}%")

        total = sum(final_weights.values())
        print(f"\n  Final weights sum: {total:.6f} ({'✅' if abs(total - 1.0) < 1e-4 else '❌'})")

        return {
            "final_weights": {k: round(v, 6) for k, v in final_weights.items()},
            "optimized_weights": optimized_weights,
            "sentiment_adjusted_weights": {k: round(v, 6) for k, v in sentiment_adjusted.items()},
            "sentiment_scores": self.sentiment_scores,
            "alpha": alpha,
            "weight_changes": weight_changes,
            "tickers": self.tickers
        }

    def sensitivity_analysis(self, alphas: Optional[list] = None,
                             max_weight: Optional[float] = DEFAULT_MAX_WEIGHT) -> dict:
        """
        Run combine() at multiple alpha values to see sensitivity.
        Useful for understanding how much sentiment affects the final portfolio.

        Args:
            alphas: list of alpha values to test (default: [0.0, 0.25, 0.5, 0.75, 1.0])
            max_weight: optional hard cap per ticker

        Returns:
            dict {alpha: final_weights}
        """
        if alphas is None:
            alphas = [0.0, 0.25, 0.5, 0.75, 1.0]

        print(f"\n[CombinedSignal] Sensitivity analysis across alphas: {alphas}")
        results = {}
        for a in alphas:
            r = self.combine(alpha=a, max_weight=max_weight)
            results[a] = r["final_weights"]

        # Print comparison table
        print(f"\n  {'Ticker':<8}", end="")
        for a in alphas:
            print(f"  α={a:.2f}", end="")
        print()
        print("  " + "─" * (8 + len(alphas) * 10))
        for ticker in self.tickers:
            print(f"  {ticker:<8}", end="")
            for a in alphas:
                w = results[a].get(ticker, 0)
                print(f"  {w*100:5.1f}%", end="")
            print()

        return results


# ── Quick Test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("COMBINED SIGNAL TEST")
    print("=" * 60)

    # Simulated output from PortfolioOptimizer.optimize()
    mock_optimized = {
        "tickers": ["AAPL", "MSFT", "GOOGL", "AMZN"],
        "weights": {
            "AAPL": 0.35,
            "MSFT": 0.30,
            "GOOGL": 0.20,
            "AMZN": 0.15
        },
        "sharpe_ratio": 1.42,
        "expected_return": 0.18,
        "volatility": 0.22
    }

    # Simulated FinBERT sentiment scores
    mock_sentiment = {
        "AAPL": 0.72,    # Strong positive → should increase weight
        "MSFT": 0.55,    # Positive → slight increase
        "GOOGL": -0.40,  # Negative → should decrease weight
        "AMZN": 0.30     # Mildly positive → slight increase
    }

    signal = CombinedSignal(mock_optimized, mock_sentiment)

    print("\n--- Default blend (alpha=0.6, max_weight=0.25) ---")
    result = signal.combine(alpha=0.6, max_weight=0.25)

    print("\n--- Pure quant (alpha=1.0, max_weight=0.25) ---")
    signal.combine(alpha=1.0, max_weight=0.25)

    print("\n--- Pure sentiment (alpha=0.0, max_weight=0.25) ---")
    signal.combine(alpha=0.0, max_weight=0.25)

    print("\n--- Sensitivity Analysis ---")
    signal.sensitivity_analysis(max_weight=0.25)

    print("\n✅ Combined signal working.")
