"""
cli.py â€” Click-based command-line interface for agentic_tikz_tester.

Usage:
    python -m agentic_tikz_tester run --n 10 --out runs/demo
    python -m agentic_tikz_tester run --no-llm --n 5 --out runs/smoke
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import click

from .config import Config
from .example_suite import GeneratedScript, get_examples
from .report import save_error_report, save_test_result
from .runner import TestResult, TestStatus, run_test


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
def main() -> None:
    """Agentic visual regression tester for tikzplotlib / MakinTikZ."""


# ---------------------------------------------------------------------------
# run command
# ---------------------------------------------------------------------------

@main.command()
@click.option("--n", "n", default=10, show_default=True, help="Number of test cases to run.")
@click.option("--out", "out", default="runs/output", show_default=True, help="Output directory.")
@click.option("--failures-dir", "failures_dir", default="failures", show_default=True,
              help="Directory for pipeline-error reports.")
@click.option("--model", "model", default="claude-haiku-4-5-20251001", show_default=True,
              help="LLM model name.")
@click.option("--provider", "provider", default="anthropic", show_default=True,
              type=click.Choice(["anthropic", "openai"]), help="LLM provider.")
@click.option("--flag-rms", "flag_rms", default=20.0, show_default=True,
              help="Flag tests with trimmed-image RMS above this value.")
@click.option("--flag-ssim", "flag_ssim", default=0.85, show_default=True,
              help="Flag tests with trimmed-image SSIM below this value.")
@click.option("--flag-edge-ssim", "flag_edge_ssim", default=0.50, show_default=True,
              help="Flag tests with edge-structure SSIM below this value.")
@click.option("--timeout", "timeout", default=30, show_default=True,
              help="Timeout per pipeline stage in seconds.")
@click.option("--transpiler", "transpiler", default="makintikz", show_default=True,
              type=click.Choice(["makintikz", "tikzplotlib"]),
              help="Transpiler backend.")
@click.option("--seed", "seed", default=None, type=int, help="Base random seed.")
@click.option("--no-llm", "no_llm", is_flag=True, default=False,
              help="Use 5 built-in example scripts instead of calling an LLM API.")
def run(
    n: int,
    out: str,
    failures_dir: str,
    model: str,
    provider: str,
    flag_rms: float,
    flag_ssim: float,
    flag_edge_ssim: float,
    timeout: int,
    transpiler: str,
    seed: int | None,
    no_llm: bool,
) -> None:
    """Run the visual regression harness."""

    config = Config(
        n=n,
        out=out,
        model=model,
        flag_rms=flag_rms,
        flag_ssim=flag_ssim,
        flag_edge_ssim=flag_edge_ssim,
        timeout=timeout,
        transpiler=transpiler,
        seed=seed,
        provider=provider,
        no_llm=no_llm,
        failures_dir=failures_dir,
    )

    out_path = Path(out).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    fail_path = Path(failures_dir).resolve()
    fail_path.mkdir(parents=True, exist_ok=True)

    config_meta = {
        "model": model,
        "provider": provider,
        "transpiler": transpiler,
        "seed": seed,
        "flag_rms": flag_rms,
        "flag_ssim": flag_ssim,
        "flag_edge_ssim": flag_edge_ssim,
    }

    # ------------------------------------------------------------------
    # Build the script source (LLM or built-in examples)
    # ------------------------------------------------------------------
    if no_llm:
        examples = get_examples()
        effective_n = min(n, len(examples))
        if n > len(examples):
            click.echo(
                f"Warning: --no-llm mode only has {len(examples)} built-in examples. "
                f"Running {len(examples)} tests."
            )
        script_source = _ExampleSource(examples, effective_n)
    else:
        script_source = _LLMSource(config)  # type: ignore[assignment]
        effective_n = n

    # ------------------------------------------------------------------
    # Counters / result accumulator
    # ------------------------------------------------------------------
    all_results: list[TestResult] = []
    error_count: dict[str, int] = {
        TestStatus.GENERATION_ERROR.value: 0,
        TestStatus.SCRIPT_ERROR.value: 0,
        TestStatus.TRANSPILE_ERROR.value: 0,
        TestStatus.LATEX_ERROR.value: 0,
        TestStatus.RENDER_ERROR.value: 0,
    }
    failure_index = _next_failure_index(fail_path)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    for i in range(1, effective_n + 1):
        test_id = f"test_{i:04d}"
        test_dir = out_path / test_id

        click.echo(f"[{i}/{effective_n}] generating ...", nl=False)

        script = script_source.get(i)
        if script is None:
            click.echo(f"\r[{i}/{effective_n}] GENERATION_ERROR                         ")
            test_dir.mkdir(parents=True, exist_ok=True)
            result = TestResult(
                test_id=test_id,
                status=TestStatus.GENERATION_ERROR,
                exception_type="GenerationError",
                traceback="LLM failed to return valid JSON after 2 attempts.",
                test_dir=test_dir,
            )
            all_results.append(result)
            error_count[TestStatus.GENERATION_ERROR.value] += 1
            err_dir = save_error_report(
                result, test_dir, fail_path, failure_index, config_meta
            )
            failure_index += 1
            click.echo(f"  -> {err_dir}")
            continue

        click.echo(f"\r[{i}/{effective_n}] generated ({', '.join(script.features[:3])})")

        result = run_test(test_id, test_dir, script, config)
        all_results.append(result)

        _print_result_line(i, effective_n, result)

        if result.status == TestStatus.COMPLETE:
            save_test_result(result, test_dir, config_meta)
        else:
            error_count[result.status.value] = error_count.get(result.status.value, 0) + 1
            err_dir = save_error_report(
                result, test_dir, fail_path, failure_index, config_meta
            )
            failure_index += 1
            click.echo(f"  -> {err_dir}")

    # ------------------------------------------------------------------
    # Write summary files
    # ------------------------------------------------------------------
    _write_summary(out_path, all_results)

    # ------------------------------------------------------------------
    # Print summary table
    # ------------------------------------------------------------------
    _print_summary(all_results, effective_n, error_count, fail_path)


# ---------------------------------------------------------------------------
# Script source abstractions
# ---------------------------------------------------------------------------

class _ExampleSource:
    def __init__(self, examples: list[GeneratedScript], n: int) -> None:
        self._examples = examples
        self._n = n

    def get(self, i: int) -> GeneratedScript | None:
        idx = (i - 1) % len(self._examples)
        return self._examples[idx]


class _LLMSource:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._generator = self._build_generator()

    def _build_generator(self):
        from .llm_generator import LLMGenerator, make_provider
        provider_obj = make_provider(self._config.provider, self._config.model)
        return LLMGenerator(provider_obj)

    def get(self, i: int) -> GeneratedScript | None:
        effective_seed = (self._config.seed or 0) + i
        return self._generator.generate_script(i, effective_seed)


# ---------------------------------------------------------------------------
# Printing helpers
# ---------------------------------------------------------------------------

def _print_result_line(i: int, n: int, result: TestResult) -> None:
    prefix = f"[{i}/{n}]"

    if result.status == TestStatus.COMPLETE:
        rms_s = f"RMS={result.rms:6.2f}" if result.rms is not None else "RMS=N/A"
        ssim_s = f"SSIM={result.ssim:.4f}" if result.ssim is not None else "SSIM=N/A"
        ess_s = f"edge={result.edge_ssim:.4f}" if result.edge_ssim is not None else "edge=N/A"
        flag_s = "  [FLAGGED]" if result.flagged else ""
        click.echo(f"{prefix} {rms_s}  {ssim_s}  {ess_s}{flag_s}")
    else:
        detail = result.exception_type or result.status.value.upper()
        click.echo(f"{prefix} ERROR ({detail})")


def _print_summary(
    results: list[TestResult],
    n: int,
    error_count: dict[str, int],
    fail_path: Path,
) -> None:
    complete = [r for r in results if r.status == TestStatus.COMPLETE]
    flagged = [r for r in complete if r.flagged]
    errors = [r for r in results if r.status != TestStatus.COMPLETE]

    click.echo("\n" + "=" * 65)
    click.echo(f"Results: {len(complete)}/{n} completed  |  {len(flagged)} flagged  |  {len(errors)} errors")

    if complete:
        click.echo("\nCompleted tests (sorted by RMS desc):")
        for r in sorted(complete, key=lambda x: x.rms or 0, reverse=True):
            rms_s = f"{r.rms:6.2f}" if r.rms is not None else "  N/A"
            ssim_s = f"{r.ssim:.4f}" if r.ssim is not None else "  N/A"
            ess_s = f"{r.edge_ssim:.4f}" if r.edge_ssim is not None else "  N/A"
            flag_s = " [F]" if r.flagged else "    "
            click.echo(f"  {r.test_id}  RMS={rms_s}  SSIM={ssim_s}  edge={ess_s}{flag_s}")

    if errors:
        click.echo("\nPipeline errors:")
        for s, c in error_count.items():
            if c:
                click.echo(f"  {s:<22}: {c}")
        click.echo(f"  Error reports saved to: {fail_path}")

    click.echo("=" * 65)


# ---------------------------------------------------------------------------
# Summary file writers
# ---------------------------------------------------------------------------

def _write_summary(out_path: Path, results: list[TestResult]) -> None:
    rows = []
    for r in results:
        rows.append({
            "test_id": r.test_id,
            "status": r.status.value,
            "rms": r.rms,
            "ssim": r.ssim,
            "edge_ssim": r.edge_ssim,
            "max_diff": r.max_diff,
            "size_mismatch": r.size_mismatch,
            "flagged": r.flagged,
            "features": ";".join(r.features),
        })

    # JSON
    (out_path / "summary.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # CSV
    if rows:
        csv_path = out_path / "summary.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _next_failure_index(fail_path: Path) -> int:
    existing = [
        int(d.name.split("_")[1])
        for d in fail_path.iterdir()
        if d.is_dir() and d.name.startswith("failure_") and d.name.split("_")[1].isdigit()
    ] if fail_path.exists() else []
    return max(existing, default=0) + 1

