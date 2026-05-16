"""Result formatters: table, json, csv, markdown."""

from __future__ import annotations

import csv
import json
import sys
from dataclasses import asdict

from rich.console import Console
from rich.table import Table

from .stats import Summary


def _row(s: Summary) -> list[str]:
    return [
        s.label,
        f"{s.n_ok}/{s.n_ok + s.n_err}",
        f"{s.wall_s:.2f}",
        f"{s.ttft_p50_ms:.0f}",
        f"{s.ttft_p95_ms:.0f}",
        f"{s.ttft_p99_ms:.0f}",
        f"{s.tpot_p50_ms:.1f}",
        f"{s.tpot_p95_ms:.1f}",
        f"{s.throughput_req_per_s:.2f}",
        f"{s.throughput_output_tok_per_s:.1f}",
        f"{s.output_tokens_total}",
    ]


_HEADERS = [
    "endpoint", "ok/total", "wall_s",
    "ttft_p50_ms", "ttft_p95_ms", "ttft_p99_ms",
    "tpot_p50_ms", "tpot_p95_ms",
    "req/s", "out_tok/s", "out_tok",
]


def emit(summaries: list[Summary], fmt: str) -> None:
    if fmt == "table":
        c = Console()
        t = Table(title="vllm-bench")
        for h in _HEADERS:
            t.add_column(h, no_wrap=True)
        for s in summaries:
            t.add_row(*_row(s))
        c.print(t)
    elif fmt == "json":
        json.dump([asdict(s) for s in summaries], sys.stdout, indent=2)
        sys.stdout.write("\n")
    elif fmt == "csv":
        w = csv.writer(sys.stdout)
        w.writerow(_HEADERS)
        for s in summaries:
            w.writerow(_row(s))
    elif fmt == "md":
        print("| " + " | ".join(_HEADERS) + " |")
        print("|" + "|".join(["---"] * len(_HEADERS)) + "|")
        for s in summaries:
            print("| " + " | ".join(_row(s)) + " |")
    else:
        raise ValueError(f"unknown format: {fmt}")
