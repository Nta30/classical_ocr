"""Image acquisition, grayscale conversion, binarization, and light cleanup."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np


def load_image(source: str | Path | bytes | bytearray | np.ndarray) -> np.ndarray:
    """Load a PNG/JPEG image as BGR; arrays are copied to avoid caller mutation."""
    if isinstance(source, np.ndarray):
        image = source.copy()
    elif isinstance(source, (bytes, bytearray)):
        image = cv2.imdecode(np.frombuffer(source, dtype=np.uint8), cv2.IMREAD_COLOR)
    else:
        path = Path(source)
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".bmp"}:
            raise ValueError("Supported image formats are PNG, JPG, JPEG, and BMP.")
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None or image.size == 0:
        raise ValueError("The image could not be read or is empty.")
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.ndim != 3 or image.shape[2] not in (3, 4):
        raise ValueError("Expected a grayscale, BGR, or BGRA image.")
    if image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    return np.ascontiguousarray(image.astype(np.uint8, copy=False))


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert BGR to grayscale using OpenCV's 0.114B + 0.587G + 0.299R weights."""
    if image.ndim == 2:
        return image.astype(np.uint8, copy=True)
    if image.ndim != 3 or image.shape[2] not in (3, 4):
        raise ValueError("Expected a grayscale, BGR, or BGRA image.")
    code = cv2.COLOR_BGRA2GRAY if image.shape[2] == 4 else cv2.COLOR_BGR2GRAY
    return cv2.cvtColor(image, code)


