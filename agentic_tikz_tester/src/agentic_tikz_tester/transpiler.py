"""
transpiler.py — invoke _transpile_helper.py as a subprocess.

Returns (success, error_text) tuple.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


# Absolute path to _transpile_helper.py so it can be invoked from any cwd.
_HELPER_PATH = Path(__file__).parent / "_transpile_helper.py"


def transpile(
    script_path: Path,
    output_path: Path,
    transpiler_name: str,
    timeout: int,
    cwd: Path,
) -> tuple[bool, str]:
    """
    Run _transpile_helper.py as a subprocess.

    Parameters
    ----------
    script_path:    Absolute path to plot_script.py
    output_path:    Absolute path where figure.tikz should be written
    transpiler_name: "makintikz" or "tikzplotlib"
    timeout:        Seconds before the subprocess is killed
    cwd:            Working directory for the subprocess

    Returns
    -------
    (success, error_text)
    """
    cmd = [
        sys.executable,
        str(_HELPER_PATH),
        "--script", str(script_path.resolve()),
        "--output", str(output_path.resolve()),
        "--transpiler", transpiler_name,
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd.resolve()),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, f"Transpiler timed out after {timeout}s."
    except Exception as exc:
        return False, f"Failed to launch transpiler subprocess: {exc}"

    if result.returncode != 0:
        error_text = result.stderr.strip() or result.stdout.strip() or "Unknown transpiler error."
        return False, error_text

    return True, ""
