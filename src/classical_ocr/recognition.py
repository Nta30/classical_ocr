"""End-to-end classical OCR orchestration and rich per-character diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

import numpy as np
import cv2

from .preprocessing import preprocess_image
from .reconstruction import reconstruct_text
from .segmentation import CharacterSegment, TextLine, segment_text
from .template_generator import Template
from .template_matching import MatchResult, build_template_index, rank_templates


def _split_attached_small_punctuation(
    segment: CharacterSegment,
    typical_height: float,
    at_word_end: bool,
) -> tuple[CharacterSegment, CharacterSegment] | None:
    """Separate a detached comma or period that overlaps the previous letter."""
    if not at_word_end or typical_height <= 0:
        return None
    mask = (segment.image > 0).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    if count < 3:
        return None
    components = sorted(range(1, count), key=lambda label: int(stats[label, cv2.CC_STAT_AREA]), reverse=True)
    main_label = components[0]
    mx, my, mw, mh, main_area = (int(value) for value in stats[main_label])
    if mh < 0.75 * typical_height or main_area < 0.25 * mask.size:
        return None
    for label in components[1:]:
        x, y, width, height, area = (int(value) for value in stats[label])
        body_bottom = my + mh
        mark_bottom = y + height
        if (
            area < 3
            or area > 0.50 * main_area
            or width > 0.55 * typical_height
            or height > 0.65 * typical_height
            or x < mx + mw - 2
            or mark_bottom < body_bottom + 0.05 * typical_height
            or y + height / 2 < body_bottom - 0.15 * typical_height
        ):
            continue
        main_pixels = (labels == main_label).astype(np.uint8) * 255
        mark_pixels = (labels == label).astype(np.uint8) * 255
        sx, sy, sw, sh = segment.bbox
        main_crop = main_pixels[my : my + mh, mx : mx + mw]
        mark_crop = mark_pixels[y : y + height, x : x + width]
        main_segment = CharacterSegment(
            segment.line_index,
            segment.character_index,
            (sx + mx, sy + my, mw, mh),
            main_crop,
            segment.space_before,
            segment.uncertain,
        )
        punctuation_segment = CharacterSegment(
            segment.line_index,
            segment.character_index + 1,
            (sx + x, sy + y, width, height),
            mark_crop,
            False,
            True,
        )
        return main_segment, punctuation_segment
    return None


def _candidate_projection_splits(segment: CharacterSegment) -> list[tuple[CharacterSegment, CharacterSegment]]:
    """Propose cuts around deep or shallow valleys; matching chooses the best cut."""
    glyph = (segment.image > 0).astype(np.uint8)
    height, width = glyph.shape
    if width < 8 or width < 0.65 * height:
        return []
    projection = glyph.sum(axis=0)
    first = max(2, int(round(width * 0.20)))
    last = min(width - 2, int(round(width * 0.80)))
    valley_positions = []
    for cut in range(first, last + 1):
        left_peak = int(projection[:cut].max(initial=0))
        right_peak = int(projection[cut:].max(initial=0))
        local_ink = min(left_peak, right_peak)
        if local_ink and projection[cut] <= max(1, int(round(0.22 * local_ink))):
            valley_positions.append(cut)
    if not valley_positions:
        # Touching glyphs such as ``y,`` may have no empty column because the
        # comma touches a descender. Keep a few low-ink central cuts as options;
        # the recognition stage accepts one only when both halves match well.
        ranked = []
        for cut in range(first, last + 1):
            left_peak = int(projection[:cut].max(initial=0))
            right_peak = int(projection[cut:].max(initial=0))
            local_ink = min(left_peak, right_peak)
            if local_ink and projection[cut] <= max(1, int(round(0.60 * local_ink))):
                ranked.append((int(projection[cut]), cut))
        valley_positions = [cut for _, cut in sorted(ranked)[:5]]
        if not valley_positions:
            return []

    # A T plus a following lowercase letter can have a broad shallow valley:
    # the deepest column may sit inside the T's crossbar. Search a few columns
    # around the qualifying valley so the template scores can select the cut.
    radius = max(1, int(round(width * 0.08)))
    first_candidate = max(first, min(valley_positions) - radius)
    last_candidate = min(last, max(valley_positions) + radius)
    x, y, _, _ = segment.bbox
    splits = []
    for cut in range(first_candidate, last_candidate + 1):
        parts = []
        for offset, crop in ((0, glyph[:, :cut]), (cut, glyph[:, cut:])):
            ys, xs = np.nonzero(crop)
            if xs.size == 0:
                break
            x0, x1 = int(xs.min()), int(xs.max()) + 1
            y0, y1 = int(ys.min()), int(ys.max()) + 1
            tight = (crop[y0:y1, x0:x1] * 255).astype(np.uint8)
            if tight.shape[1] < 2 or int(np.count_nonzero(tight)) < 6:
                break
            parts.append(
                CharacterSegment(
                    line_index=segment.line_index,
                    character_index=0,
                    bbox=(x + offset + x0, y + y0, tight.shape[1], tight.shape[0]),
                    image=tight,
                    space_before=segment.space_before if offset == 0 else False,
                    uncertain=True,
                )
            )
        if len(parts) == 2:
            splits.append((parts[0], parts[1]))
    return splits


def _prefer_case_by_word_position(
    matches: list[MatchResult],
    segment: CharacterSegment,
    prefer_upper: bool | None = None,
    typical_height: float | None = None,
    inside_word: bool = False,
) -> MatchResult:
    """Use word and sentence context to resolve visually similar narrow glyphs."""
    best = matches[0]
    if prefer_upper is None:
        prefer_upper = segment.space_before or segment.character_index == 0

    def close(character: str, margin: float = 0.045) -> MatchResult | None:
        candidate = next((item for item in matches if item.character == character), None)
        return candidate if candidate is not None and best.score - candidate.score <= margin else None

    upper_i = close("I")
    lower_i = [item for item in matches if item.character in {"i", "l"} and best.score - item.score <= 0.045]
    if (
        prefer_upper
        and best.character in {"I", "i", "l", "1", "|", "!", "'", "‘", "’"}
        and upper_i is not None
    ):
        return upper_i

    # In the middle of a word, lowercase letters are much more likely than a
    # capital I, digit 1, or vertical punctuation mark. This also recovers a
    # lowercase ``f`` when its tall stem was ranked as I.
    if inside_word and best.character in {"I", "1", "|", "!"}:
        lowercase_letters = [
            item for item in matches
            if item.character.isalpha() and item.character.islower() and best.score - item.score <= 0.035
        ]
        if lowercase_letters:
            return max(lowercase_letters, key=lambda item: item.score)
    if (
        best.character in {"I", "i", "l", "1", "|", "!"}
        and lower_i
        and (inside_word or not prefer_upper)
    ):
        return max(lower_i, key=lambda item: item.score)

    if best.character.isalpha() and best.character.islower() and len(best.character) == 1 and prefer_upper:
        opposite_case = best.character.upper() if best.character.islower() else best.character.lower()
        case_match = close(opposite_case, 0.025)
        if case_match is not None:
            return case_match

    if prefer_upper and best.character in {"'", "‘", "’", "|", "!"}:
        capital = close("I", 0.045)
        if capital is not None and typical_height and segment.bbox[3] >= 1.10 * typical_height:
            return capital
    return best


def _prefer_letter_over_tall_quote(
    matches: list[MatchResult],
    segment: CharacterSegment,
    inside_word: bool,
    typical_height: float,
    best_match: MatchResult,
) -> MatchResult:
    """Treat a full-height quote-shaped crop inside a word as a narrow letter."""
    if (
        not inside_word
        or best_match.character not in {"'", "‘", "’", "|", "]"}
        or segment.bbox[3] < 0.78 * typical_height
        or segment.bbox[2] > 0.70 * typical_height
    ):
        return best_match
    letters = [
        item for item in matches
        if item.character.isalpha()
        and item.character.islower()
        and best_match.score - item.score <= 0.12
    ]
    if not letters:
        return best_match
    return max(letters, key=lambda item: item.score)


def _prefer_small_punctuation_by_position(
    matches: list[MatchResult],
    segment: CharacterSegment,
    baseline: float | None,
    typical_height: float,
    best_match: MatchResult,
) -> MatchResult:
    """Recover tiny periods and commas from their size and baseline location."""
    if baseline is None or typical_height <= 0:
        return best_match
    x, y, width, height = segment.bbox
    center_y = y + height / 2
    punctuation = {item.character: item for item in matches if item.character in {".", ",", "'", "’"}}
    candidate = None
    if height <= 0.36 * typical_height and width <= 0.55 * typical_height:
        if center_y >= baseline - 0.30 * typical_height:
            candidate = punctuation.get(".")
    elif height <= 0.62 * typical_height and width <= 0.60 * typical_height:
        if y + height >= baseline - 0.08 * typical_height:
            candidate = punctuation.get(",")
        elif center_y < baseline - 0.30 * typical_height:
            candidate = punctuation.get("'") or punctuation.get("’")
    if candidate is not None and best_match.score - candidate.score <= 0.15:
        return candidate
    return best_match


def _prefer_attached_comma_tail(
    best_match: MatchResult,
    segment: CharacterSegment,
    previous_character: str,
    previous_segment: CharacterSegment | None,
    next_segment: CharacterSegment | None,
    baseline: float | None,
    typical_height: float,
) -> MatchResult:
    """Recover a comma whose tail remains connected to the preceding descender."""
    if (
        best_match.character not in {"j", ";", "|", "}"}
        or previous_character not in {"y", "g", "p", "q", "j"}
        or previous_segment is None
        or baseline is None
        or segment.space_before
        or (next_segment is not None and not next_segment.space_before)
    ):
        return best_match
    x, y, width, height = segment.bbox
    previous_right = previous_segment.bbox[0] + previous_segment.bbox[2]
    if (
        width > 0.50 * typical_height
        or height < 1.05 * typical_height
        or x - previous_right > 1
        or y + height < baseline + 0.10 * typical_height
    ):
        return best_match
    return MatchResult(
        ",", best_match.font_name, best_match.font_path,
        best_match.score, best_match.raw_score, best_match.image
    )


def _prefer_period_before_capital(
    matches: list[MatchResult],
    best_match: MatchResult,
    segment: CharacterSegment,
    previous_character: str,
    previous_segment: CharacterSegment | None,
    next_segment: CharacterSegment | None,
    next_matches: list[MatchResult] | None,
    typical_height: float,
) -> MatchResult:
    """Resolve a tiny colon-shaped crop before a new sentence as a period."""
    if (
        best_match.character not in {":", ";"}
        or not previous_character.isalnum()
        or next_segment is None
        or not next_segment.space_before
        or not next_matches
        or not any(item.character.isupper() and item.score >= 0.85 for item in next_matches)
    ):
        return best_match
    period = next((item for item in matches if item.character == "."), None)
    if period is not None and best_match.score - period.score <= 0.20:
        return period
    x, y, width, height = segment.bbox
    if (
        previous_character == "y"
        and previous_segment is not None
        and width <= 0.55 * typical_height
        and height <= 1.10 * typical_height
        and x - (previous_segment.bbox[0] + previous_segment.bbox[2]) <= 1
    ):
        return MatchResult(
            ".", best_match.font_name, best_match.font_path,
            best_match.score, best_match.raw_score, best_match.image
        )
    return best_match


def _prefer_i_j_by_baseline(
    matches: list[MatchResult],
    segment: CharacterSegment,
    baseline: float | None,
    best_match: MatchResult | None = None,
) -> MatchResult:
    """Use line-baseline position to resolve a close i/j shape match."""
    best = best_match or matches[0]
    if baseline is None:
        return best
    candidates = [item for item in matches if best.score - item.score <= 0.10]
    bottom = segment.bbox[1] + segment.bbox[3]
    if best.character in {"1", "I", "l", "|", "!", "]", "}"} and bottom > baseline + 1:
        descender = next((item for item in candidates if item.character == "j"), None)
        if descender is not None:
            return descender
    if best.character not in {"i", "j"} or not {item.character for item in candidates}.issuperset({"i", "j"}):
        return best
    expected = "j" if bottom > baseline + 1 else "i"
    return next(item for item in candidates if item.character == expected)


def _prefer_dash_by_position(
    matches: list[MatchResult],
    segment: CharacterSegment,
    baseline: float | None,
    typical_height: float,
    best_match: MatchResult | None = None,
) -> MatchResult:
    """Use the text baseline and stroke length to distinguish dash from underscore."""
    best = best_match or matches[0]
    x, y, width, height = segment.bbox
    if baseline is None or height > 0.25 * typical_height or width < 1.8 * height:
        return best

    center_y = y + height / 2
    if center_y > baseline + 0.08 * typical_height:
        expected = "_"
    else:
        ratio = width / max(1.0, typical_height)
        expected = "—" if ratio >= 1.15 else "–" if ratio >= 0.60 else "-"
    candidate = next((item for item in matches if item.character == expected), None)
    if candidate is not None and best.score - candidate.score <= 0.08:
        return candidate
    return best


def _prefer_comma_or_quote_by_baseline(
    matches: list[MatchResult],
    segment: CharacterSegment,
    baseline: float | None,
    typical_height: float,
    best_match: MatchResult | None = None,
) -> MatchResult:
    """Distinguish a low comma tail from a high apostrophe/quote mark."""
    best = best_match or matches[0]
    if baseline is None or segment.bbox[3] > 0.65 * typical_height:
        return best
    center_y = segment.bbox[1] + segment.bbox[3] / 2
    comma = next((item for item in matches if item.character == ","), None)
    quotes = [item for item in matches if item.character in {"'", "‘", "’"}]
    if (
        best.character in {"'", "‘", "’"}
        and comma is not None
        and center_y >= baseline - 0.15 * typical_height
        and best.score - comma.score <= 0.08
    ):
        return comma
    if (
        best.character == ","
        and quotes
        and center_y < baseline - 0.35 * typical_height
    ):
        quote = max(quotes, key=lambda item: item.score)
        if best.score - quote.score <= 0.08:
            return quote
    return best


def _prefer_alphanumeric_inside_unpaired_bracket(
    best: MatchResult,
    alternatives: list[MatchResult],
    previous_character: str,
    next_character: str,
    space_before: bool,
    space_after: bool,
    matching_bracket_exists: bool,
    tall_stroke: bool = False,
) -> MatchResult:
    """Undo bracket false positives embedded inside an unbroken word."""
    if best.character not in {"(", ")", "[", "]", "{", "}"} or matching_bracket_exists:
        return best
    previous_attached = previous_character.isalnum() and not space_before
    next_attached = next_character.isalnum() and not space_after
    word_interior = previous_attached and next_attached
    word_start = space_before and next_attached
    word_end = previous_attached and space_after
    if not (word_interior or word_start or word_end):
        return best
    alphanumeric = next((item for item in alternatives if item.character.isalnum()), None)
    if alphanumeric is not None and best.score - alphanumeric.score <= 0.12:
        if tall_stroke:
            tall_candidates = [item for item in alternatives if item.character in "bdfhkltI1"]
            if tall_candidates:
                tall_best = max(tall_candidates, key=lambda item: item.score)
                if alphanumeric.score - tall_best.score <= 0.03:
                    return tall_best
        return alphanumeric
    return best


def _merge_adjacent_quote_strokes(line: TextLine, binary: np.ndarray) -> None:
    """Join the two small, side-by-side strokes used to print a double quote."""
    if len(line.characters) < 2:
        return
    typical_height = max(segment.bbox[3] for segment in line.characters)
    merged: list[CharacterSegment] = []
    index = 0
    while index < len(line.characters):
        left = line.characters[index]
        if index + 1 < len(line.characters):
            right = line.characters[index + 1]
            x1, y1, width1, height1 = left.bbox
            x2, y2, width2, height2 = right.bbox
            horizontal_gap = x2 - (x1 + width1)
            same_height = min(height1, height2) >= 0.75 * max(height1, height2)
            small_marks = (
                max(height1, height2) <= 0.60 * typical_height
                and width1 <= 0.70 * height1
                and width2 <= 0.70 * height2
            )
            aligned = abs(y1 - y2) <= max(1, round(0.15 * max(height1, height2)))
            close = -1 <= horizontal_gap <= max(2, round(0.45 * max(height1, height2)))
            if small_marks and same_height and aligned and close:
                x0, y0 = min(x1, x2), min(y1, y2)
                right_edge = max(x1 + width1, x2 + width2)
                bottom = max(y1 + height1, y2 + height2)
                merged.append(
                    CharacterSegment(
                        line_index=left.line_index,
                        character_index=len(merged),
                        bbox=(x0, y0, right_edge - x0, bottom - y0),
                        image=binary[y0:bottom, x0:right_edge].copy(),
                        space_before=left.space_before,
                        uncertain=left.uncertain or right.uncertain,
                    )
                )
                index += 2
                continue
        merged.append(left)
        index += 1
    line.characters = merged


@dataclass
class OCRCharacter:
    segment: Any
    prediction: str
    best_match: MatchResult
    top_matches: list[MatchResult]


@dataclass
class OCRResult:
    text: str
    steps: dict[str, Any]
    lines: list[TextLine]
    characters: list[OCRCharacter]
    annotated: np.ndarray
    processing_seconds: float


def recognize(
    image: np.ndarray,
    templates: list[Template],
    threshold_method: str = "otsu",
    threshold: int = 150,
    matching_method: str = "pixel",
    median_kernel: int = 1,
    morphology: str = "none",
    min_component_area: int = 30,
    top_k: int = 20,
) -> OCRResult:
    started = perf_counter()
    steps = preprocess_image(image, threshold_method, threshold, median_kernel, morphology, min_component_area)
    lines = segment_text(steps["denoised"])
    template_index = build_template_index(templates) if matching_method.strip().lower() in {"pixel", "pixel similarity"} else None
    characters: list[OCRCharacter] = []
    predictions: dict[tuple[int, int], str] = {}
    line_segment_counts = [len(line.characters) for line in lines]
    median_line_count = float(np.median(line_segment_counts)) if line_segment_counts else 0.0
    for line_position, line in enumerate(lines):
        _merge_adjacent_quote_strokes(line, steps["denoised"])
        line_heights = [segment.bbox[3] for segment in line.characters]
        line_median_height = float(np.median(line_heights)) if line_heights else 1.0
        classified: list[tuple[CharacterSegment, list[MatchResult]]] = []
        source_segments: list[CharacterSegment] = []
        for source_index, segment in enumerate(line.characters):
            at_word_end = (
                source_index + 1 == len(line.characters)
                or line.characters[source_index + 1].space_before
            )
            punctuation_split = _split_attached_small_punctuation(
                segment, line_median_height, at_word_end
            )
            source_segments.extend(punctuation_split or (segment,))
        for segment in source_segments:
            matches = rank_templates(
                segment.image, templates, matching_method, top_k=top_k, template_index=template_index
            )
            is_wide = segment.image.shape[1] >= 1.05 * segment.image.shape[0]
            is_compact_double_quote = (
                matches[0].character in {'"', "“", "”"}
                and segment.image.shape[1] < 1.5 * segment.image.shape[0]
                and segment.bbox[3] <= 0.75 * line_median_height
            )
            tall_quote_merge = (
                matches[0].character in {'"', "“", "”"}
                and segment.image.shape[1] >= 0.70 * segment.image.shape[0]
                and segment.bbox[3] > 0.75 * line_median_height
            )
            narrow_merge_candidate = (
                matches[0].score < 0.94
                and segment.image.shape[1] >= 0.65 * segment.image.shape[0]
            )
            if (
                not is_compact_double_quote
                and (matches[0].score < 0.92 or tall_quote_merge)
                and (is_wide or narrow_merge_candidate)
            ):
                best_split = None
                best_split_score = matches[0].score
                for left, right in _candidate_projection_splits(segment):
                    left_matches = rank_templates(
                        left.image, templates, matching_method, top_k=top_k, template_index=template_index
                    )
                    right_matches = rank_templates(
                        right.image, templates, matching_method, top_k=top_k, template_index=template_index
                    )
                    split_score = (left_matches[0].score + right_matches[0].score) / 2
                    minimum_child_score = 0.95 if not is_wide else 0.72
                    if (
                        min(left_matches[0].score, right_matches[0].score) >= minimum_child_score
                        and split_score > best_split_score
                    ):
                        best_split = (left, left_matches, right, right_matches)
                        best_split_score = split_score
                required_gain = 0.05 if not is_wide else 0.07
                if best_split is not None and best_split_score >= matches[0].score + required_gain:
                    left, left_matches, right, right_matches = best_split
                    classified.extend(((left, left_matches), (right, right_matches)))
                    continue
            classified.append((segment, matches))

        line.characters = []
        baseline_bottoms = [
            segment.bbox[1] + segment.bbox[3]
            for segment, matches in classified
            if matches[0].character.isalnum() and matches[0].character not in {"i", "j"}
        ]
        baseline = float(np.median(baseline_bottoms)) if len(baseline_bottoms) >= 4 else None
        alphanumeric_heights = [
            segment.bbox[3]
            for segment, matches in classified
            if matches[0].character.isalnum()
        ]
        typical_height = float(np.median(alphanumeric_heights)) if alphanumeric_heights else 1.0
        title_line = (
            len(lines) > 1
            and line_position == 0
            and len(classified) <= 0.65 * median_line_count
        )
        previous_line = lines[line_position - 1] if line_position > 0 else None
        previous_line_text_end = next(
            (
                item.prediction
                for item in reversed(characters)
                if previous_line is not None and item.segment.line_index == previous_line.index
            ),
            "",
        )
        previous_is_title = (
            line_position == 1
            and len(lines) > 2
            and len(lines[0].characters) <= 0.65 * median_line_count
        )
        starts_sentence_at_line = (
            line_position == 0 or previous_is_title or previous_line_text_end in ".!?"
        )
        selected: list[MatchResult] = []
        for character_index, (segment, matches) in enumerate(classified):
            segment.character_index = character_index
            previous = classified[character_index - 1] if character_index > 0 else None
            next_item = classified[character_index + 1] if character_index + 1 < len(classified) else None
            inside_word = bool(
                previous
                and not segment.space_before
                and previous[1][0].character.isalpha()
                or next_item
                and not next_item[0].space_before
                and next_item[1][0].character.isalpha()
            )
            previous_character = selected[-1].character if selected else ""
            word_start = segment.space_before or character_index == 0
            prefer_upper = word_start and (
                title_line
                or (character_index == 0 and starts_sentence_at_line)
                or previous_character in {".", "!", "?"}
            )
            best = _prefer_case_by_word_position(matches, segment, prefer_upper, typical_height, inside_word)
            best = _prefer_letter_over_tall_quote(matches, segment, inside_word, typical_height, best)
            best = _prefer_i_j_by_baseline(matches, segment, baseline, best)
            best = _prefer_dash_by_position(matches, segment, baseline, typical_height, best)
            best = _prefer_comma_or_quote_by_baseline(matches, segment, baseline, typical_height, best)
            best = _prefer_small_punctuation_by_position(matches, segment, baseline, typical_height, best)
            best = _prefer_period_before_capital(
                matches,
                best,
                segment,
                previous_character,
                previous[0] if previous else None,
                next_item[0] if next_item else None,
                next_item[1] if next_item else None,
                typical_height,
            )
            best = _prefer_attached_comma_tail(
                best,
                segment,
                previous_character,
                previous[0] if previous else None,
                next_item[0] if next_item else None,
                baseline,
                typical_height,
            )
            selected.append(best)

        bracket_pairs = {"(": ")", "[": "]", "{": "}"}
        for character_index, ((segment, matches), best) in enumerate(zip(classified, selected, strict=True)):
            corrected_matches = matches
            if best.character in {"(", ")", "[", "]", "{", "}"}:
                previous_character = selected[character_index - 1].character if character_index > 0 else ""
                next_character = selected[character_index + 1].character if character_index + 1 < len(selected) else ""
                open_character = best.character if best.character in bracket_pairs else next(
                    (opening for opening, closing in bracket_pairs.items() if closing == best.character), ""
                )
                matching_character = bracket_pairs.get(open_character, "")
                matching_exists = (
                    any(item.character == open_character for item in selected[:character_index])
                    and any(item.character == matching_character for item in selected[character_index + 1:])
                ) or (
                    any(item.character == matching_character for item in selected[:character_index])
                    and any(item.character == open_character for item in selected[character_index + 1:])
                )
                if not matching_exists:
                    alternatives = rank_templates(
                        segment.image, templates, matching_method, top_k=20, template_index=template_index
                    )
                    best = _prefer_alphanumeric_inside_unpaired_bracket(
                        best,
                        alternatives,
                        previous_character,
                        next_character,
                        segment.space_before,
                        classified[character_index + 1][0].space_before if character_index + 1 < len(classified) else True,
                        matching_exists,
                        segment.bbox[3] > 1.10 * typical_height,
                    )
                    corrected_matches = [best, *[item for item in alternatives if item.character != best.character][:2]]
            line.characters.append(segment)
            predictions[(segment.line_index, segment.character_index)] = best.character
            characters.append(OCRCharacter(segment, best.character, best, corrected_matches))
    text = reconstruct_text(lines, predictions)
    # Delayed import avoids a cv2 dependency inside the recognition records.
    from .segmentation import draw_character_boxes

    annotated = draw_character_boxes(steps["original"], lines)
    return OCRResult(text, steps, lines, characters, annotated, perf_counter() - started)
