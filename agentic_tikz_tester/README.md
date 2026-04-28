# Agentic TikZ Visual Regression Tester

A local Python CLI tool that stress-tests tikzplotlib / MakinTikZ by generating Matplotlib figures (via an LLM or built-in examples), transpiling them to TikZ/PGFPlots, rendering the result back to PNG via LaTeX, and comparing the two renders pixel-by-pixel.

Every failure is automatically saved as a clean, self-contained reproduction folder.

---

## New machine setup (minimum steps)

### 1. System requirements

| Requirement | Windows | Linux/macOS |
|-------------|---------|-------------|
| Python 3.10+ | [python.org](https://www.python.org/downloads/) | `pyenv` or system package |
| `pdflatex` | [MiKTeX](https://miktex.org/download) — tick "Install missing packages on the fly" | `apt install texlive-full` |
| Poppler (for pdf2image) | Download from [oschwartz10612/poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases), extract, add the `Library/bin/` folder to your PATH | `apt install poppler-utils` / `brew install poppler` |

After installing MiKTeX on Windows, open **MiKTeX Console → Updates** and apply all updates, then run any pdflatex command once so it installs `pgfplots` and `standalone` on first use.

### 2. Clone / copy the repository

```bash
git clone <repo-url>
cd matplot2tikzfix
```

### 3. Create and activate a virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install the matplot2tikz (MakinTikZ) package

```bash
pip install -e .
```

### 5. Install the agentic tester

```bash
cd agentic_tikz_tester
pip install -e .
cd ..
```

### 6. Set your Anthropic API key

```bash
# Windows (Command Prompt, current session only)
set ANTHROPIC_API_KEY=sk-ant-...

# Windows (PowerShell, current session only)
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# Linux/macOS
export ANTHROPIC_API_KEY=sk-ant-...
```

To persist it across sessions on Windows, use **System Properties → Environment Variables** and add `ANTHROPIC_API_KEY` as a user variable.

### 7. Verify with the no-LLM smoke test

```bash
cd agentic_tikz_tester
python -m agentic_tikz_tester run --no-llm --n 5 --out runs/smoke
```

You should see 5 tests run through the full pipeline and visual-mismatch failures reported in `failures/`.

### 8. Run with the LLM

```bash
python -m agentic_tikz_tester run --n 10 --out runs/demo
```

---

## Prerequisites

- Python 3.10+
- A LaTeX installation with `pdflatex` on PATH:
  - **Windows**: [MiKTeX](https://miktex.org/) or [TeX Live](https://tug.org/texlive/)
  - **Linux/macOS**: TeX Live (`apt install texlive-full` or similar)
- Poppler (for `pdf2image`):
  - **Windows**: download from https://github.com/oschwartz10612/poppler-windows/releases, add `bin/` to PATH
  - **Linux**: `apt install poppler-utils`
  - **macOS**: `brew install poppler`

---

## Installation

```bash
cd agentic_tikz_tester
pip install -e .
```

To use with the Anthropic API:

```bash
pip install -e ".[openai]"   # optional, for OpenAI provider
```

---

## Quick Start (no API key required)

Run the 5 built-in example figures:

```bash
python -m agentic_tikz_tester run --no-llm --n 5 --out runs/smoke
```

This will:
1. Execute each hand-written Matplotlib script
2. Transpile it with MakinTikZ (`matplot2tikz.get_tikz_code`)
3. Compile via pdflatex
4. Compare reference vs rendered PNG
5. Save failure reports to `failures/`

---

## LLM-driven mode

Set your API key:

```bash
set ANTHROPIC_API_KEY=sk-ant-...   # Windows
export ANTHROPIC_API_KEY=sk-ant-...  # Linux/macOS
```

Run:

```bash
python -m agentic_tikz_tester run --n 10 --out runs/demo
```

---

## CLI Reference

```
python -m agentic_tikz_tester run [OPTIONS]

Options:
  --n INTEGER              Number of test cases          [default: 10]
  --out TEXT               Output directory              [default: runs/output]
  --failures-dir TEXT      Failures directory            [default: failures]
  --model TEXT             LLM model name                [default: claude-opus-4-5]
  --provider [anthropic|openai]  LLM provider           [default: anthropic]
  --threshold-rms FLOAT    RMS failure threshold         [default: 8.0]
  --threshold-ssim FLOAT   SSIM failure threshold        [default: 0.985]
  --timeout INTEGER        Seconds per pipeline stage    [default: 30]
  --keep-passing           Store passing test artifacts
  --transpiler [makintikz|tikzplotlib]  Transpiler       [default: makintikz]
  --seed INTEGER           Base random seed
  --no-llm                 Use 5 built-in examples
```

---

## Output Structure

```
runs/demo/
  test_0001/
    plot_script.py       ← generated Python script
    reference.png        ← Matplotlib render
    figure.tikz          ← transpiled TikZ/PGFPlots
    wrapper.tex          ← standalone LaTeX document
    wrapper.pdf          ← compiled PDF
    tikz_rendered.png    ← rasterized TikZ render
    diff.png             ← amplified pixel difference
    latex.log            ← pdflatex output
    metadata.json        ← metrics (optional, if --keep-passing)

failures/
  failure_0001/
    plot_script.py
    reference.png
    tikz_rendered.png
    diff.png
    figure.tikz
    wrapper.tex
    latex.log
    metadata.json        ← full machine-readable metadata
    report.md            ← human-readable bug report
```

---

## Failure Statuses

| Status | Meaning |
|--------|---------|
| `visual_mismatch` | Both renders succeeded but RMS/SSIM exceeded threshold |
| `script_error` | Generated Python script crashed or didn't save `reference.png` |
| `transpile_error` | `get_tikz_code()` or `tikzplotlib.save()` raised an exception |
| `latex_error` | `pdflatex` failed to compile `wrapper.tex` |
| `render_error` | PDF-to-PNG conversion failed |
| `generation_error` | LLM returned invalid JSON twice in a row |

---

## Architecture

```
cli.py              ← Click commands, main loop, progress printing
runner.py           ← Orchestrates 7-stage pipeline, returns TestResult
transpiler.py       ← Launches _transpile_helper.py as subprocess
_transpile_helper.py← Imports generated script, calls create_figure(), saves figure.tikz
latex_renderer.py   ← Creates wrapper.tex, runs pdflatex, calls pdf2image
image_compare.py    ← RMS + SSIM comparison, saves diff.png
report.py           ← Copies artifacts, writes metadata.json + report.md
llm_generator.py    ← Anthropic/OpenAI providers, JSON retry logic
prompts.py          ← System prompt + user prompt builders
example_suite.py    ← 5 hand-written test cases for --no-llm mode
config.py           ← Config dataclass with all defaults
```

---

## TODO

- **Minimization**: bisect failing script to minimal repro
- **Feature coverage**: avoid regenerating already-covered feature combos
- **Stronger sandboxing**: replace subprocess with Docker/nsjail
- **Agent feedback loop**: feed failure report back to LLM for next iteration
- **GitHub issue formatter**: post repro to issues automatically
- **OpenAI provider**: complete `OpenAIProvider.generate()` implementation
