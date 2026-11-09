"""Reassemble recognized characters into lines and estimate word spaces."""

from __future__ import annotations

from .segmentation import CharacterSegment, TextLine

NO_SPACE_BEFORE = frozenset(".,;:!?%)]}»”’-")
NO_SPACE_AFTER = frozenset("([{«“‘¡¿-")
QUOTE_MARKS = frozenset("'\"‘’“”")


def reconstruct_text(lines: list[TextLine], predictions: dict[tuple[int, int], str]) -> str:
    output_lines: list[str] = []
    for line in lines:
        parts: list[str] = []
        characters = [
            predictions.get((segment.line_index, segment.character_index), "�")
            for segment in line.characters
        ]
        merged: list[tuple[CharacterSegment, str]] = []
        index = 0
        quote_pairs = {
            ("'", "'"): '"',
            ('"', '"'): '"',
            ("‘", "‘"): "“",
            ("’", "’"): "”",
        }
        while index < len(line.characters):
            segment = line.characters[index]
            character = characters[index]
            if index + 1 < len(line.characters):
                following = line.characters[index + 1]
                pair = (character, characters[index + 1])
                x, y, width, height = segment.bbox
                next_x, next_y, _, next_height = following.bbox
                horizontal_gap = next_x - (x + width)
                vertical_overlap = min(y + height, next_y + next_height) - max(y, next_y)
                if (
                    pair in quote_pairs
                    and not following.space_before
                    and -1 <= horizontal_gap <= max(2, round(0.40 * max(height, next_height)))
                    and vertical_overlap >= 0.60 * min(height, next_height)
                ):
                    merged.append((segment, quote_pairs[pair]))
                    index += 2
                    continue
            merged.append((segment, character))
            index += 1
        previous_character = ""
        previous_opens_quote = False
        for index, (segment, character) in enumerate(merged):
            next_character = merged[index + 1][1] if index + 1 < len(merged) else ""
            opens_quote = character in QUOTE_MARKS and (
                index == 0
                or segment.space_before
                or previous_character in NO_SPACE_AFTER
                or previous_opens_quote
            )
            contraction_apostrophe = (
                character in {"'", "’"}
                and previous_character.isalnum()
                and next_character.isalnum()
            )
            no_space_before = (
                character in NO_SPACE_BEFORE
                or (character in QUOTE_MARKS and not opens_quote)
                or contraction_apostrophe
            )
            no_space_after_previous = (
                previous_character in NO_SPACE_AFTER
                or previous_opens_quote
                or contraction_apostrophe
            )
            if segment.space_before and parts and not no_space_before and not no_space_after_previous:
                parts.append(" ")
            parts.append(character)
            previous_character = character
            previous_opens_quote = opens_quote
        output_lines.append("".join(parts).strip())
    return "\n".join(output_lines)
