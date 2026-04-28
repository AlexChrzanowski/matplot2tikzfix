"""
report.py — save artifacts and write metadata.json + report.md for failures.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .runner import TestResult, TestStatus


_ARTIFACT_NAMES = [
    "plot_script.py",
    "figure.tikz",
    "wrapper.tex",
    "latex.log",
    "reference.png",
    "tikz_rendered.png",
    "diff.png",
]


def save_report(
    result: TestResult,
    test_dir: Path,
    failures_dir: Path,
    failure_index: int,
    config_meta: dict,
    prompt: str = "",
) -> Path:
    """
    Copy all artifacts into failures/failure_XXXX/ and write metadata.json
    and report.md.

    Returns the path to the failure directory.
    """
    failure_id = f"failure_{failure_index:04d}"
    dest = failures_dir / failure_id
    dest.mkdir(parents=True, exist_ok=True)

    # Copy available artifacts
    for name in _ARTIFACT_NAMES:
        src = test_dir / name
        if src.exists():
            shutil.copy2(src, dest / name)

    # Write metadata.json
    metadata = {
        "test_id": result.test_id,
        "failure_id": failure_id,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "status": result.status.value,
        "model": config_meta.get("model", ""),
        "provider": config_meta.get("provider", ""),
        "transpiler": config_meta.get("transpiler", ""),
        "seed": config_meta.get("seed"),
        "prompt": prompt,
        "script_path": str(result.script_path) if result.script_path else "",
        "rms": result.rms,
        "ssim": result.ssim,
        "max_diff": result.max_diff,
        "size_mismatch": result.size_mismatch,
        "threshold_rms": config_meta.get("threshold_rms"),
        "threshold_ssim": config_meta.get("threshold_ssim"),
        "exception_type": result.exception_type,
        "traceback": result.traceback,
        "features_claimed_by_agent": result.features,
    }
    (dest / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Write report.md
    (dest / "report.md").write_text(
        _build_report_md(result, failure_id, metadata),
        encoding="utf-8",
    )

    return dest


def save_passing_report(result: TestResult, test_dir: Path, config_meta: dict) -> None:
    """Write metadata.json for a passing test (no artifact copy, stays in test_dir)."""
    metadata = {
        "test_id": result.test_id,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "status": result.status.value,
        "model": config_meta.get("model", ""),
        "transpiler": config_meta.get("transpiler", ""),
        "rms": result.rms,
        "ssim": result.ssim,
        "threshold_rms": config_meta.get("threshold_rms"),
        "threshold_ssim": config_meta.get("threshold_ssim"),
        "features_claimed_by_agent": result.features,
    }
    (test_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Markdown report builder
# ---------------------------------------------------------------------------

def _build_report_md(result: TestResult, failure_id: str, meta: dict) -> str:
    rms_str = f"{result.rms:.4f}" if result.rms is not None else "N/A"
    ssim_str = f"{result.ssim:.6f}" if result.ssim is not None else "N/A"

    script_code = ""
    if result.script_path and result.script_path.exists():
        try:
            script_code = result.script_path.read_text(encoding="utf-8")
        except OSError:
            script_code = "(could not read script)"

    error_section = ""
    if result.traceback:
        error_section = f"""
## Error Log

```
{result.traceback}
```
"""

    repro_cmd = (
        f"cd {failure_id}\n"
        "python plot_script.py\n"
        "# Then compile wrapper.tex with pdflatex and compare reference.png vs tikz_rendered.png"
    )

    artifacts = "\n".join(
        f"- `{name}`" for name in _ARTIFACT_NAMES
        if (Path(".") / name).name in _ARTIFACT_NAMES
    )

    return f"""\
# Failure {failure_id}

## Summary

| Field | Value |
|-------|-------|
| Status | `{result.status.value}` |
| RMS | {rms_str} |
| SSIM | {ssim_str} |
| Test ID | `{result.test_id}` |
| Timestamp | {meta.get("timestamp", "")} |
| Model | {meta.get("model", "")} |
| Seed | {meta.get("seed", "N/A")} |
| Transpiler | {meta.get("transpiler", "")} |
| Features | {", ".join(result.features) if result.features else "N/A"} |

## Reproduction

```bash
{repro_cmd}
```

## Generated Matplotlib Script

```python
{script_code}
```
{error_section}
## Artifacts

- `reference.png` — Matplotlib reference render
- `tikz_rendered.png` — TikZ/PGFPlots render
- `diff.png` — Amplified pixel difference (×4)
- `figure.tikz` — Generated TikZ/PGFPlots code
- `wrapper.tex` — Standalone LaTeX wrapper
- `latex.log` — pdflatex output log
- `metadata.json` — Full machine-readable metadata
"""
