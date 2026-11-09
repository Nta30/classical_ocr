"""Projection-profile line and character segmentation."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class CharacterSegment:
    line_index: int
    character_index: int
    bbox: tuple[int, int, int, int]
    image: np.ndarray
    space_before: bool = False
    uncertain: bool = False


@dataclass
class TextLine:
    index: int
    bbox: tuple[int, int, int, int]
    characters: list[CharacterSegment]


def _runs(active: np.ndarray, tolerated_gap: int = 0) -> list[tuple[int, int]]:
    indexes = np.flatnonzero(active)
    if indexes.size == 0:
        return []
    cuts = np.flatnonzero(np.diff(indexes) > tolerated_gap + 1) + 1
    groups = np.split(indexes, cuts)
    return [(int(group[0]), int(group[-1]) + 1) for group in groups if group.size]


def _merge_same_component_runs(band: np.ndarray, col_runs: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Bridge a one-column projection gap only when ink is one 8-connected object."""
    if len(col_runs) < 2:
        return col_runs
    _, labels = cv2.connectedComponents((band > 0).astype(np.uint8), 8)
    merged: list[tuple[int, int]] = []
    previous_labels: set[int] = set()
    for x0, x1 in col_runs:
        current_labels = set(int(value) for value in np.unique(labels[:, x0:x1]) if value)
        if merged and x0 - merged[-1][1] <= 1 and previous_labels.intersection(current_labels):
            merged[-1] = (merged[-1][0], x1)
            previous_labels.update(current_labels)
        else:
            merged.append((x0, x1))
            previous_labels = current_labels
    return merged


