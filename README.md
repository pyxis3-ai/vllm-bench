# vllm-bench

Throughput and latency benchmark for OpenAI-compatible LLM inference endpoints — **vLLM**, **TGI**, **llama.cpp server**, **Ollama**, anything that speaks `/v1/chat/completions`.

Streams `stream: true` responses, measures **TTFT** (time-to-first-token) and **TPOT** (time-per-output-token) per request, and reports per-endpoint percentiles plus aggregate throughput. Single binary's worth of dependencies (`httpx`, `rich`).

Built for **Pyxis** — comparing model-serving runtimes across heterogeneous GPU fleets.

## Install

```sh
pip install vllm-bench
# or:
uv tool install vllm-bench
```

## Benchmark one endpoint

```sh
vllm-bench run \
  --base-url http://localhost:8000 \
  --model Qwen/Qwen2.5-7B-Instruct \
  --concurrency 8 \
  --requests 200
```

Output:

```
                                              vllm-bench
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┓
┃ endpoint                              ┃ ok/total ┃ wall_s ┃ ttft_p50_ms┃ ttft_p95_ms┃ ttft_p99_ms┃ tpot_p50_ms┃ tpot_p95_ms┃ req/s ┃ out_tok/s┃ out_tok ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━┩
│ Qwen2.5-7B@http://localhost:8000      │  200/200 │  18.42 │         412│         683│         784│        14.2│        23.7│ 10.86 │   1284.3 │  23652  │
└───────────────────────────────────────┴──────────┴────────┴────────────┴────────────┴────────────┴────────────┴────────────┴───────┴──────────┴─────────┘
```

## Compare multiple endpoints

`compare.json`:

```json
[
  {
    "label": "vllm-A100",
    "base_url": "http://gpu-a100:8000",
    "model": "Qwen/Qwen2.5-7B-Instruct"
  },
  {
    "label": "vllm-H100",
    "base_url": "http://gpu-h100:8000",
    "model": "Qwen/Qwen2.5-7B-Instruct"
  },
  {
    "label": "tgi-A100",
    "base_url": "http://tgi-a100:8080",
    "model": "Qwen/Qwen2.5-7B-Instruct"
  }
]
```

Run:

```sh
vllm-bench compare --config compare.json --concurrency 16 --requests 500 --format md
```

## Output formats

`--format table` (default · rich terminal table) · `--format json` · `--format csv` · `--format md`

Pipe `json` into your existing dashboards; commit `md` to repos as benchmark records over time.

## Metrics

- **TTFT** — time from request send to **first** streamed token. The latency a user feels.
- **TPOT** — time per output token *after* the first. Cleanly separates queue/prefill latency (TTFT) from steady-state decode speed.
- **req/s** — completed requests divided by wall time. Counts only successful requests.
- **out_tok/s** — aggregate decode throughput across all concurrent requests.

p50, p95, p99 reported for TTFT; p50, p95 for TPOT (p99 is noisy at low n).

## Why TTFT + TPOT separately

When tuning a serving runtime, the two move independently. Prefill (TTFT) is dominated by attention-matrix construction and queueing; decode (TPOT) is dominated by GPU memory bandwidth and batch shape. Looking only at end-to-end latency hides which side of the pipeline is the bottleneck. Practitioners running vLLM, SGLang, TGI, or TensorRT-LLM compare these two axes per model + per GPU class — `vllm-bench` reports both per-request.

## Streaming + token accounting

The benchmark uses `stream: true` because that's the only way to measure TTFT honestly on these endpoints. Token counts come from the server-emitted `usage` block when available (most modern runtimes set `stream_options.include_usage`); the runner falls back to counting non-empty `choices[0].delta.content` chunks if usage isn't returned.

## License

MIT.

## Maintenance

This repository is maintained with small, reviewable updates. Supporting documentation lives in `docs/`, example inputs live in `examples/`, and lightweight validation notes live in `tests/smoke/`.
