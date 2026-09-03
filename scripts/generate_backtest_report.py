"""Generate a Markdown result table from results/backtest_results.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/backtest_results.json")
    parser.add_argument("--output", default="results/backtest_summary.md")
    return parser.parse_args()


def pct(value: Any) -> str:
    return f"{float(value) * 100:.2f}%"


def num(value: Any) -> str:
    return f"{float(value):.3f}"


def main() -> None:
    args = parse_args()
    source = Path(args.input)
    data = json.loads(source.read_text(encoding="utf-8"))
    strategies = data["strategies"]
    q = strategies["quantitative_only"]
    e = strategies["equal_weight"]
    b = strategies["benchmark"]
    qn, qg, qi = q["net"], q["gross"], q["implementation"]
    en, eg, ei = e["net"], e["gross"], e["implementation"]
    rows = [
        ("Net CAGR", "Not measured*", pct(qn["cagr"]), pct(en["cagr"]), pct(b["cagr"])),
        (
            "Gross CAGR",
            "Not measured*",
            pct(qg["cagr"]),
            pct(eg["cagr"]),
            pct(b["cagr"]),
        ),
        (
            "Net annualized volatility",
            "Not measured*",
            pct(qn["annualized_volatility"]),
            pct(en["annualized_volatility"]),
            pct(b["annualized_volatility"]),
        ),
        (
            "Net Sharpe ratio",
            "Not measured*",
            num(qn["sharpe_ratio"]),
            num(en["sharpe_ratio"]),
            num(b["sharpe_ratio"]),
        ),
        (
            "Net Sortino ratio",
            "Not measured*",
            num(qn["sortino_ratio"]),
            num(en["sortino_ratio"]),
            num(b["sortino_ratio"]),
        ),
        (
            "Net maximum drawdown",
            "Not measured*",
            pct(qn["maximum_drawdown"]),
            pct(en["maximum_drawdown"]),
            pct(b["maximum_drawdown"]),
        ),
        (
            "Annual one-way turnover",
            "Not measured*",
            pct(qi["annual_turnover"]),
            pct(ei["annual_turnover"]),
            "N/A",
        ),
        (
            "CAGR cost drag",
            "Not measured*",
            pct(qi["cagr_cost_drag"]),
            pct(ei["cagr_cost_drag"]),
            "0.00%",
        ),
        (
            "Transaction costs / initial capital",
            "Not measured*",
            pct(qi["transaction_cost_pct_initial"]),
            pct(ei["transaction_cost_pct_initial"]),
            "0.00%",
        ),
    ]
    lines = [
        "# AXIOM Backtest Summary",
        "",
        f"Evaluation window: `{data['data']['first_date']}` to `{data['data']['last_date']}`  ",
        f"Assets: `{', '.join(data['config']['tickers'])}`  ",
        f"Benchmark: `{data['config']['benchmark']}`",
        f"Transaction-cost rate: `{data['config']['transaction_cost'] * 10_000:.1f} bps per traded notional`",
        "Initial portfolio establishment: `excluded from turnover and transaction costs`",
        "",
        "| Metric | AXIOM combined | Quantitative only | Equal weight | Benchmark |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    lines.extend(
        [
            "",
            "## Turnover and cost methodology",
            "",
            "One-way turnover is "
            "`0.5 * sum(abs(target weight - drifted pre-trade weight))`. "
            "Transaction costs apply to complete bought-and-sold notional, "
            "`sum(abs(target weight - drifted pre-trade weight))`. "
            "Net performance is the primary result; gross performance is shown "
            "for cost comparison.",
            "",
            "*AXIOM combined is not measured because the repository does not yet contain a point-in-time historical news/sentiment dataset. Current news must not be used to simulate past decisions.*",
            "",
            "> Historical performance does not guarantee future results. This report is for research and educational use only.",
        ]
    )
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(target.resolve())


if __name__ == "__main__":
    main()
