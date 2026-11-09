import pytest

from classical_ocr.evaluation import evaluate_text, levenshtein_distance
from classical_ocr.reconstruction import reconstruct_text
from classical_ocr.segmentation import CharacterSegment, TextLine


def test_reconstruction_restores_word_and_line_breaks():
    line0 = TextLine(0, (0, 0, 22, 10), [
        CharacterSegment(0, 0, (0, 0, 4, 10), None),
        CharacterSegment(0, 1, (6, 0, 4, 10), None),
        CharacterSegment(0, 2, (18, 0, 4, 10), None, space_before=True),
    ])
    line1 = TextLine(1, (0, 20, 4, 10), [CharacterSegment(1, 0, (0, 20, 4, 10), None)])
    assert reconstruct_text([line0, line1], {(0, 0): "H", (0, 1): "i", (0, 2): "1", (1, 0): "A"}) == "Hi 1\nA"


def test_cer_and_accuracy_use_edit_distance():
    result = evaluate_text("book", "back")
    assert not result.exact_match
    assert result.edit_distance == 2
    assert result.cer == 0.5
    assert result.character_accuracy == 0.5


@pytest.mark.parametrize(("reference", "hypothesis", "distance"), [("", "", 0), ("abc", "abc", 0), ("abc", "ac", 1), ("", "xy", 2)])
def test_levenshtein_distance(reference, hypothesis, distance):
    assert levenshtein_distance(reference, hypothesis) == distance
