from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Config:
    n: int = 10
    out: str = "runs/output"
    model: str = "claude-haiku-4-5-20251001"
    # Flag thresholds: annotate results as "flagged" for human inspection.
    # These do NOT gate artifact saving — all completed tests are always saved.
    # Set to None to disable a threshold entirely.
    flag_rms: float | None = 20.0       # raw RMS on trimmed images
    flag_ssim: float | None = 0.85      # SSIM on trimmed images
    flag_edge_ssim: float | None = 0.50 # edge-structure SSIM (most informative)
    timeout: int = 30
    transpiler: str = "makintikz"
    seed: int | None = None
    provider: str = "anthropic"
    no_llm: bool = False
    failures_dir: str = "failures"
