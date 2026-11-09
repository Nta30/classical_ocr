import numpy as np

from classical_ocr.reconstruction import reconstruct_text
from classical_ocr.segmentation import CharacterSegment, TextLine


def test_reconstruction_attaches_punctuation_and_respects_bracket_spacing():
    characters = ["H", "i", ",", "w", "o", "w", "!", "(", "o", "k", ")"]
    spaces_before = [False, False, True, True, False, False, True, True, True, False, True]
    segments = [
        CharacterSegment(0, index, (index * 2, 0, 1, 1), np.ones((1, 1), np.uint8), space_before=space)
        for index, space in enumerate(spaces_before)
    ]
    line = TextLine(0, (0, 0, len(segments) * 2, 1), segments)
    predictions = {(0, index): character for index, character in enumerate(characters)}

    assert reconstruct_text([line], predictions) == "Hi, wow! (ok)"


def test_reconstruction_joins_double_quote_strokes_and_keeps_contraction():
    characters = ["'", "'", "H", "i", "d", "o", "n", "'", "t", "'", "'"]
    spaces_before = [False, False, True, False, True, False, False, False, False, False, False]
    segments = [
        CharacterSegment(
            0,
            index,
            (index * 5, 0, 3, 9),
            np.ones((9, 3), np.uint8),
            space_before=space,
        )
        for index, space in enumerate(spaces_before)
    ]
    line = TextLine(0, (0, 0, len(segments) * 5, 9), segments)
    predictions = {(0, index): character for index, character in enumerate(characters)}

    assert reconstruct_text([line], predictions) == '"Hi don\'t"'
