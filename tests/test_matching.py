import numpy as np
import pytest

from classical_ocr.template_generator import ALPHABET, Template, normalize_glyph
from classical_ocr.recognition import (
    _candidate_projection_splits,
    _merge_adjacent_quote_strokes,
    _split_attached_small_punctuation,
    _prefer_case_by_word_position,
    _prefer_alphanumeric_inside_unpaired_bracket,
    _prefer_i_j_by_baseline,
)
from classical_ocr.segmentation import CharacterSegment, TextLine
from classical_ocr.template_matching import MatchResult, normalized_cross_correlation, pixel_similarity, rank_templates


def test_pixel_similarity_identical_and_complementary():
    a = np.array([[255, 0], [0, 255]], np.uint8)
    assert pixel_similarity(a, a) == 1.0
    assert pixel_similarity(a, 255 - a) == 0.0


def test_ncc_handles_zero_variance_without_dividing_by_zero():
    blank = np.zeros((4, 4), np.uint8)
    full = np.full((4, 4), 255, np.uint8)
    assert normalized_cross_correlation(blank, blank) == 1.0
    assert normalized_cross_correlation(blank, full) == 0.0


def test_matching_rejects_size_mismatch():
    with pytest.raises(ValueError):
        pixel_similarity(np.zeros((2, 2)), np.zeros((3, 2)))


def test_default_template_alphabet_includes_ascii_punctuation():
    assert all(character in ALPHABET for character in ".,;:!?()[]{}-'\"/\\@#$%&*+=_<>`~")


def test_template_ranking_returns_best_label_and_three_classes():
    glyph = np.zeros((24, 18), np.uint8)
    glyph[2:22, 7:11] = 255
    normalized = normalize_glyph(glyph)
    templates = [
        Template("I", "A", "a.ttf", normalized),
        Template("1", "B", "b.ttf", 255 - normalized),
        Template("l", "C", "c.ttf", np.rot90(normalized).copy()),
    ]
    matches = rank_templates(glyph, templates, top_k=3)
    assert len(matches) == 3
    assert matches[0].character == "I"
    assert matches[0].score == 1.0


def test_ambiguous_i_and_lowercase_l_use_word_position_as_tiebreaker():
    image = np.zeros((8, 8), dtype=np.uint8)
    uppercase = MatchResult("I", "font", "font.ttf", 0.99, 0.99, image)
    lowercase = MatchResult("l", "font", "font.ttf", 0.99, 0.99, image)
    matches = [uppercase, lowercase]

    at_word_start = CharacterSegment(0, 3, (0, 0, 2, 8), image, space_before=True)
    inside_word = CharacterSegment(0, 3, (0, 0, 2, 8), image)

    assert _prefer_case_by_word_position(matches, at_word_start).character == "I"
    assert _prefer_case_by_word_position(matches, inside_word).character == "l"


def test_ambiguous_i_and_j_use_baseline_to_identify_descender():
    image = np.zeros((8, 8), dtype=np.uint8)
    lowercase_i = MatchResult("i", "font", "font.ttf", 0.94, 0.94, image)
    lowercase_j = MatchResult("j", "font", "font.ttf", 0.96, 0.96, image)
    matches = [lowercase_j, lowercase_i]
    stem = CharacterSegment(0, 1, (0, 2, 3, 8), image)
    descender = CharacterSegment(0, 1, (0, 3, 3, 10), image)

    assert _prefer_i_j_by_baseline(matches, stem, baseline=10).character == "i"
    assert _prefer_i_j_by_baseline(matches, descender, baseline=10).character == "j"


def test_low_projection_valley_can_split_touching_character_crops():
    image = np.zeros((13, 22), dtype=np.uint8)
    image[0:13, 2:10] = 255
    image[6, 10] = 255  # one-pixel bridge creates a deep vertical-projection valley
    image[0:13, 11:20] = 255
    segment = CharacterSegment(0, 0, (10, 20, 22, 13), image)

    splits = _candidate_projection_splits(segment)

    assert splits
    left, right = splits[0]
    assert left.bbox[0] < right.bbox[0]
    assert left.image.size > 0 and right.image.size > 0
    assert left.uncertain and right.uncertain


def test_detached_comma_at_word_end_splits_from_previous_letter():
    image = np.zeros((20, 15), dtype=np.uint8)
    image[3:16, 2:10] = 255
    image[13:20, 11:15] = 255
    segment = CharacterSegment(0, 4, (100, 200, 15, 20), image, space_before=True)

    split = _split_attached_small_punctuation(segment, typical_height=16, at_word_end=True)

    assert split is not None
    letter, comma = split
    assert letter.bbox == (102, 203, 8, 13)
    assert comma.bbox == (111, 213, 4, 7)
    assert letter.space_before
    assert not comma.space_before
    assert _split_attached_small_punctuation(segment, 16, at_word_end=False) is None


def test_detached_upper_dot_is_not_mistaken_for_word_end_comma():
    image = np.zeros((20, 15), dtype=np.uint8)
    image[4:17, 2:10] = 255
    image[0:3, 5:8] = 255
    segment = CharacterSegment(0, 4, (100, 200, 15, 20), image)

    assert _split_attached_small_punctuation(segment, typical_height=16, at_word_end=True) is None


def test_adjacent_quote_strokes_merge_into_one_segment():
    binary = np.zeros((22, 24), dtype=np.uint8)
    binary[1:10, 1:4] = 255
    binary[1:10, 7:10] = 255
    binary[4:20, 15:19] = 255
    line = TextLine(
        0,
        (1, 1, 18, 19),
        [
            CharacterSegment(0, 0, (1, 1, 3, 9), binary[1:10, 1:4]),
            CharacterSegment(0, 1, (7, 1, 3, 9), binary[1:10, 7:10]),
            CharacterSegment(0, 2, (15, 4, 4, 16), binary[4:20, 15:19]),
        ],
    )

    _merge_adjacent_quote_strokes(line, binary)

    assert len(line.characters) == 2
    assert line.characters[0].bbox == (1, 1, 9, 9)
    assert line.characters[0].image.sum() == 255 * 54


def test_bracket_that_looks_like_a_letter_inside_a_word_uses_letter_candidate():
    image = np.ones((8, 8), dtype=np.uint8)
    bracket = MatchResult("[", "font", "font.ttf", 0.956, 0.956, image)
    lowercase_i = MatchResult("i", "font", "font.ttf", 0.942, 0.942, image)
    letter = MatchResult("t", "font", "font.ttf", 0.941, 0.941, image)
    alternatives = [bracket, lowercase_i, letter]

    assert _prefer_alphanumeric_inside_unpaired_bracket(
        bracket, alternatives, "l", "e", False, False, False
    ).character == "i"
    assert _prefer_alphanumeric_inside_unpaired_bracket(
        bracket, alternatives, "l", "e", False, False, True
    ).character == "["
    assert _prefer_alphanumeric_inside_unpaired_bracket(
        bracket, alternatives, "l", "e", False, False, False, tall_stroke=True
    ).character == "t"
