"""Command-line utility for building a reusable NPZ template bank."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from classical_ocr.template_generator import available_fonts, generate_templates, save_templates


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="templates/generated/templates.npz")
    parser.add_argument("--font", action="append", default=[], help="Path to an additional .ttf/.otf font; repeatable")
    parser.add_argument("--font-size", action="append", type=int, default=[])
    args = parser.parse_args()
    fonts = available_fonts(args.font)
    sizes = tuple(args.font_size) if args.font_size else (28, 33, 34, 38, 42)
    templates = generate_templates(fonts, font_sizes=sizes)
    save_templates(templates, args.output)
    print(f"Saved {len(templates)} templates from {len(fonts)} installed font(s) to {Path(args.output).resolve()}")
    for name, path in fonts:
        print(f"  {name}: {path}")


if __name__ == "__main__":
    main()
