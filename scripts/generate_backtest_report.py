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
    rows = [
        ("CAGR", "Not measured*", pct(q["cagr"]), pct(e["cagr"]), pct(b["cagr"])),
        ("Annualized volatility", "Not measured*", pct(q["annualized_volatility"]), pct(e["annualized_volatility"]), pct(b["annualized_volatility"])),
        ("Sharpe ratio", "Not measured*", num(q["sharpe_ratio"]), num(e["sharpe_ratio"]), num(b["sharpe_ratio"])),
        ("Sortino ratio", "Not measured*", num(q["sortino_ratio"]), num(e["sortino_ratio"]), num(b["sortino_ratio"])),
        ("Maximum drawdown", "Not measured*", pct(q["maximum_drawdown"]), pct(e["maximum_drawdown"]), pct(b["maximum_drawdown"])),
        ("Annual turnover", "Not measured*", pct(q["annual_turnover"]), pct(e["annual_turnover"]), "N/A"),
        ("Transaction-cost drag", "Not measured*", pct(q["transaction_cost_drag"]), pct(e["transaction_cost_drag"]), "0.00%"),
    ]
    lines = [
        "# AXIOM Backtest Summary",
        "",
        f"Evaluation window: `{data['data']['first_date']}` to `{data['data']['last_date']}`  ",
        f"Assets: `{', '.join(data['config']['tickers'])}`  ",
        f"Benchmark: `{data['config']['benchmark']}`",
        "",
        "| Metric | AXIOM combined | Quantitative only | Equal weight | Benchmark |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    lines.extend([
        "",
        "*AXIOM combined is not measured because the repository does not yet contain a point-in-time historical news/sentiment dataset. Current news must not be used to simulate past decisions.*",
        "",
        "> Historical performance does not guarantee future results. This report is for research and educational use only.",
    ])
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(target.resolve())


if __name__ == "__main__":
    main()
