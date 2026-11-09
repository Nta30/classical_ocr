"""Run OCR against generated samples with ground-truth text and save CSV."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from classical_ocr.evaluation import evaluate_text
from classical_ocr.preprocessing import load_image
from classical_ocr.recognition import recognize
from classical_ocr.template_generator import available_fonts, generate_templates


def evaluate_dataset(
    dataset: Path,
    matching: str = "pixel",
    training_font_names: tuple[str, ...] | None = None,
) -> list[dict[str, object]]:
    manifest = dataset / "manifest.csv"
    if not manifest.exists():
        raise FileNotFoundError(f"Missing {manifest}; run scripts/generate_test_data.py first.")
    installed_fonts = available_fonts()
    by_name = {name.casefold(): (name, path) for name, path in installed_fonts}
    if training_font_names is None:
        # Match the app's broader local template bank for the practical score.
        fonts = installed_fonts
    else:
        missing = [name for name in training_font_names if name.casefold() not in by_name]
        if missing:
            raise ValueError(f"Font(s) not installed: {', '.join(missing)}")
        fonts = [by_name[name.casefold()] for name in training_font_names]
    templates = generate_templates(fonts)
    rows = []
    with manifest.open(newline="", encoding="utf-8") as handle:
        for record in csv.DictReader(handle):
            image_path = dataset / record["image"]
            truth_path = dataset / record["ground_truth"]
            if not image_path.is_file() or not truth_path.is_file():
                raise FileNotFoundError(f"Dataset row is missing a file: {record}")
            image = load_image(image_path)
            result = recognize(image, templates, matching_method=matching)
            truth = truth_path.read_text(encoding="utf-8")
            metric = evaluate_text(truth, result.text)
            expected_count = sum(not character.isspace() for character in truth)
            predicted_count = sum(len(line.characters) for line in result.lines)
            count_accuracy = max(0.0, 1.0 - abs(expected_count - predicted_count) / max(1, expected_count))
            rows.append({
                "image": record["image"],
                "font": record["font"],
                "template_fonts": "; ".join(name for name, _ in fonts),
                "ground_truth": truth.replace("\n", "\\n"),
                "prediction": result.text.replace("\n", "\\n"),
                "exact_match": metric.exact_match,
                "character_accuracy": metric.character_accuracy,
                "cer": metric.cer,
                "edit_distance": metric.edit_distance,
                "reference_characters": len(truth),
                "segment_count_accuracy": count_accuracy,
                "segments": predicted_count,
                "expected_characters": expected_count,
                "seconds": result.processing_seconds,
            })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="sample_images/evaluation")
    parser.add_argument("--matching", choices=["pixel", "ncc"], default="pixel")
    parser.add_argument("--output", default="evaluation_results.csv")
    parser.add_argument("--train-font", action="append", default=None, help="Restrict templates to named font(s), for example repeat with Calibri and Verdana to approximate the paper's bank. Default matches the app and uses every available font.")
    parser.add_argument("--all-training-fonts", action="store_true", help="Use every available font as a template font (same as the default).")
    args = parser.parse_args()
    train_fonts = tuple(name for name, _ in available_fonts()) if args.all_training_fonts else (tuple(args.train_font) if args.train_font else None)
    rows = evaluate_dataset(Path(args.dataset), args.matching, train_fonts)
    if not rows:
        print("No image rows found.")
        return
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    total_edits = sum(int(row["edit_distance"]) for row in rows)
    total_reference_characters = sum(int(row["reference_characters"]) for row in rows)
    weighted_cer = total_edits / max(1, total_reference_characters)
    exact_matches = sum(bool(row["exact_match"]) for row in rows)
    mean_accuracy = sum(float(row["character_accuracy"]) for row in rows) / len(rows)
    mean_cer = sum(float(row["cer"]) for row in rows) / len(rows)
    trained_on = rows[0]["template_fonts"]
    print(f"Template fonts: {trained_on}")
    print(
        f"Images: {len(rows)} | aggregate character accuracy: {1 - weighted_cer:.3f} "
        f"| aggregate CER: {weighted_cer:.3f} | exact match: {exact_matches}/{len(rows)}"
    )
    print(f"Macro-average per image | character accuracy: {mean_accuracy:.3f} | CER: {mean_cer:.3f}")
    print(f"Saved per-image results to {output.resolve()}")
    for row in rows:
        print(f"{row['image']}: CER={float(row['cer']):.3f}, segments={row['segments']}/{row['expected_characters']}")


if __name__ == "__main__":
    main()
