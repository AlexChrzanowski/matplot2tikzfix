"""
_transpile_helper.py — run as a subprocess inside the test working directory.

Usage:
    python _transpile_helper.py --script plot_script.py --output figure.tikz
                                 --transpiler makintikz

Exits 0 on success, 1 on any error (traceback printed to stderr).

Security note:
  This script is executed in a subprocess with cwd set to the test directory.
  All generated code is run here, not in the main harness process.
  TODO: stronger sandboxing — replace subprocess with Docker/nsjail.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import traceback
from pathlib import Path


def _import_script(script_path: str):
    """Dynamically import the generated plot script as a module."""
    path = Path(script_path).resolve()
    spec = importlib.util.spec_from_file_location("_plot_script", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def _transpile_makintikz(fig, output_path: str) -> None:
    """Transpile using the local matplot2tikz (MakinTikZ) package."""
    # Adapter: import the local matplot2tikz package.
    # TODO: if the package is renamed or moved, update this import.
    import matplot2tikz  # type: ignore[import]

    code = matplot2tikz.get_tikz_code(
        figure=fig,
        wrap=True,
        standalone=False,
        include_disclaimer=False,
    )
    Path(output_path).write_text(code, encoding="utf-8")


def _transpile_tikzplotlib(fig, output_path: str) -> None:
    """Transpile using the tikzplotlib package."""
    try:
        import tikzplotlib  # type: ignore[import]
        tikzplotlib.save(output_path, figure=fig)
    except Exception:
        # Fallback: use get_tikz_code and write text manually.
        import tikzplotlib  # type: ignore[import]
        code = tikzplotlib.get_tikz_code(figure=fig)
        Path(output_path).write_text(code, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Transpile a matplotlib script to TikZ")
    parser.add_argument("--script", required=True, help="Path to the generated plot_script.py")
    parser.add_argument("--output", required=True, help="Output path for figure.tikz")
    parser.add_argument(
        "--transpiler",
        default="makintikz",
        choices=["makintikz", "tikzplotlib"],
        help="Transpiler backend to use",
    )
    args = parser.parse_args()

    try:
        module = _import_script(args.script)
    except Exception:
        print("ERROR: Failed to import script.", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    if not hasattr(module, "create_figure"):
        print(
            f"ERROR: Script {args.script!r} does not define create_figure().",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        fig = module.create_figure()
    except Exception:
        print("ERROR: create_figure() raised an exception.", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    try:
        if args.transpiler == "makintikz":
            _transpile_makintikz(fig, args.output)
        else:
            _transpile_tikzplotlib(fig, args.output)
    except Exception:
        print(f"ERROR: Transpilation with {args.transpiler!r} failed.", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    # Close all matplotlib figures to avoid resource leaks
    try:
        import matplotlib.pyplot as plt
        plt.close("all")
    except Exception:
        pass


if __name__ == "__main__":
    main()
