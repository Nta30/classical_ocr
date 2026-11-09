"""Create deterministic printed-text images and matching ground-truth files."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from classical_ocr.template_generator import available_fonts


CASES = {
    "single_i": "i",
    "single_j": "j",
    "confusable": "O0 B8 I1 l",
    "word": "Matching",
    "one_line": "Classical OCR 2026",
    "multiple_lines": "Pixel Matching\nUses NumPy 123",
    "noisy_line": "Noise Filter 456",
    "punctuation": "Hello, world! How are you? (Fine.) Don't stop; wait: [test]. \"Good\" and well-known \u2014 yes.",
}
DEMO_TEXT = "ABC DEF 123\nXYZ 789"


def create_image(text: str, font_path: str, font_size: int = 34, noisy: bool = False, seed: int = 7) -> Image.Image:
    font = ImageFont.truetype(font_path, font_size)
    lines = text.splitlines() or [""]
    line_height = font_size + 13
    widths = [ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), line, font=font)[2] for line in lines]
    width = max(widths, default=1) + 32
    height = len(lines) * line_height + 24
    image = Image.new("L", (width, height), color=255)
    draw = ImageDraw.Draw(image)
    for index, line in enumerate(lines):
        draw.text((16, 12 + index * line_height), line, fill=0, font=font)
    if noisy:
        pixels = np.asarray(image).copy()
        rng = np.random.default_rng(seed)
        count = max(1, int(pixels.size * 0.001))
        ys = rng.integers(0, pixels.shape[0], size=count)
        xs = rng.integers(0, pixels.shape[1], size=count)
        pixels[ys, xs] = rng.choice(np.array([0, 255], dtype=np.uint8), size=count)
        image = Image.fromarray(pixels)
    return image.convert("RGB")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="sample_images/evaluation")
    parser.add_argument("--demo-output", default="sample_images/demo_multiline.png")
    parser.add_argument("--fonts", nargs="*", default=[])
    args = parser.parse_args()
    available = available_fonts(args.fonts)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    records = []
    for font_index, (font_name, font_path) in enumerate(available):
        for case_index, (case_name, text) in enumerate(CASES.items()):
            is_noisy = case_name == "noisy_line"
            font_size = 28 + (case_index % 3) * 5
            stem = f"{font_index:02d}_{font_name.lower().replace(' ', '_')}_{case_name}"
            image_path = out / f"{stem}.png"
            create_image(text, font_path, font_size=font_size, noisy=is_noisy, seed=7 + font_index).save(image_path)
            truth_path = out / f"{stem}.txt"
            truth_path.write_text(text, encoding="utf-8")
            records.append(f"{image_path.name},{font_name},{truth_path.name}")
    manifest = out / "manifest.csv"
    manifest.write_text("image,font,ground_truth\n" + "\n".join(records) + "\n", encoding="utf-8")
    demo = Path(args.demo_output)
    demo.parent.mkdir(parents=True, exist_ok=True)
    create_image(DEMO_TEXT, available[0][1], font_size=34, noisy=False).save(demo)
    demo.with_suffix(".txt").write_text(DEMO_TEXT, encoding="utf-8")
    print(f"Created {len(records)} images across {len(available)} fonts in {out.resolve()}")
    print(f"Demo image: {demo.resolve()} (font: {available[0][0]})")


if __name__ == "__main__":
    main()
