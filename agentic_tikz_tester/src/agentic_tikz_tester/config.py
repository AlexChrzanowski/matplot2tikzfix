from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Config:
    n: int = 10
    out: str = "runs/output"
    model: str = "claude-3-5-haiku-20241022"
    threshold_rms: float = 8.0
    threshold_ssim: float = 0.985
    timeout: int = 30
    keep_passing: bool = False
    transpiler: str = "makintikz"
    seed: int | None = None
    provider: str = "anthropic"
    no_llm: bool = False
    failures_dir: str = "failures"
