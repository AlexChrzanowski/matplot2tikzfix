"""
runner.py — orchestrates the full pipeline for a single test case.

Pipeline stages:
  1. Save generated script to plot_script.py
  2. Execute script as subprocess → reference.png
  3. Transpile → figure.tikz
  4. Create wrapper.tex
  5. Compile wrapper.tex → wrapper.pdf
  6. Rasterize wrapper.pdf → tikz_rendered.png
  7. Compare reference.png vs tikz_rendered.png
"""
from __future__ import annotations

import subprocess
import sys
import traceback
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .config import Config
from .example_suite import GeneratedScript
from .image_compare import CompareResult, compare_images
from .latex_renderer import compile_latex, create_wrapper_tex, pdf_to_png
from .transpiler import transpile


class TestStatus(str, Enum):
    PASS = "pass"
    VISUAL_MISMATCH = "visual_mismatch"
    GENERATION_ERROR = "generation_error"
    SCRIPT_ERROR = "script_error"
    TRANSPILE_ERROR = "transpile_error"
    LATEX_ERROR = "latex_error"
    RENDER_ERROR = "render_error"


@dataclass
class TestResult:
    test_id: str
    status: TestStatus
    rms: float | None = None
    ssim: float | None = None
    max_diff: float | None = None
    size_mismatch: bool = False
    features: list[str] = field(default_factory=list)
    exception_type: str = ""
    traceback: str = ""
    test_dir: Path | None = None
    script_path: Path | None = None
    tikz_path: Path | None = None
    wrapper_path: Path | None = None
    ref_png: Path | None = None
    rendered_png: Path | None = None
    diff_png: Path | None = None
    latex_log: Path | None = None


def run_test(
    test_id: str,
    test_dir: Path,
    script: GeneratedScript,
    config: Config,
) -> TestResult:
    """
    Run one complete pipeline stage for a single generated script.

    Returns a TestResult regardless of which stage failed.
    """
    result = TestResult(test_id=test_id, status=TestStatus.GENERATION_ERROR)
    result.features = script.features
    test_dir.mkdir(parents=True, exist_ok=True)

    # --- Stage 1: Save the script ------------------------------------------
    script_path = test_dir / "plot_script.py"
    script_path.write_text(script.code, encoding="utf-8")
    result.script_path = script_path
    result.test_dir = test_dir

    # --- Stage 2: Execute the script (reference.png) -----------------------
    ref_png = test_dir / "reference.png"
    result.ref_png = ref_png

    ok, tb = _run_script(script_path, test_dir, config.timeout)
    if not ok:
        result.status = TestStatus.SCRIPT_ERROR
        result.exception_type = "ScriptError"
        result.traceback = tb
        return result

    if not ref_png.exists():
        result.status = TestStatus.SCRIPT_ERROR
        result.exception_type = "MissingReferencePNG"
        result.traceback = "Script ran but reference.png was not created."
        return result

    # --- Stage 3: Transpile → figure.tikz ----------------------------------
    tikz_path = test_dir / "figure.tikz"
    result.tikz_path = tikz_path

    ok, error = transpile(
        script_path=script_path,
        output_path=tikz_path,
        transpiler_name=config.transpiler,
        timeout=config.timeout,
        cwd=test_dir,
    )
    if not ok:
        result.status = TestStatus.TRANSPILE_ERROR
        result.exception_type = "TranspileError"
        result.traceback = error
        return result

    if not tikz_path.exists():
        result.status = TestStatus.TRANSPILE_ERROR
        result.exception_type = "MissingTikzFile"
        result.traceback = "Transpiler exited 0 but figure.tikz was not created."
        return result

    # --- Stage 4: Create wrapper.tex ----------------------------------------
    wrapper_path = create_wrapper_tex(test_dir, tikz_filename="figure.tikz")
    result.wrapper_path = wrapper_path
    result.latex_log = test_dir / "latex.log"

    # --- Stage 5: Compile LaTeX → PDF ---------------------------------------
    pdf_path = test_dir / "wrapper.pdf"

    ok, log = compile_latex(
        work_dir=test_dir,
        tex_file=wrapper_path,
        timeout=config.timeout,
    )
    if not ok:
        result.status = TestStatus.LATEX_ERROR
        result.exception_type = "LaTeXError"
        result.traceback = log
        return result

    if not pdf_path.exists():
        result.status = TestStatus.LATEX_ERROR
        result.exception_type = "MissingPDF"
        result.traceback = "pdflatex exited 0 but wrapper.pdf was not created."
        return result

    # --- Stage 6: Rasterize PDF → tikz_rendered.png -------------------------
    rendered_png = test_dir / "tikz_rendered.png"
    result.rendered_png = rendered_png

    ok, error = pdf_to_png(pdf_path, rendered_png, dpi=150)
    if not ok:
        result.status = TestStatus.RENDER_ERROR
        result.exception_type = "RenderError"
        result.traceback = error
        return result

    if not rendered_png.exists():
        result.status = TestStatus.RENDER_ERROR
        result.exception_type = "MissingRenderedPNG"
        result.traceback = "pdf_to_png returned success but tikz_rendered.png was not created."
        return result

    # --- Stage 7: Compare images --------------------------------------------
    diff_png = test_dir / "diff.png"
    result.diff_png = diff_png

    try:
        cmp: CompareResult = compare_images(
            ref_path=ref_png,
            rendered_path=rendered_png,
            diff_path=diff_png,
            threshold_rms=config.threshold_rms,
            threshold_ssim=config.threshold_ssim,
        )
    except Exception as exc:
        result.status = TestStatus.RENDER_ERROR
        result.exception_type = type(exc).__name__
        result.traceback = traceback.format_exc()
        return result

    result.rms = cmp.rms
    result.ssim = cmp.ssim
    result.max_diff = cmp.max_diff
    result.size_mismatch = cmp.size_mismatch

    if cmp.passed:
        result.status = TestStatus.PASS
    else:
        result.status = TestStatus.VISUAL_MISMATCH

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_script(
    script_path: Path,
    cwd: Path,
    timeout: int,
) -> tuple[bool, str]:
    """Execute plot_script.py as a subprocess. Returns (success, error_text)."""
    cmd = [sys.executable, str(script_path.resolve())]

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd.resolve()),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, f"Script timed out after {timeout}s."
    except Exception as exc:
        return False, f"Failed to launch script subprocess: {exc}"

    if proc.returncode != 0:
        error = proc.stderr.strip() or proc.stdout.strip() or "Unknown error."
        return False, error

    return True, ""
