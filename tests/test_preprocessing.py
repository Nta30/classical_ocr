import numpy as np
import pytest

from classical_ocr.preprocessing import (
    _remove_spellcheck_underlines,
    binarize,
    clean_binary,
    load_image,
    to_grayscale,
)


def test_grayscale_uses_expected_luminance_order():
    bgr = np.array([[[0, 0, 255], [255, 0, 0], [0, 255, 0]]], dtype=np.uint8)
    gray = to_grayscale(bgr)
    assert gray[0, 2] > gray[0, 0] > gray[0, 1]


@pytest.mark.parametrize("method", ["global", "otsu"])
def test_binarize_marks_dark_text_as_foreground(method):
    gray = np.full((20, 30), 255, np.uint8)
    gray[5:15, 10:20] = 0
    binary, _ = binarize(gray, method)
    assert binary[8, 12] == 255
    assert binary[0, 0] == 0


def test_binarize_rejects_unknown_method():
    with pytest.raises(ValueError):
        binarize(np.zeros((2, 2), np.uint8), "adaptive-magic")


def test_cleanup_keeps_a_detached_aligned_dot():
    binary = np.zeros((30, 16), np.uint8)
    binary[13:29, 6:9] = 255
    binary[3:6, 6:9] = 255
    cleaned = clean_binary(binary, median_kernel=1, min_component_area=30)
    assert cleaned[4, 7] == 255
    assert cleaned[20, 7] == 255


def test_cleanup_preserves_period_and_paired_colon_dots_but_removes_speck():
    binary = np.zeros((44, 70), np.uint8)
    binary[8:31, 6:18] = 255
    binary[8:31, 45:57] = 255
    binary[28:31, 20:23] = 255  # period beside the first glyph
    binary[19:21, 25:33] = 255  # hyphen at midline
    binary[18:21, 38:41] = 255  # upper colon dot
    binary[28:31, 38:41] = 255  # lower colon dot
    binary[30, 62] = 255  # isolated noise speck

    cleaned = clean_binary(binary, median_kernel=1, min_component_area=30)

    assert cleaned[29, 21] == 255
    assert cleaned[19, 28] == 255
    assert cleaned[19, 39] == 255
    assert cleaned[29, 39] == 255
    assert cleaned[30, 62] == 0


def test_load_image_rejects_empty_array():
    with pytest.raises(ValueError):
        load_image(np.empty((0, 0, 3), dtype=np.uint8))


def test_red_spellcheck_underline_is_removed_without_erasing_text():
    image = np.full((80, 200, 3), 255, dtype=np.uint8)
    image[20:45, 20:30] = (0, 0, 0)
    image[55, 70:150] = (0, 0, 220)
    gray = to_grayscale(image)

    cleaned = _remove_spellcheck_underlines(image, gray)

    assert cleaned[55, 100] > 220
    assert cleaned[30, 24] < 30
