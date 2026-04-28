"""
latex_renderer.py — wrap figure.tikz in a standalone LaTeX document,
compile with pdflatex, and rasterize to PNG using pdf2image.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


# ---------------------------------------------------------------------------
# Standalone LaTeX wrapper template
# ---------------------------------------------------------------------------

_WRAPPER_TEMPLATE = r"""\documentclass[tikz,border=2pt]{{standalone}}
\usepackage{{pgfplots}}
\pgfplotsset{{compat=newest}}
\usepackage{{amsmath}}
\usepackage{{amssymb}}
\begin{{document}}
\input{{{tikz_filename}}}
\end{{document}}
"""


def create_wrapper_tex(work_dir: Path, tikz_filename: str = "figure.tikz") -> Path:
    """
    Write wrapper.tex into work_dir that inputs tikz_filename.

    Returns the path to the created wrapper.tex.
    """
    content = _WRAPPER_TEMPLATE.format(tikz_filename=tikz_filename)
    wrapper_path = work_dir / "wrapper.tex"
    wrapper_path.write_text(content, encoding="utf-8")
    return wrapper_path


# ---------------------------------------------------------------------------
# LaTeX compilation
# ---------------------------------------------------------------------------

def compile_latex(
    work_dir: Path,
    tex_file: Path,
    timeout: int,
) -> tuple[bool, str]:
    """
    Compile tex_file with pdflatex.

    Returns (success, log_text).
    The log is also written to work_dir/latex.log.
    """
    pdflatex = shutil.which("pdflatex")
    if not pdflatex:
        msg = (
            "pdflatex not found. Please install a LaTeX distribution "
            "(e.g., MiKTeX on Windows or TeX Live on Linux/macOS)."
        )
        return False, msg

    cmd = [
        pdflatex,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-output-directory", str(work_dir),
        str(tex_file),
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(work_dir.resolve()),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        msg = f"pdflatex timed out after {timeout}s."
        _write_log(work_dir, msg)
        return False, msg
    except Exception as exc:
        msg = f"Failed to launch pdflatex: {exc}"
        _write_log(work_dir, msg)
        return False, msg

    combined_log = result.stdout + "\n" + result.stderr
    _write_log(work_dir, combined_log)

    if result.returncode != 0:
        # Extract a short excerpt of the error from the log
        excerpt = _extract_error_excerpt(combined_log)
        return False, excerpt

    return True, combined_log


def _write_log(work_dir: Path, text: str) -> None:
    try:
        (work_dir / "latex.log").write_text(text, encoding="utf-8", errors="replace")
    except OSError:
        pass


def _extract_error_excerpt(log: str, max_lines: int = 20) -> str:
    """Return lines around the first '!' error marker in the log."""
    lines = log.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("!"):
            start = max(0, i - 2)
            end = min(len(lines), i + max_lines)
            return "\n".join(lines[start:end])
    # No '!' found — return the last max_lines lines
    return "\n".join(lines[-max_lines:])


# ---------------------------------------------------------------------------
# PDF → PNG rasterization
# ---------------------------------------------------------------------------

def pdf_to_png(pdf_path: Path, png_path: Path, dpi: int = 150) -> tuple[bool, str]:
    """
    Convert the first page of a PDF to a PNG using pdf2image.

    Returns (success, error_message).
    """
    try:
        from pdf2image import convert_from_path  # type: ignore[import]
    except ImportError:
        return False, "pdf2image is not installed. Run: pip install pdf2image"

    try:
        pages = convert_from_path(str(pdf_path), dpi=dpi, fmt="png", first_page=1, last_page=1)
    except Exception as exc:
        return False, f"pdf2image conversion failed: {exc}"

    if not pages:
        return False, "pdf2image returned no pages."

    try:
        pages[0].save(str(png_path))
    except Exception as exc:
        return False, f"Failed to save PNG: {exc}"

    return True, ""