def _merge_detached_mark_bands(mask: np.ndarray, row_runs: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Join a small, aligned dot band with a nearby glyph-body band (i/j)."""
    if len(row_runs) < 2:
        return row_runs
    count, _, stats, centroids = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    parent = list(range(len(row_runs)))

    def root(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(first: int, second: int) -> None:
        a, b = root(first), root(second)
        if a != b:
            parent[b] = a

    component_bands: dict[int, int] = {}
    for label in range(1, count):
        cy = float(centroids[label][1])
        for band_index, (top, bottom) in enumerate(row_runs):
            if top <= cy < bottom:
                component_bands[label] = band_index
                break

    for small in range(1, count):
        if small not in component_bands:
            continue
        sx, sy, sw, sh, sarea = (int(value) for value in stats[small])
        dot_aspect = sw / max(1, sh)
        if not 0.55 <= dot_aspect <= 1.8:
            continue
        best: tuple[int, int] | None = None
        for large in range(1, count):
            if large == small or large not in component_bands:
                continue
            lx, ly, lw, lh, larea = (int(value) for value in stats[large])
            if sh > lh * 0.55 or sarea > larea * 0.45:
                continue
            horizontal_alignment = abs((sx + sw / 2) - (lx + lw / 2)) <= max(2, 0.65 * max(sw, lw))
            vertical_gap = max(ly - (sy + sh), sy - (ly + lh), 0)
            if not horizontal_alignment or vertical_gap > max(4, round(0.35 * lh)):
                continue
            pair = (vertical_gap, large)
            if best is None or pair[0] < best[0]:
                best = pair
        if best is not None:
            union(component_bands[small], component_bands[best[1]])

    groups: dict[int, list[tuple[int, int]]] = {}
    for index, band in enumerate(row_runs):
        groups.setdefault(root(index), []).append(band)
    merged = [(min(top for top, _ in group), max(bottom for _, bottom in group)) for group in groups.values()]
    return sorted(merged)


def _trim_bbox(binary: np.ndarray, x0: int, x1: int, y0: int, y1: int) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(binary[y0:y1, x0:x1])
    if xs.size == 0:
        return None
    left, right = x0 + int(xs.min()), x0 + int(xs.max()) + 1
    top, bottom = y0 + int(ys.min()), y0 + int(ys.max()) + 1
    return left, top, right - left, bottom - top


def _estimate_word_gap_threshold(gaps: list[int], typical_height: float) -> int:
    """Estimate a word-space cutoff from glyph height and the line's gap clusters."""
    threshold = max(3, round(0.40 * typical_height) + 1)
    positive_gaps = sorted(gap for gap in gaps if gap > 0)
    if len(positive_gaps) < 4:
        return threshold

    largest_jump: tuple[float, int, int] | None = None
    for low, high in zip(positive_gaps, positive_gaps[1:]):
        ratio = high / max(1, low)
        if largest_jump is None or ratio > largest_jump[0]:
            largest_jump = ratio, low, high
    if largest_jump is not None:
        ratio, low, high = largest_jump
        if ratio >= 1.30 and high >= threshold:
            threshold = max(threshold, round((low + high) / 2))
    return threshold


def segment_text(binary: np.ndarray, min_character_area: int = 6) -> list[TextLine]:
    """Split foreground=255 text into lines and vertical-projection character runs.

    Projection segmentation naturally keeps a detached i/j dot with its stem
    when both occupy overlapping x columns. Touching glyphs are retained as a
    wide, uncertain segment instead of being silently presented as reliable.
    """
    if binary.ndim != 2 or binary.size == 0:
        raise ValueError("Segmentation expects a non-empty binary image.")
    mask = (binary > 0).astype(np.uint8)
    row_runs = _merge_detached_mark_bands(mask, _runs(mask.sum(axis=1) > 0))
    lines: list[TextLine] = []
    for line_index, (top, bottom) in enumerate(row_runs):
        band = mask[top:bottom]
        # Bridge a narrow gap only when both sides belong to the same connected
        # glyph fragment; adjacent characters remain separate projection runs.
        col_runs = _merge_same_component_runs(band, _runs(band.sum(axis=0) > 0))
        if not col_runs:
            continue
        heights = []
        valid_boxes = []
        for x0, x1 in col_runs:
            box = _trim_bbox(mask, x0, x1, top, bottom)
            if box and box[2] * box[3] >= min_character_area:
                heights.append(box[3])
                valid_boxes.append(box)
        typical_height = float(np.median(heights)) if heights else float(bottom - top)
        line_gaps = [
            current[0] - (previous[0] + previous[2])
            for previous, current in zip(valid_boxes, valid_boxes[1:])
        ]
        word_gap_threshold = _estimate_word_gap_threshold(line_gaps, typical_height)
        characters: list[CharacterSegment] = []
        previous_right: int | None = None
        for x0, x1 in col_runs:
            bbox = _trim_bbox(mask, x0, x1, top, bottom)
            if bbox is None or bbox[2] * bbox[3] < min_character_area:
                continue
            x, y, width, height = bbox
            gap = 0 if previous_right is None else x - previous_right
            wide = width > 1.35 * max(height, typical_height)
            uncertain = bool(wide)
            char = CharacterSegment(
                line_index=line_index,
                character_index=len(characters),
                bbox=bbox,
                image=(mask[y : y + height, x : x + width] * 255),
                space_before=bool(previous_right is not None and gap >= word_gap_threshold),
                uncertain=uncertain,
            )
            characters.append(char)
            previous_right = x + width
        if characters:
            xs = [c.bbox[0] for c in characters]
            rights = [c.bbox[0] + c.bbox[2] for c in characters]
            line_bbox = (min(xs), top, max(rights) - min(xs), bottom - top)
            lines.append(TextLine(index=line_index, bbox=line_bbox, characters=characters))
    return lines


def draw_character_boxes(image: np.ndarray, lines: list[TextLine]) -> np.ndarray:
    """Draw segmented character boxes over a BGR image."""
    overlay = image.copy()
    if overlay.ndim == 2:
        overlay = cv2.cvtColor(overlay, cv2.COLOR_GRAY2BGR)
    for line in lines:
        for segment in line.characters:
            x, y, width, height = segment.bbox
            color = (20, 100, 230) if segment.uncertain else (60, 170, 70)
            cv2.rectangle(overlay, (x, y), (x + width - 1, y + height - 1), color, 1)
    return overlay
