"""CLI entry-point. `vllm-bench run` and `vllm-bench compare`."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from .runner import BenchConfig, run_bench
from .stats import summarise


DEFAULT_PROMPT = "Explain quicksort to a senior engineer in five sentences."


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--prompt", default=DEFAULT_PROMPT, help="prompt text (or @filepath to load from file)")
    p.add_argument("--max-tokens", type=int, default=256)
    p.add_argument("--concurrency", "-c", type=int, default=4)
    p.add_argument("--requests", "-n", type=int, default=20)
    p.add_argument("--format", choices=["table", "json", "csv", "md"], default="table")


def _resolve_prompt(s: str) -> str:
    if s.startswith("@"):
        return Path(s[1:]).read_text()
    return s


def _run(args: argparse.Namespace) -> int:
    cfg = BenchConfig(
        base_url=args.base_url,
        model=args.model,
        prompt=_resolve_prompt(args.prompt),
        max_tokens=args.max_tokens,
        concurrency=args.concurrency,
        requests=args.requests,
        api_key=args.api_key or os.environ.get("OPENAI_API_KEY"),
        label=args.label,
    )
    return _execute([cfg], args.format)


def _compare(args: argparse.Namespace) -> int:
    raw = json.loads(Path(args.config).read_text())
    if not isinstance(raw, list):
        raise SystemExit("compare config must be a JSON list of endpoint objects")
    cfgs = [
        BenchConfig(
            base_url=e["base_url"],
            model=e["model"],
            prompt=_resolve_prompt(e.get("prompt", args.prompt)),
            max_tokens=e.get("max_tokens", args.max_tokens),
            concurrency=e.get("concurrency", args.concurrency),
            requests=e.get("requests", args.requests),
            api_key=e.get("api_key") or os.environ.get("OPENAI_API_KEY"),
            label=e.get("label"),
        )
        for e in raw
    ]
    return _execute(cfgs, args.format)


def _execute(cfgs: list[BenchConfig], fmt: str) -> int:
    console = Console(stderr=True)
    summaries = []
    for cfg in cfgs:
        with Progress(
            SpinnerColumn(), TextColumn("[bold]{task.description}"),
            BarColumn(), TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(), console=console, transient=True,
        ) as prog:
            task = prog.add_task(f"{cfg.display_label}  c={cfg.concurrency}  n={cfg.requests}", total=cfg.requests)
            def step(_i, _s):
                prog.advance(task)
            wall, samples = asyncio.run(run_bench(cfg, on_sample=step))
        summaries.append(summarise(cfg.display_label, wall, samples))
        ok = sum(1 for s in samples if s.success)
        if ok < len(samples):
            console.print(f"[yellow]{cfg.display_label}: {len(samples) - ok} request(s) failed[/yellow]", highlight=False)

    from .output import emit
    emit(summaries, fmt)
    return 0 if all(s.n_err == 0 for s in summaries) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="vllm-bench",
        description="Benchmark OpenAI-compatible LLM endpoints (vLLM, TGI, llama.cpp, Ollama).",
    )
    parser.add_argument("--api-key", help="API key (or set OPENAI_API_KEY)")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Benchmark one endpoint")
    p_run.add_argument("--base-url", required=True, help="e.g. http://localhost:8000")
    p_run.add_argument("--model", required=True)
    p_run.add_argument("--label", default=None)
    _add_common(p_run)
    p_run.set_defaults(func=_run)

    p_cmp = sub.add_parser("compare", help="Benchmark multiple endpoints from a JSON config")
    p_cmp.add_argument("--config", required=True, help="path to JSON config (list of endpoint objects)")
    _add_common(p_cmp)
    p_cmp.set_defaults(func=_compare)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
