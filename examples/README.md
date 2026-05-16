# Examples

## `compare.json`

Drop-in config for `vllm-bench compare --config compare.json`. Three endpoints, same model, varying hardware + runtime.

```sh
vllm-bench compare --config compare.json --format md
```

## `qwen-7b-comparison.json`

Sample output from a 3-endpoint run, captured as `vllm-bench compare ... --format json`. Useful as test fixture and as a reference for what the JSON schema looks like for downstream tooling.

A2-A100 vs H100 vs TGI-A100 on Qwen 2.5 7B, 200 requests at concurrency 8 each. Showcase numbers:

| Endpoint | TTFT p50 (ms) | TPOT p50 (ms) | Throughput (out tok/s) |
|---|---|---|---|
| vllm-A100 | 412 | 14.2 | 1,284 |
| vllm-H100 | 187 | 6.4 | 2,881 |
| tgi-A100 | 487 | 16.9 | 1,066 |

The H100 numbers are roughly what you'd expect from the memory-bandwidth ratio (3.35 TB/s vs 2.04 TB/s for SXM A100s). The vLLM-vs-TGI gap on A100 is mostly continuous batching efficiency at concurrency 8 — gap narrows at lower concurrency.
