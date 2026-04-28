from __future__ import annotations

SYSTEM_PROMPT = """\
You are generating deterministic Matplotlib test cases for a visual regression system \
that compares Matplotlib output against tikzplotlib/PGFPlots output.

Return ONLY valid JSON with exactly two keys:
  "features": a short list of Matplotlib features used (strings)
  "code": a complete Python script as a single string

Script requirements:
- Use only matplotlib and numpy (no pandas, seaborn, or other libs).
- The very first two lines must be:
    import matplotlib
    matplotlib.use("Agg")
- Import matplotlib.pyplot as plt and numpy as np.
- Define a function  create_figure()  that creates and returns exactly one matplotlib Figure.
- In the main block, save the figure:
    if __name__ == "__main__":
        fig = create_figure()
        fig.savefig("reference.png", dpi=120)
- Do NOT call plt.show().
- Do NOT read or write any files other than "reference.png".
- Do NOT use: network, subprocess, pathlib, os, sys, pandas, seaborn, or external data files.
- Do NOT use 3D plots, animations, interactive widgets.
- Keep data arrays small (< 200 points).
- Make exactly one figure per script.
- Use fixed random seeds (np.random.seed(42)) wherever randomness is used.
- Do NOT use any external image files.
- Do NOT use huge LaTeX strings or unusual fonts.

Feature guidance:
- Prefer simple plots, but combine 2-4 features that may stress a matplotlib-to-PGFPlots transpiler.
- Good feature interactions:
    * log scale with markers + legend + grid
    * bar chart with rotated categorical ticks + value labels
    * scatter + alpha + colorbar + custom axis limits
    * fill_between + transparency + legend
    * errorbar + capsize + log y-axis
    * subplots (max 2 axes) + shared x-axis + mathtext labels
    * annotations with arrows + tight layout
    * histogram + density=True + legend
    * step plot + custom ticks
    * imshow + colorbar + axis labels
    * twin axes (twinx)
    * inverted axis
    * date-like or categorical tick labels
    * rotated tick labels
    * mathtext in labels or title ($\\alpha$, $x^2$, etc.)
- Vary among: line, scatter, bar, barh, errorbar, hist, step, fill_between, imshow.
- Legends, titles, x/y labels are encouraged.
- Grid may be on or off.
- Alpha transparency is fine.
- Colorbars: occasionally.
- Do NOT use twin axes more than very occasionally.

The JSON must be valid. Escape all backslashes in the "code" string. \
Do not add any text outside the JSON object.
"""


def build_user_prompt(test_index: int, seed: int) -> str:
    return (
        f"Test index: {test_index}, seed: {seed}. "
        "Please generate a distinct, simple Matplotlib figure that is DIFFERENT from a plain line plot. "
        "Choose a feature combination from the guidance that is likely to reveal a tikzplotlib rendering difference. "
        "Return only the JSON object."
    )


RETRY_SYSTEM_PROMPT = """\
Your previous response was not valid JSON. Return ONLY a JSON object with keys \
"features" (list of strings) and "code" (string). No markdown, no explanation, \
no code fences. The JSON must be parseable by Python's json.loads().
"""


def build_retry_prompt(test_index: int, seed: int, previous_response: str) -> str:
    return (
        f"Test index: {test_index}, seed: {seed}. "
        f"Your previous response could not be parsed as JSON. "
        f"Previous response (first 500 chars): {previous_response[:500]!r}\n\n"
        "Try again. Return ONLY valid JSON with keys 'features' and 'code'."
    )
