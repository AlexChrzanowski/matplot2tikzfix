"""
cli.py — Click-based command-line interface for agentic_tikz_tester.

Usage:
    python -m agentic_tikz_tester run --n 10 --out runs/demo
    python -m agentic_tikz_tester run --no-llm --n 5 --out runs/smoke
"""
from __future__ import annotations

import sys
from pathlib import Path

import click

from .config import Config
from .example_suite import GeneratedScript, get_examples
from .report import save_passing_report, save_report
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
@click.option("--failures-dir", "failures_dir", default="failures", show_default=True, help="Directory for failure reports.")
@click.option("--model", "model", default="claude-3-5-haiku-20241022", show_default=True, help="LLM model name.")
@click.option("--provider", "provider", default="anthropic", show_default=True,
              type=click.Choice(["anthropic", "openai"]), help="LLM provider.")
@click.option("--threshold-rms", "threshold_rms", default=8.0, show_default=True,
              help="RMS pixel difference failure threshold.")
@click.option("--threshold-ssim", "threshold_ssim", default=0.985, show_default=True,
              help="SSIM failure threshold (lower = more tolerant).")
@click.option("--timeout", "timeout", default=30, show_default=True,
              help="Timeout per pipeline stage in seconds.")
@click.option("--keep-passing", "keep_passing", is_flag=True, default=False,
              help="Keep artifacts for passing tests.")
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
    threshold_rms: float,
    threshold_ssim: float,
    timeout: int,
    keep_passing: bool,
    transpiler: str,
    seed: int | None,
    no_llm: bool,
) -> None:
    """Run the visual regression harness."""

    config = Config(
        n=n,
        out=out,
        model=model,
        threshold_rms=threshold_rms,
        threshold_ssim=threshold_ssim,
        timeout=timeout,
        keep_passing=keep_passing,
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
        "threshold_rms": threshold_rms,
        "threshold_ssim": threshold_ssim,
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
    # Counters
    # ------------------------------------------------------------------
    totals: dict[str, int] = {s.value: 0 for s in TestStatus}
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
            click.echo(f"\r[{i}/{effective_n}] GENERATION_ERROR                    ")
            result = TestResult(
                test_id=test_id,
                status=TestStatus.GENERATION_ERROR,
                exception_type="GenerationError",
                traceback="LLM failed to return valid JSON after 2 attempts.",
                test_dir=test_dir,
            )
            totals[TestStatus.GENERATION_ERROR.value] += 1
            failure_dir = save_report(
                result, test_dir, fail_path, failure_index, config_meta
            )
            failure_index += 1
            click.echo(f"  -> {failure_dir}")
            continue

        click.echo(f"\r[{i}/{effective_n}] generated ({', '.join(script.features[:3])})")

        result = run_test(test_id, test_dir, script, config)
        totals[result.status.value] += 1

        _print_result_line(i, effective_n, result)

        if result.status != TestStatus.PASS:
            failure_dir = save_report(
                result,
                test_dir,
                fail_path,
                failure_index,
                config_meta,
            )
            failure_index += 1
            click.echo(f"  -> {failure_dir}")
        elif keep_passing:
            save_passing_report(result, test_dir, config_meta)
        else:
            # Clean up test dir for passing tests to save disk space
            # (keep plot_script.py for reference)
            pass  # TODO: optional cleanup of passing artifacts

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    _print_summary(totals, effective_n, fail_path)


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
    status = result.status.value.upper()

    if result.rms is not None and result.ssim is not None:
        metrics = f"RMS={result.rms:.2f}, SSIM={result.ssim:.4f}"
    else:
        metrics = ""

    if result.status == TestStatus.PASS:
        verdict = "PASS"
        line = f"{prefix} {metrics}  {verdict}"
    else:
        verdict = "FAIL"
        detail = result.exception_type or status
        if metrics:
            line = f"{prefix} {metrics}  {verdict} ({detail})"
        else:
            line = f"{prefix} {verdict} ({detail})"

    click.echo(line)


def _print_summary(totals: dict[str, int], n: int, fail_path: Path) -> None:
    passes = totals.get(TestStatus.PASS.value, 0)
    click.echo("\n" + "=" * 50)
    click.echo(f"Results: {passes}/{n} passed")
    click.echo(f"  visual_mismatch : {totals.get(TestStatus.VISUAL_MISMATCH.value, 0)}")
    click.echo(f"  generation_error: {totals.get(TestStatus.GENERATION_ERROR.value, 0)}")
    click.echo(f"  script_error    : {totals.get(TestStatus.SCRIPT_ERROR.value, 0)}")
    click.echo(f"  transpile_error : {totals.get(TestStatus.TRANSPILE_ERROR.value, 0)}")
    click.echo(f"  latex_error     : {totals.get(TestStatus.LATEX_ERROR.value, 0)}")
    click.echo(f"  render_error    : {totals.get(TestStatus.RENDER_ERROR.value, 0)}")
    total_failures = n - passes
    if total_failures > 0:
        click.echo(f"\nFailure reports saved to: {fail_path.resolve()}")
    click.echo("=" * 50)


def _next_failure_index(fail_path: Path) -> int:
    """Find the next available failure_XXXX index."""
    existing = [
        int(d.name.split("_")[1])
        for d in fail_path.iterdir()
        if d.is_dir() and d.name.startswith("failure_") and d.name.split("_")[1].isdigit()
    ] if fail_path.exists() else []
    return max(existing, default=0) + 1
