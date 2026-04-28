"""
image_compare.py — structural comparison of reference PNG vs TikZ-rendered PNG.

Strategy (iteration 2):
  - Trim near-white borders from both images before comparing, so that
    matplotlib's tight margins and LaTeX standalone's border do not dominate
    the pixel diff.
  - Compute raw RMS and SSIM on the trimmed + size-matched images.
  - Compute edge-SSIM: run Canny edge detection on both grayscale trimmed images
    and compute SSIM on the resulting binary edge maps. This captures structural
    similarity (plot lines, axes, labels) while ignoring font, color, and style
    rendering differences that are expected to differ between matplotlib and PGFPlots.
  - Save an amplified diff image (diff.png).
  - Save a side-by-side composite (composite.png): [reference | rendered | diff]
    for quick human inspection without opening three separate files.
  - No pass/fail verdict is computed here — that is left to the caller.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


# Pixel brightness threshold for "near-white" border trimming.
# Any row/column whose mean brightness across all channels exceeds this
# value (0-255) is considered background padding.
_WHITE_THRESHOLD = 240

# Padding in pixels to keep around the trimmed content bounding box.
_TRIM_PADDING = 6


@dataclass
class CompareResult:
    rms: float
    ssim: float
    edge_ssim: float
    max_diff: float
    size_mismatch: bool
    ref_size: tuple[int, int]
    rendered_size: tuple[int, int]
    ref_trimmed_size: tuple[int, int]
    rendered_trimmed_size: tuple[int, int]


def compare_images(
    ref_path: Path,
    rendered_path: Path,
    diff_path: Path,
    composite_path: Path,
) -> CompareResult:
    """
    Load both images, trim whitespace, compare structurally, and write outputs.

    Writes:
      - diff_path: amplified absolute pixel difference (×4, clipped to 255)
      - composite_path: side-by-side strip [reference | rendered | diff]

    Returns a CompareResult with metrics but no pass/fail verdict.
    """
    ref_img = Image.open(ref_path).convert("RGB")
    rendered_img = Image.open(rendered_path).convert("RGB")

    ref_size = ref_img.size
    rendered_size = rendered_img.size

    # Trim near-white borders independently
    ref_trimmed = _trim_whitespace(ref_img)
    rendered_trimmed = _trim_whitespace(rendered_img)

    ref_trimmed_size = ref_trimmed.size
    rendered_trimmed_size = rendered_trimmed.size

    # Resize rendered to match reference trimmed size for pixel comparison
    size_mismatch = ref_trimmed_size != rendered_trimmed_size
    if size_mismatch:
        rendered_trimmed = rendered_trimmed.resize(ref_trimmed_size, Image.LANCZOS)

    ref_arr = np.asarray(ref_trimmed, dtype=np.float32)
    rendered_arr = np.asarray(rendered_trimmed, dtype=np.float32)

    diff_arr = np.abs(ref_arr - rendered_arr)

    rms = float(np.sqrt(np.mean(diff_arr ** 2)))
    max_diff = float(diff_arr.max())

    ssim = _compute_ssim(ref_arr, rendered_arr)
    edge_ssim = _compute_edge_ssim(ref_arr, rendered_arr)

    # Save amplified diff image
    diff_amplified = np.clip(diff_arr * 4, 0, 255).astype(np.uint8)
    diff_img = Image.fromarray(diff_amplified)
    diff_img.save(diff_path)

    # Save composite side-by-side
    _save_composite(ref_trimmed, rendered_trimmed, diff_img, composite_path)

    return CompareResult(
        rms=rms,
        ssim=ssim,
        edge_ssim=edge_ssim,
        max_diff=max_diff,
        size_mismatch=size_mismatch,
        ref_size=ref_size,
        rendered_size=rendered_size,
        ref_trimmed_size=ref_trimmed_size,
        rendered_trimmed_size=rendered_trimmed_size,
    )


# ---------------------------------------------------------------------------
# Whitespace trimming
# ---------------------------------------------------------------------------

def _trim_whitespace(img: Image.Image) -> Image.Image:
    """
    Crop near-white borders from img.

    Finds the tightest bounding box where any row or column has at least one
    pixel with a channel value below _WHITE_THRESHOLD, then pads by
    _TRIM_PADDING pixels (clamped to image bounds).
    """
    arr = np.asarray(img)  # (H, W, 3)

    # A pixel is "content" if any channel is dark enough
    content_mask = np.any(arr < _WHITE_THRESHOLD, axis=2)  # (H, W)

    rows = np.any(content_mask, axis=1)
    cols = np.any(content_mask, axis=0)

    if not rows.any():
        # Fully white image — return as-is
        return img

    row_min = int(np.argmax(rows))
    row_max = int(len(rows) - 1 - np.argmax(rows[::-1]))
    col_min = int(np.argmax(cols))
    col_max = int(len(cols) - 1 - np.argmax(cols[::-1]))

    h, w = arr.shape[:2]
    left = max(0, col_min - _TRIM_PADDING)
    top = max(0, row_min - _TRIM_PADDING)
    right = min(w, col_max + _TRIM_PADDING + 1)
    bottom = min(h, row_max + _TRIM_PADDING + 1)

    return img.crop((left, top, right, bottom))


# ---------------------------------------------------------------------------
# SSIM helpers
# ---------------------------------------------------------------------------

def _compute_ssim(a: np.ndarray, b: np.ndarray) -> float:
    """SSIM on trimmed RGB float32 arrays (data range 0–255)."""
    try:
        from skimage.metrics import structural_similarity  # type: ignore[import]
    except ImportError:
        return -1.0

    score: float = structural_similarity(
        a.astype(np.uint8),
        b.astype(np.uint8),
        channel_axis=2,
        data_range=255,
    )
    return float(score)


def _compute_edge_ssim(a: np.ndarray, b: np.ndarray) -> float:
    """
    Edge-structure SSIM.

    Converts both images to grayscale, runs Canny edge detection, then
    computes SSIM on the binary edge maps. This captures structural
    similarity (axes, lines, label positions) while ignoring color,
    font rendering, and background differences.
    """
    try:
        from skimage.feature import canny  # type: ignore[import]
        from skimage.metrics import structural_similarity  # type: ignore[import]
    except ImportError:
        return -1.0

    # Convert to grayscale float [0, 1]
    def _to_gray(arr: np.ndarray) -> np.ndarray:
        return (
            0.2989 * arr[:, :, 0]
            + 0.5870 * arr[:, :, 1]
            + 0.1140 * arr[:, :, 2]
        ) / 255.0

    gray_a = _to_gray(a)
    gray_b = _to_gray(b)

    edges_a = canny(gray_a, sigma=1.5).astype(np.float32)
    edges_b = canny(gray_b, sigma=1.5).astype(np.float32)

    score: float = structural_similarity(
        edges_a,
        edges_b,
        data_range=1.0,
    )
    return float(score)


# ---------------------------------------------------------------------------
# Composite image
# ---------------------------------------------------------------------------

_LABEL_HEIGHT = 20
_LABEL_BG = (40, 40, 40)
_LABEL_FG = (220, 220, 220)
_SEPARATOR_W = 4
_SEPARATOR_COLOR = (80, 80, 80)


def _save_composite(
    ref: Image.Image,
    rendered: Image.Image,
    diff: Image.Image,
    out_path: Path,
) -> None:
    """
    Save a horizontal strip: [Reference | Rendered | Diff (×4)]
    with small text labels above each panel.
    """
    panels = [
        (ref, "Reference (matplotlib)"),
        (rendered, "Rendered (TikZ)"),
        (diff, "Diff ×4"),
    ]

    # Normalise all panels to the same height
    target_h = max(p.size[1] for p, _ in panels)
    resized = []
    for p, label in panels:
        if p.size[1] != target_h:
            scale = target_h / p.size[1]
            new_w = max(1, int(p.size[0] * scale))
            p = p.resize((new_w, target_h), Image.LANCZOS)
        resized.append((p, label))

    total_w = (
        sum(p.size[0] for p, _ in resized)
        + _SEPARATOR_W * (len(resized) - 1)
    )
    total_h = target_h + _LABEL_HEIGHT

    composite = Image.new("RGB", (total_w, total_h), (255, 255, 255))
    draw = ImageDraw.Draw(composite)

    x = 0
    for p, label in resized:
        # Label bar
        draw.rectangle([x, 0, x + p.size[0] - 1, _LABEL_HEIGHT - 1], fill=_LABEL_BG)
        draw.text((x + 4, 3), label, fill=_LABEL_FG)
        # Panel
        composite.paste(p, (x, _LABEL_HEIGHT))
        x += p.size[0]
        if x < total_w:
            draw.rectangle([x, 0, x + _SEPARATOR_W - 1, total_h - 1], fill=_SEPARATOR_COLOR)
            x += _SEPARATOR_W

    composite.save(out_path)
