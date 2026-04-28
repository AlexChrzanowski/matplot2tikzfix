"""
report.py — save artifacts and write metadata.json for every test result.

Iteration 2 behavior:
  - save_test_result(): called for every COMPLETE test; writes metadata.json
    directly into the test_dir (artifacts are already there from the pipeline).
  - save_error_report(): called for pipeline errors (SCRIPT_ERROR, TRANSPILE_ERROR,
    LATEX_ERROR, RENDER_ERROR, GENERATION_ERROR); copies available artifacts to
    failures/failure_XXXX/ and writes metadata.json + report.md there.
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
    "composite.png",
]


def save_test_result(
    result: TestResult,
    test_dir: Path,
    config_meta: dict,
    prompt: str = "",
) -> None:
    """
    Write metadata.json for a completed (COMPLETE status) test.

    Artifacts are already in test_dir from the pipeline — this just adds
    the metadata alongside them.
    """
    metadata = _build_metadata(result, config_meta, prompt=prompt)
    (test_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def save_error_report(
    result: TestResult,
    test_dir: Path,
    failures_dir: Path,
    failure_index: int,
    config_meta: dict,
    prompt: str = "",
) -> Path:
    """
    Copy available artifacts into failures/failure_XXXX/ and write
    metadata.json + report.md there.

    Returns the path to the created failure directory.
    """
    failure_id = f"failure_{failure_index:04d}"
    dest = failures_dir / failure_id
    dest.mkdir(parents=True, exist_ok=True)

    for name in _ARTIFACT_NAMES:
        src = test_dir / name
        if src.exists():
            shutil.copy2(src, dest / name)

    metadata = _build_metadata(result, config_meta, failure_id=failure_id, prompt=prompt)
    (dest / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (dest / "report.md").write_text(
        _build_report_md(result, failure_id, metadata),
        encoding="utf-8",
    )
    return dest


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_metadata(
    result: TestResult,
    config_meta: dict,
    failure_id: str = "",
    prompt: str = "",
) -> dict:
    return {
        "test_id": result.test_id,
        "failure_id": failure_id or None,
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
        "edge_ssim": result.edge_ssim,
        "max_diff": result.max_diff,
        "size_mismatch": result.size_mismatch,
        "flagged": result.flagged,
        "flag_rms": config_meta.get("flag_rms"),
        "flag_ssim": config_meta.get("flag_ssim"),
        "flag_edge_ssim": config_meta.get("flag_edge_ssim"),
        "exception_type": result.exception_type,
        "traceback": result.traceback,
        "features_claimed_by_agent": result.features,
    }


def _build_report_md(result: TestResult, failure_id: str, meta: dict) -> str:
    rms_str = f"{result.rms:.4f}" if result.rms is not None else "N/A"
    ssim_str = f"{result.ssim:.6f}" if result.ssim is not None else "N/A"
    edge_ssim_str = f"{result.edge_ssim:.6f}" if result.edge_ssim is not None else "N/A"

    script_code = ""
    if result.script_path and result.script_path.exists():
        try:
            script_code = result.script_path.read_text(encoding="utf-8")
        except OSError:
            script_code = "(could not read script)"

    error_section = ""
    if result.traceback:
        error_section = f"\n## Error Log\n\n```\n{result.traceback}\n```\n"

    return f"""\
# Error Report: {failure_id}

## Summary

| Field | Value |
|-------|-------|
| Status | `{result.status.value}` |
| RMS (trimmed) | {rms_str} |
| SSIM (trimmed) | {ssim_str} |
| Edge-SSIM | {edge_ssim_str} |
| Test ID | `{result.test_id}` |
| Timestamp | {meta.get("timestamp", "")} |
| Model | {meta.get("model", "")} |
| Seed | {meta.get("seed", "N/A")} |
| Transpiler | {meta.get("transpiler", "")} |
| Features | {", ".join(result.features) if result.features else "N/A"} |

## Reproduction

```bash
cd {failure_id}
python plot_script.py
# Then compile wrapper.tex with pdflatex and inspect reference.png vs tikz_rendered.png
```

## Generated Script

```python
{script_code}
```
{error_section}
## Artifacts

- `reference.png` — Matplotlib reference render
- `tikz_rendered.png` — TikZ/PGFPlots render
- `composite.png` — Side-by-side: reference | rendered | diff
- `diff.png` — Amplified pixel difference (×4)
- `figure.tikz` — Generated TikZ/PGFPlots code
- `wrapper.tex` — Standalone LaTeX wrapper
- `latex.log` — pdflatex output log
- `metadata.json` — Full machine-readable metadata
"""
