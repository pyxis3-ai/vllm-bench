# Contributing

Issues and PRs welcome. Quick orientation:

## Layout

- `src/vllm_bench/cli.py` — argument parsing, sub-commands (`run`, `compare`)
- `src/vllm_bench/runner.py` — async HTTP loop against the chat-completions endpoint
- `src/vllm_bench/stats.py` — per-request samples + percentile aggregation
- `src/vllm_bench/output.py` — table / json / csv / md emitters

Two runtime deps only (`httpx`, `rich`). Keep it that way unless you're adding a feature that genuinely needs more.

## Local development

```sh
git clone https://github.com/pyxis3-ai/vllm-bench
cd vllm-bench
uv sync                    # or: pip install -e .
python -m vllm_bench --help
```

## Testing against a real endpoint

Easiest: run a small model on `llama-server` (llama.cpp) or `vllm serve` locally, then point `vllm-bench` at it:

```sh
vllm-bench run \
  --base-url http://localhost:8000 \
  --model my-model \
  --concurrency 4 \
  --requests 20
```

## What we'd love help with

- More serving runtimes in the README compatibility list (test against your favourite, send a PR if `--format json` output round-trips)
- Sweep mode — vary concurrency, batch size, or input length across runs in one command
- Prefill-vs-decode separation when the runtime exposes it via response headers
- Result aggregation across multiple runs over time (CI-friendly trend tracking)

## Style

- Python 3.10+, type hints throughout, dataclasses for structured records
- `ruff format` for layout; no opinion on `ruff check` warnings unless they catch a real bug
- Keep CLI ergonomic — every flag should have a short and long form where it helps

## Commit messages

One line summary, present tense ("add", not "added"). Body if it's non-obvious.

## License

MIT. By contributing you agree your code is released under the same.
