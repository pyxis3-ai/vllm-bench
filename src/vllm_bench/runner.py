"""Async benchmark runner. Hits an OpenAI-compatible chat-completions endpoint."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass

import httpx

from .stats import RequestSample


@dataclass(slots=True)
class BenchConfig:
    base_url: str
    model: str
    prompt: str
    max_tokens: int
    concurrency: int
    requests: int
    api_key: str | None = None
    timeout_s: float = 120.0
    label: str | None = None

    @property
    def display_label(self) -> str:
        return self.label or f"{self.model}@{self.base_url}"


async def _one_request(client: httpx.AsyncClient, cfg: BenchConfig) -> RequestSample:
    url = cfg.base_url.rstrip("/") + "/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    if cfg.api_key:
        headers["Authorization"] = f"Bearer {cfg.api_key}"
    payload = {
        "model": cfg.model,
        "messages": [{"role": "user", "content": cfg.prompt}],
        "max_tokens": cfg.max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
    }

    t0 = time.perf_counter()
    ttft = 0.0
    output_tokens = 0
    input_tokens = 0

    try:
        async with client.stream("POST", url, headers=headers, json=payload, timeout=cfg.timeout_s) as r:
            if r.status_code >= 400:
                body = await r.aread()
                return RequestSample(
                    ttft_s=0.0, total_s=time.perf_counter() - t0,
                    input_tokens=0, output_tokens=0,
                    success=False, error=f"HTTP {r.status_code}: {body[:200].decode(errors='replace')}",
                )
            async for line in r.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if ttft == 0.0:
                    choices = chunk.get("choices") or []
                    if choices and (choices[0].get("delta") or {}).get("content"):
                        ttft = time.perf_counter() - t0
                if usage := chunk.get("usage"):
                    output_tokens = usage.get("completion_tokens") or output_tokens
                    input_tokens = usage.get("prompt_tokens") or input_tokens
                else:
                    choices = chunk.get("choices") or []
                    if choices and (choices[0].get("delta") or {}).get("content"):
                        output_tokens += 1
    except (httpx.HTTPError, asyncio.TimeoutError) as e:
        return RequestSample(
            ttft_s=0.0, total_s=time.perf_counter() - t0,
            input_tokens=0, output_tokens=0,
            success=False, error=str(e)[:200],
        )

    return RequestSample(
        ttft_s=ttft or (time.perf_counter() - t0),
        total_s=time.perf_counter() - t0,
        input_tokens=input_tokens,
        output_tokens=max(output_tokens, 1),
        success=True,
    )


async def run_bench(cfg: BenchConfig, on_sample=None) -> tuple[float, list[RequestSample]]:
    """Run cfg.requests requests with cfg.concurrency in flight at once. Returns (wall_seconds, samples)."""

    sem = asyncio.Semaphore(cfg.concurrency)
    samples: list[RequestSample] = []

    async with httpx.AsyncClient() as client:
        async def worker(i: int) -> None:
            async with sem:
                s = await _one_request(client, cfg)
                samples.append(s)
                if on_sample:
                    on_sample(i, s)

        t0 = time.perf_counter()
        await asyncio.gather(*(worker(i) for i in range(cfg.requests)))
        wall = time.perf_counter() - t0
    return wall, samples
