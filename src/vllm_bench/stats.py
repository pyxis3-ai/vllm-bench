"""Latency and throughput statistics."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


@dataclass(slots=True)
class RequestSample:
    """One completed request."""

    ttft_s: float
    """Time to first token (seconds)."""
    total_s: float
    """Wall time from request start to completion."""
    input_tokens: int
    output_tokens: int
    success: bool
    error: str | None = None

    @property
    def tpot_s(self) -> float:
        """Time per output token after the first."""
        if self.output_tokens <= 1 or self.total_s <= self.ttft_s:
            return 0.0
        return (self.total_s - self.ttft_s) / (self.output_tokens - 1)


@dataclass(slots=True)
class Summary:
    label: str
    n_ok: int
    n_err: int
    wall_s: float

    ttft_p50_ms: float
    ttft_p95_ms: float
    ttft_p99_ms: float
    ttft_mean_ms: float

    tpot_p50_ms: float
    tpot_p95_ms: float
    tpot_p99_ms: float
    tpot_mean_ms: float

    throughput_req_per_s: float
    throughput_output_tok_per_s: float
    input_tokens_total: int
    output_tokens_total: int


def _pct(xs: list[float], p: float) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    k = max(0, min(len(s) - 1, round((p / 100) * (len(s) - 1))))
    return s[k]


def summarise(label: str, wall_s: float, samples: list[RequestSample]) -> Summary:
    ok = [s for s in samples if s.success]
    err = [s for s in samples if not s.success]
    ttfts = [s.ttft_s * 1000 for s in ok]
    tpots = [s.tpot_s * 1000 for s in ok if s.tpot_s > 0]
    out_tokens = sum(s.output_tokens for s in ok)
    in_tokens = sum(s.input_tokens for s in ok)
    return Summary(
        label=label,
        n_ok=len(ok),
        n_err=len(err),
        wall_s=wall_s,
        ttft_p50_ms=_pct(ttfts, 50),
        ttft_p95_ms=_pct(ttfts, 95),
        ttft_p99_ms=_pct(ttfts, 99),
        ttft_mean_ms=mean(ttfts) if ttfts else 0.0,
        tpot_p50_ms=_pct(tpots, 50),
        tpot_p95_ms=_pct(tpots, 95),
        tpot_p99_ms=_pct(tpots, 99),
        tpot_mean_ms=mean(tpots) if tpots else 0.0,
        throughput_req_per_s=len(ok) / wall_s if wall_s > 0 else 0.0,
        throughput_output_tok_per_s=out_tokens / wall_s if wall_s > 0 else 0.0,
        input_tokens_total=in_tokens,
        output_tokens_total=out_tokens,
    )
