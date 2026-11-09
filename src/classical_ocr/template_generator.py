"""Generate deterministic alphanumeric templates from installed font files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import platform
import string

import numpy as np
from PIL import Image, ImageDraw, ImageFont

PUNCTUATION = string.punctuation + "\u2013\u2014\u2018\u2019\u201c\u201d"
ALPHABET = string.ascii_uppercase + string.ascii_lowercase + string.digits + PUNCTUATION
DEFAULT_SIZE = (48, 48)
FONT_CANDIDATES = {
    "Calibri": ["calibri.ttf", "Calibri.ttf"],
    "Verdana": ["verdana.ttf", "Verdana.ttf"],
    "Arial": ["arial.ttf", "Arial.ttf"],
    "Times New Roman": ["times.ttf", "Times New Roman.ttf", "timesnewroman.ttf"],
    "DejaVu Sans": ["DejaVuSans.ttf"],
}


@dataclass
class Template:
    character: str
    font_name: str
    font_path: str
    image: np.ndarray


def _font_roots() -> list[Path]:
    roots = [Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/dejavu"), Path("/usr/share/fonts/truetype/liberation2")]
    if platform.system() == "Darwin":
        roots.extend([Path("/System/Library/Fonts"), Path("/Library/Fonts")])
    return roots


def available_fonts(custom_paths: list[str] | None = None) -> list[tuple[str, str]]:
    """Return usable font names and paths, preferring requested paper fonts."""
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for name, filenames in FONT_CANDIDATES.items():
        for root in _font_roots():
            for filename in filenames:
                path = root / filename
                if path.is_file() and str(path).lower() not in seen:
                    found.append((name, str(path)))
                    seen.add(str(path).lower())
                    break
            if any(item[0] == name for item in found):
                break
    for index, raw_path in enumerate(custom_paths or []):
        path = Path(raw_path).expanduser()
        if path.is_file() and path.suffix.lower() in {".ttf", ".otf", ".ttc"} and str(path).lower() not in seen:
            found.insert(0, (path.stem or f"Custom {index + 1}", str(path)))
            seen.add(str(path).lower())
    if not found:
        raise FileNotFoundError("No usable TTF/OTF font was found. Install a system font such as DejaVu Sans, Arial, Calibri, or Verdana.")
    return found


def normalize_glyph(glyph: np.ndarray, size: tuple[int, int] = DEFAULT_SIZE, padding: int = 4) -> np.ndarray:
    """Scale a foreground=255 glyph into a centered fixed-size binary canvas."""
    if glyph.ndim != 2 or glyph.size == 0:
        raise ValueError("A glyph must be a non-empty 2D image.")
    # Pillow renders grayscale glyph edges with faint antialiasing pixels.
    # Treating every nonzero edge pixel as ink makes templates heavier than
    # the thresholded input image. Use the same foreground convention as a
    # typical binary scan before scaling the glyph.
    source = np.where(glyph >= 128, 255, 0).astype(np.uint8)
    ys, xs = np.nonzero(source)
    if xs.size == 0:
        return np.zeros((size[1], size[0]), dtype=np.uint8)
    source = source[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    target_w, target_h = int(size[0]), int(size[1])
    inner_w, inner_h = max(1, target_w - 2 * padding), max(1, target_h - 2 * padding)
    scale = min(inner_w / source.shape[1], inner_h / source.shape[0])
    new_w = max(1, min(inner_w, round(source.shape[1] * scale)))
    new_h = max(1, min(inner_h, round(source.shape[0] * scale)))
    resized = np.asarray(Image.fromarray(source).resize((new_w, new_h), Image.Resampling.NEAREST))
    canvas = np.zeros((target_h, target_w), dtype=np.uint8)
    x = (target_w - new_w) // 2
    y = (target_h - new_h) // 2
    canvas[y : y + new_h, x : x + new_w] = resized
    return canvas


def _render_with_font(character: str, font: ImageFont.FreeTypeFont, canvas_size: int = 64) -> np.ndarray:
    canvas = Image.new("L", (canvas_size, canvas_size), color=0)
    draw = ImageDraw.Draw(canvas)
    box = draw.textbbox((0, 0), character, font=font, stroke_width=0)
    width, height = box[2] - box[0], box[3] - box[1]
    x = (canvas_size - width) // 2 - box[0]
    y = (canvas_size - height) // 2 - box[1]
    draw.text((x, y), character, fill=255, font=font)
    return normalize_glyph(np.asarray(canvas))


def render_character(character: str, font_path: str, font_size: int = 36, canvas_size: int = 64) -> np.ndarray:
    """Rasterize one character and crop to its ink bounds before normalization."""
    font = ImageFont.truetype(font_path, size=int(font_size))
    return _render_with_font(character, font, canvas_size)


def generate_templates(
    fonts: list[tuple[str, str]] | None = None,
    characters: str = ALPHABET,
    font_sizes: tuple[int, ...] = (28, 33, 34, 38, 42),
    size: tuple[int, int] = DEFAULT_SIZE,
) -> list[Template]:
    """Build an in-memory template bank; templates are reproducible from fonts."""
    selected_fonts = fonts or available_fonts()
    templates: list[Template] = []
    for font_name, font_path in selected_fonts:
        for font_size in font_sizes:
            # Load each font-size once; repeatedly opening the same font for
            # every character makes the first demo run unnecessarily slow.
            font = ImageFont.truetype(font_path, size=int(font_size))
            for character in characters:
                rendered = _render_with_font(character, font)
                templates.append(Template(character, font_name, font_path, normalize_glyph(rendered, size)))
    if not templates:
        raise ValueError("At least one font and one character are required to create templates.")
    return templates


def save_templates(templates: list[Template], output: str | Path) -> None:
    """Save a compressed, self-describing NPZ template bank."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output,
        characters=np.array([item.character for item in templates]),
        fonts=np.array([item.font_name for item in templates]),
        font_paths=np.array([item.font_path for item in templates]),
        images=np.stack([item.image for item in templates]),
    )


def load_templates(path: str | Path) -> list[Template]:
    data = np.load(path, allow_pickle=False)
    return [Template(str(c), str(f), str(p), image) for c, f, p, image in zip(data["characters"], data["fonts"], data["font_paths"], data["images"], strict=True)]
