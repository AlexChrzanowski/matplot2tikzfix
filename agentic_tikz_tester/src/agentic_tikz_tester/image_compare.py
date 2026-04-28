"""
image_compare.py — pixel-level comparison of reference PNG vs TikZ-rendered PNG.

Computes RMS pixel difference and SSIM.
Saves an amplified diff image.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


@dataclass
class CompareResult:
    rms: float
    ssim: float
    max_diff: float
    size_mismatch: bool
    passed: bool
    ref_size: tuple[int, int]
    rendered_size: tuple[int, int]


def compare_images(
    ref_path: Path,
    rendered_path: Path,
    diff_path: Path,
    threshold_rms: float,
    threshold_ssim: float,
) -> CompareResult:
    """
    Load both images, compare them, and write a diff PNG.

    If sizes differ, the rendered image is resized to match the reference
    using LANCZOS resampling (recorded via size_mismatch=True).

    Returns a CompareResult with pass/fail verdict.
    """
    ref_img = Image.open(ref_path).convert("RGB")
    rendered_img = Image.open(rendered_path).convert("RGB")

    ref_size = ref_img.size       # (width, height)
    rendered_size = rendered_img.size

    size_mismatch = ref_size != rendered_size
    if size_mismatch:
        rendered_img = rendered_img.resize(ref_size, Image.LANCZOS)

    ref_arr = np.asarray(ref_img, dtype=np.float32)
    rendered_arr = np.asarray(rendered_img, dtype=np.float32)

    diff_arr = np.abs(ref_arr - rendered_arr)

    rms = float(np.sqrt(np.mean(diff_arr ** 2)))
    max_diff = float(diff_arr.max())

    ssim = _compute_ssim(ref_arr, rendered_arr)

    # Save amplified diff image
    diff_amplified = np.clip(diff_arr * 4, 0, 255).astype(np.uint8)
    Image.fromarray(diff_amplified).save(diff_path)

    passed = rms <= threshold_rms and ssim >= threshold_ssim

    return CompareResult(
        rms=rms,
        ssim=ssim,
        max_diff=max_diff,
        size_mismatch=size_mismatch,
        passed=passed,
        ref_size=ref_size,
        rendered_size=rendered_size,
    )


def _compute_ssim(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute structural similarity index (SSIM) between two RGB uint8-range arrays.
    """
    try:
        from skimage.metrics import structural_similarity  # type: ignore[import]
    except ImportError:
        # Graceful degradation: return 0.0 so the test fails with a clear status
        return 0.0

    score: float = structural_similarity(
        a.astype(np.uint8),
        b.astype(np.uint8),
        channel_axis=2,
        data_range=255,
    )
    return float(score)
