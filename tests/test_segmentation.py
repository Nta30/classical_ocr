import numpy as np

from classical_ocr.segmentation import segment_text


def test_projection_segmentation_finds_lines_characters_and_spaces():
    image = np.zeros((24, 50), np.uint8)
    image[2:19, 2:7] = 255
    image[2:19, 11:16] = 255
    image[2:19, 28:33] = 255
    image[2:19, 37:42] = 255
    image[22:24, 2:6] = 255
    lines = segment_text(image, min_character_area=6)
    assert [len(line.characters) for line in lines] == [4, 1]
    assert lines[0].characters[2].space_before
    assert lines[1].index == 1


def test_word_gap_threshold_ignores_near_touching_letter_gap():
    image = np.zeros((22, 40), np.uint8)
    image[3:18, 2:5] = 255
    image[3:18, 11:14] = 255  # 6 px gap: kerning within a word
    image[3:18, 26:29] = 255  # 12 px gap: word boundary

    lines = segment_text(image)

    assert len(lines) == 1
    assert [item.space_before for item in lines[0].characters] == [False, False, True]


def test_detached_i_dot_and_stem_are_one_projection_segment():
    image = np.zeros((20, 12), np.uint8)
    image[1:4, 4:7] = 255
    image[7:19, 4:7] = 255
    lines = segment_text(image)
    assert len(lines) == 1
    assert len(lines[0].characters) == 1
    assert lines[0].characters[0].bbox == (4, 1, 3, 18)


def test_blank_image_has_no_segments():
    assert segment_text(np.zeros((10, 10), np.uint8)) == []
