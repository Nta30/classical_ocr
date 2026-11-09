"""NumPy implementations of binary pixel similarity and normalized correlation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .template_generator import DEFAULT_SIZE, Template, normalize_glyph


@dataclass
class MatchResult:
    character: str
    font_name: str
    font_path: str
    score: float
    raw_score: float
    image: np.ndarray


@dataclass
class TemplateIndex:
    """Precomputed binary template bank for fast pixel-similarity ranking."""

    source: list[Template]
    binary_images: np.ndarray
    character_indices: dict[str, np.ndarray]


def build_template_index(
    templates: list[Template], size: tuple[int, int] = DEFAULT_SIZE
) -> TemplateIndex:
    """Prepare template masks once instead of converting each sample per glyph."""
    if not templates:
        raise ValueError("The template bank is empty.")
    normalized = [
        item.image if item.image.shape == (size[1], size[0]) else normalize_glyph(item.image, size=size)
        for item in templates
    ]
    masks = np.stack([image > 0 for image in normalized], axis=0)
    grouped: dict[str, list[int]] = {}
    for index, item in enumerate(templates):
        grouped.setdefault(item.character, []).append(index)
    return TemplateIndex(
        source=templates,
        binary_images=masks,
        character_indices={key: np.asarray(value, dtype=np.intp) for key, value in grouped.items()},
    )


def pixel_similarity(image: np.ndarray, template: np.ndarray) -> float:
    """S = 1 - mean(|I-T|) for identically sized binary images in [0,1]."""
    a = np.asarray(image, dtype=np.float64)
    b = np.asarray(template, dtype=np.float64)
    if a.shape != b.shape:
        raise ValueError("Pixel similarity requires arrays with the same dimensions.")
    if a.size == 0:
        raise ValueError("Pixel similarity does not accept empty arrays.")
    a, b = (a > 0).astype(np.float64), (b > 0).astype(np.float64)
    return float(1.0 - np.mean(np.abs(a - b)))


def normalized_cross_correlation(image: np.ndarray, template: np.ndarray) -> float:
    """Compute zero-mean normalized cross-correlation using NumPy only."""
    a = np.asarray(image, dtype=np.float64)
    b = np.asarray(template, dtype=np.float64)
    if a.shape != b.shape:
        raise ValueError("NCC requires arrays with the same dimensions.")
    if a.size == 0:
        raise ValueError("NCC does not accept empty arrays.")
    a, b = (a > 0).astype(np.float64), (b > 0).astype(np.float64)
    a = a - a.mean()
    b = b - b.mean()
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denominator <= np.finfo(np.float64).eps:
        # Two constant masks either match exactly or are completely opposite.
        return 1.0 if np.array_equal(np.asarray(image) > 0, np.asarray(template) > 0) else 0.0
    return float(np.clip(np.sum(a * b) / denominator, -1.0, 1.0))


def score_match(image: np.ndarray, template: np.ndarray, method: str) -> tuple[float, float]:
    mode = method.strip().lower()
    if mode in {"pixel", "pixel similarity"}:
        value = pixel_similarity(image, template)
        return value, value
    if mode in {"ncc", "normalized cross-correlation"}:
        raw = normalized_cross_correlation(image, template)
        return float((raw + 1.0) / 2.0), raw
    raise ValueError("Matching method must be 'pixel' or 'ncc'.")


def rank_templates(
    glyph: np.ndarray,
    templates: list[Template],
    method: str = "pixel",
    top_k: int = 3,
    size: tuple[int, int] = DEFAULT_SIZE,
    template_index: TemplateIndex | None = None,
) -> list[MatchResult]:
    """Normalize one glyph, score every font/character sample, return top-k."""
    if not templates:
        raise ValueError("The template bank is empty.")
    normalized = normalize_glyph(glyph, size=size)
    mode = method.strip().lower()
    if mode in {"pixel", "pixel similarity"}:
        index = template_index
        if index is None or index.source is not templates:
            index = build_template_index(templates, size)
        mask = normalized > 0
        differences = np.count_nonzero(index.binary_images != mask, axis=(1, 2))
        denominator = float(mask.size)
        results = []
        for character, indexes in index.character_indices.items():
            local = differences[indexes]
            best_local = int(np.argmin(local))
            template_index_for_character = int(indexes[best_local])
            template = templates[template_index_for_character]
            score = 1.0 - float(local[best_local]) / denominator
            results.append(
                MatchResult(character, template.font_name, template.font_path, score, score, template.image)
            )
        results.sort(key=lambda item: item.score, reverse=True)
        return results[: max(1, int(top_k))]

    best_by_character: dict[str, MatchResult] = {}
    for template in templates:
        candidate = template.image
        if candidate.shape != normalized.shape:
            candidate = normalize_glyph(candidate, size=size)
        score, raw = score_match(normalized, candidate, method)
        result = MatchResult(template.character, template.font_name, template.font_path, score, raw, candidate)
        current = best_by_character.get(template.character)
        if current is None or result.score > current.score:
            best_by_character[template.character] = result
    results = list(best_by_character.values())
    results.sort(key=lambda item: item.score, reverse=True)
    return results[: max(1, int(top_k))]