def _remove_spellcheck_underlines(image: np.ndarray, gray: np.ndarray) -> np.ndarray:
    """Erase thin, long red spellcheck marks before they join printed glyphs."""
    if image.ndim != 3 or image.shape[2] != 3:
        return gray
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hue, saturation, value = cv2.split(hsv)
    red = (((hue <= 12) | (hue >= 170)) & (saturation >= 65) & (value >= 80)).astype(np.uint8)
    if not np.any(red):
        return gray
    connected = cv2.morphologyEx(
        red, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 1))
    )
    count, labels, stats, _ = cv2.connectedComponentsWithStats(connected, 8)
    erase = np.zeros_like(red)
    minimum_width = max(16, round(image.shape[1] * 0.015))
    for label in range(1, count):
        x, y, width, height, _ = (int(value) for value in stats[label])
        if width >= minimum_width and height <= 10 and width >= 2.5 * max(1, height):
            erase[labels == label] = 255
    if not np.any(erase):
        return gray
    erase = cv2.dilate(erase, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
    return cv2.inpaint(gray, erase, 2, cv2.INPAINT_TELEA)


def _small_punctuation_components(stats: np.ndarray, min_area: int) -> set[int]:
    """Keep compact punctuation near a text baseline while rejecting specks.

    Periods, colon/semicolon dots, and comma tails are often smaller than the
    paper's 30-pixel component cutoff. Their size and position relative to
    nearby full-size glyphs distinguish them from isolated image noise.
    """
    bodies = []
    candidates = []
    for label in range(1, len(stats)):
        x, y, width, height, area = (int(value) for value in stats[label])
        item = (label, x, y, width, height, area)
        if area >= min_area and height >= 6:
            bodies.append(item)
        elif area >= 3:
            candidates.append(item)
    if not bodies or not candidates:
        return set()

    typical_height = float(np.median([item[4] for item in bodies]))
    near_limit = max(3.0, 0.70 * typical_height)

    def near_text(item: tuple[int, int, int, int, int, int]) -> bool:
        _, x, _, width, _, _ = item
        return min(
            max(body[1] - (x + width), x - (body[1] + body[3]), 0)
            for body in bodies
        ) <= near_limit

    plausible = [
        item
        for item in candidates
        if (
            item[3] <= max(3, round(0.40 * typical_height))
            and item[4] <= max(3, round(0.55 * typical_height))
            or item[3] >= 1.8 * item[4]
            and item[4] <= max(2, round(0.25 * typical_height))
        )
        and near_text(item)
    ]
    keep: set[int] = set()
    baseline_marks = []
    for item in plausible:
        label, _, y, _, height, _ = item
        center_y = y + height / 2
        # Estimate the baseline from glyphs in this text row. A single
        # baseline for the whole page drops punctuation on most other lines.
        row_bodies = [
            body for body in bodies
            if body[2] + body[4] >= center_y - 0.65 * typical_height
            and body[2] <= center_y + 0.65 * typical_height
        ]
        if not row_bodies:
            continue
        local_height = float(np.median([body[4] for body in row_bodies]))
        baseline = float(np.median([body[2] + body[4] for body in row_bodies]))
        if baseline - 1.30 * local_height <= center_y <= baseline + 0.45 * local_height:
            keep.add(label)
            if baseline - 0.35 * local_height <= center_y <= baseline + 0.45 * local_height:
                baseline_marks.append(item)
        # Short horizontal strokes sit above the baseline (hyphens/dashes),
        # while underscores sit on or below it and are handled separately.
        width = item[3]
        if (
            width >= 1.8 * height
            and baseline - 0.75 * local_height <= center_y <= baseline - 0.20 * local_height
        ):
            keep.add(label)

    # A colon or semicolon has a second, vertically aligned mark above the
    # baseline mark. Keep the pair together so segmentation sees one glyph.
    for lower in baseline_marks:
        lower_label, lower_x, lower_y, lower_w, lower_h, _ = lower
        lower_center_x = lower_x + lower_w / 2
        lower_center_y = lower_y + lower_h / 2
        for upper in plausible:
            upper_label, upper_x, upper_y, upper_w, upper_h, _ = upper
            if upper_label == lower_label:
                continue
            center_x = upper_x + upper_w / 2
            center_y = upper_y + upper_h / 2
            if (
                abs(center_x - lower_center_x) <= max(2.0, 0.16 * typical_height)
                and 0.25 * typical_height <= lower_center_y - center_y <= 0.90 * typical_height
            ):
                keep.add(upper_label)
    return keep


def binarize(gray: np.ndarray, method: str = "otsu", threshold: int = 150) -> tuple[np.ndarray, float]:
    """Return a binary mask with text=255 and background=0, assuming dark text."""
    if gray.ndim != 2 or gray.size == 0:
        raise ValueError("Binarization expects a non-empty grayscale image.")
    gray = gray.astype(np.uint8, copy=False)
    mode = method.strip().lower()
    if mode == "otsu":
        used, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    elif mode in {"global", "fixed"}:
        used, mask = cv2.threshold(gray, int(np.clip(threshold, 0, 255)), 255, cv2.THRESH_BINARY_INV)
    else:
        raise ValueError("Threshold method must be 'otsu' or 'global'.")
    # Accept common black-on-white and white-on-dark scans while preserving the
    # foreground=white convention used by the rest of the pipeline.
    if np.mean(mask > 0) > 0.5:
        mask = cv2.bitwise_not(mask)
    return mask, float(used)


def remove_small_components(binary: np.ndarray, min_area: int = 30) -> np.ndarray:
    """Remove tiny specks while retaining small dots aligned with a glyph body.

    The 30-pixel value is the paper's stated threshold. A small component can
    still be kept as a likely i/j dot when it is vertically aligned with a
    larger neighboring component. The threshold remains configurable.
    """
    if binary.ndim != 2 or binary.size == 0:
        raise ValueError("Component cleanup expects a non-empty binary image.")
    min_area = max(0, int(min_area))
    count, labels, stats, _ = cv2.connectedComponentsWithStats((binary > 0).astype(np.uint8), 8)
    keep = np.zeros(count, dtype=bool)
    keep[0] = False
    punctuation = _small_punctuation_components(stats, min_area)
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area >= min_area:
            keep[label] = True
            continue
        if label in punctuation:
            keep[label] = True
            continue
        x, y, w, h, _ = (int(v) for v in stats[label])
        # Narrow, tall components can be complete glyphs such as i, l, or 1.
        # Preserve a modest minimum amount of ink even when paper's 30-pixel
        # noise cutoff would otherwise erase these characters.
        if area >= 6 and h >= 6 and h >= 1.8 * w:
            keep[label] = True
            continue
        cx = x + w / 2
        for other in range(1, count):
            if other == label:
                continue
            ox, oy, ow, oh, _ = (int(v) for v in stats[other])
            other_area = int(stats[other, cv2.CC_STAT_AREA])
            if other_area < max(6, area * 1.5) or oh < 6 or oh < 1.5 * ow:
                continue
            ocx = ox + ow / 2
            horizontal_alignment = abs(cx - ocx) <= max(w, ow) * 0.65
            vertical_gap = max(oy - (y + h), y - (oy + oh), 0)
            if horizontal_alignment and vertical_gap <= max(12, 3 * max(h, oh)):
                keep[label] = True
                break
    return (keep[labels].astype(np.uint8) * 255)


def clean_binary(
    binary: np.ndarray,
    median_kernel: int = 1,
    morphology: str = "none",
    min_component_area: int = 30,
) -> np.ndarray:
    """Apply optional median filtering/morphology, then conservative CC cleanup."""
    result = np.where(binary > 0, 255, 0).astype(np.uint8)
    kernel_size = max(1, int(median_kernel))
    if kernel_size % 2 == 0:
        kernel_size += 1
    if kernel_size > 1 and min(result.shape) >= kernel_size:
        result = cv2.medianBlur(result, kernel_size)
    mode = morphology.lower()
    if mode not in {"none", "opening", "closing"}:
        raise ValueError("Morphology must be none, opening, or closing.")
    if mode != "none":
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        operation = cv2.MORPH_OPEN if mode == "opening" else cv2.MORPH_CLOSE
        result = cv2.morphologyEx(result, operation, kernel)
    return remove_small_components(result, min_component_area)


def preprocess_image(
    image: np.ndarray,
    threshold_method: str = "otsu",
    threshold: int = 150,
    median_kernel: int = 1,
    morphology: str = "none",
    min_component_area: int = 30,
) -> dict[str, Any]:
    """Run the image steps and return named intermediates for display/debugging."""
    original = load_image(image)
    gray = _remove_spellcheck_underlines(original, to_grayscale(original))
    binary, threshold_used = binarize(gray, threshold_method, threshold)
    denoised = clean_binary(binary, median_kernel, morphology, min_component_area)
    return {
        "original": original,
        "gray": gray,
        "binary": binary,
        "denoised": denoised,
        "threshold_used": threshold_used,
    }
