"""Generate a deterministic 100-paragraph printed-English OCR dataset."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import random
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from classical_ocr.template_generator import available_fonts


# Each scenario supplies vocabulary for ten complete sentences. The paragraph
# variants are deterministic for a given seed and use only supported ASCII text.
SCENARIOS = [
    ("an old city map", "the library archive", "a folded map", "the east gate", "desk lamp", "route marks", "a torn corner", "trace the safest route", "the river bridge was missing from the oldest copy", "a clean map for the town walk"),
    ("a community garden", "the north courtyard", "a clay pot", "the seed beds", "rain gauge", "daily growth", "a dry patch", "water the young plants", "the first sprouts appeared after five days", "a healthy row of herbs"),
    ("a small music room", "the school hall", "a blue notebook", "the piano bench", "tuning fork", "the sound of each string", "a loose music sheet", "prepare a short concert", "the quiet notes carried farther than expected", "a simple evening performance"),
    ("a local history project", "the town museum", "a glass slide", "the west display", "hand lens", "the age of each photograph", "a missing label", "arrange the family records", "one picture showed the first train station", "a clear story for visitors"),
    ("a river survey", "the stone footbridge", "a sample jar", "the lower bank", "small ruler", "water depth and color", "a muddy trail", "measure the current", "the stream moved more slowly near the bend", "a useful chart for the class"),
    ("a paper airplane test", "the gym entrance", "a yellow plane", "the center line", "tape measure", "the distance of every flight", "a bent wing", "compare three folding styles", "the widest wings traveled farthest", "a fair test for the next lesson"),
    ("a weather journal", "the station window", "a pocket calendar", "the south wall", "glass thermometer", "the morning temperature", "a sudden shower", "track the clouds", "dark clouds arrived before the wind changed", "a full week of weather notes"),
    ("a neighborhood recipe book", "the kitchen table", "a recipe card", "the open shelf", "wooden spoon", "the amount of each ingredient", "a missing page", "collect the family dishes", "the oldest soup used only four vegetables", "a warm meal for the whole group"),
    ("a bicycle repair lesson", "the workshop door", "a silver wrench", "the front wheel", "small pump", "tire pressure and wheel speed", "a loose bolt", "check each safety part", "the chain ran smoothly after one careful adjustment", "a safer ride around the park"),
    ("a bird watching walk", "the lake path", "a field guide", "the wooden bench", "binoculars", "feather colors and calls", "a noisy flock", "identify the birds", "a bright blue jay rested beside the reeds", "a quiet hour outdoors"),
    ("a school science fair", "the east classroom", "a project card", "the tall window", "glass jar", "the time each seed needed", "a cracked lid", "show the results clearly", "warm light helped the beans grow faster", "a neat display for the judges"),
    ("a lighthouse model", "the craft room", "a cardboard tower", "the work table", "small flashlight", "the beam angle", "a short wire", "build a steady light", "the narrow beam reached the far wall", "a strong model for the exhibit"),
    ("a book club meeting", "the reading room", "a green bookmark", "the wide sofa", "paper calendar", "the favorite chapter", "a late delivery", "choose a story for next week", "every reader noticed a different clue", "another lively discussion"),
    ("a park clean up", "the west entrance", "a pair of gloves", "the picnic area", "large basket", "the number of cans and bottles", "a windy morning", "sort the recycling", "the path looked bright and tidy by noon", "a safer place for families"),
    ("a bridge building challenge", "the design lab", "a wooden block", "the test table", "hanging weight", "the strength of each joint", "a weak corner", "support the longest span", "a wide base held more weight than a tall frame", "a sturdy bridge design"),
    ("a family photo album", "the upstairs room", "a black frame", "the round table", "soft cloth", "the dates on the pictures", "a faded caption", "sort the pictures by year", "the youngest cousin had the oldest photograph", "a bright new album"),
    ("a solar oven test", "the sunny porch", "a foil tray", "the brick step", "kitchen timer", "the heat inside the box", "a passing cloud", "keep the food warm", "dark paper absorbed more light than white paper", "a simple outdoor lunch"),
    ("a small robotics project", "the computer lab", "a plastic wheel", "the center mat", "spare battery", "the robot path", "a stuck sensor", "guide the machine around the cones", "the robot turned faster after its wheels were aligned", "a smooth final run"),
    ("a market day plan", "the village square", "a price list", "the front counter", "pocket scale", "the weight of each basket", "a missing sign", "set up the fruit stand", "fresh apples sold best before the rain", "a busy and friendly market"),
    ("a night sky journal", "the hilltop shelter", "a star chart", "the south window", "small compass", "the position of each bright star", "a thin cloud", "find the northern star", "the moon appeared above the quiet ridge", "a clear page of observations"),
]

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
LEADS = ["Maya and Luis", "Nora's class", "the young crew", "a local team", "four curious students", "Eli and his sister", "the science club", "Jamal's neighbors", "two patient builders", "the art group"]
WEATHER = ["cool", "bright", "misty", "warm", "windy", "clear", "cloudy", "fresh", "still", "sunny"]
MOODS = ["calm", "patient", "hopeful", "cheerful", "focused", "careful", "curious", "steady", "ready", "positive"]
EVENTS = ["the lights flickered", "a cart rolled by", "the bell rang", "the rain began", "a door opened", "the wind grew stronger", "the clouds moved away", "a phone rang", "the sun came out", "a dog barked nearby"]
ACTIONS = ["check every detail", "finish the first draft", "share the work with others", "keep the notes in order", "solve the small problem", "make the next step easier", "save time for review", "explain the result", "complete the careful test", "prepare a useful display"]
PROBLEMS = ["a loose screw", "a missing label", "a short delay", "a heavy box", "a smudged note", "a narrow path", "a dull pencil", "a faulty switch", "a noisy room", "a wet patch"]


def build_paragraphs(count: int, seed: int) -> list[list[str]]:
    rng = random.Random(seed)
    paragraphs: list[list[str]] = []
    for index in range(count):
        topic, place, item, landmark, tool, measure, problem, action, finding, project = SCENARIOS[index % len(SCENARIOS)]
        lead = LEADS[index % len(LEADS)]
        day = DAYS[(index + seed) % len(DAYS)]
        weather = WEATHER[(index * 3 + seed) % len(WEATHER)]
        mood = MOODS[(index * 7 + seed) % len(MOODS)]
        event = EVENTS[(index * 5 + seed) % len(EVENTS)]
        problem = PROBLEMS[(index * 9 + seed) % len(PROBLEMS)] if index % 2 else problem
        action = ACTIONS[(index * 11 + seed) % len(ACTIONS)] if index % 3 else action
        detail = rng.choice(["short", "careful", "simple", "clear", "useful", "bright", "steady", "fresh"])
        sentences = [
            f"On {day}, {lead} visited {place} to study {topic}.",
            f"It was a {weather} morning, and the group felt {mood}.",
            f"{lead} set {item} beside {landmark} before the first task began.",
            f"A {detail} note explained how the group would {action}.",
            f"When {event}, everyone paused and checked the {tool} again.",
            f"They used the {tool} to record {measure} and compare each result.",
            f"The group noticed {problem}, so they adjusted the plan and continued.",
            f"After lunch, {lead} asked whether the new plan could {ACTIONS[(index + seed) % len(ACTIONS)]}.",
            f"The answer was clear: {finding}.",
            f"By evening, the group had finished {project}, and the next step seemed possible.",
        ]
        paragraphs.append(sentences)
    return paragraphs


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    scratch = Image.new("L", (1, 1), color=255)
    draw = ImageDraw.Draw(scratch)
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and draw.textbbox((0, 0), candidate, font=font)[2] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def render_text(text: str, font_path: str, font_size: int, max_width: int) -> tuple[Image.Image, str]:
    font = ImageFont.truetype(font_path, font_size)
    lines = wrap_text(text, font, max_width)
    line_height = font_size + 13
    scratch = Image.new("L", (1, 1), color=255)
    measure = ImageDraw.Draw(scratch)
    width = max(measure.textbbox((0, 0), line, font=font)[2] for line in lines) + 32
    image = Image.new("L", (width, len(lines) * line_height + 24), color=255)
    draw = ImageDraw.Draw(image)
    for index, line in enumerate(lines):
        draw.text((16, 12 + index * line_height), line, fill=0, font=font)
    return image.convert("RGB"), "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="sample_images/paragraph_evaluation")
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20261110)
    parser.add_argument("--font-size", type=int, default=28)
    parser.add_argument("--wrap-width", type=int, default=1100, help="Maximum rendered line width in pixels.")
    parser.add_argument("--fonts", nargs="*", default=[])
    args = parser.parse_args()
    if args.count <= 0:
        parser.error("--count must be greater than zero")
    if args.wrap_width <= 0 or args.font_size <= 0:
        parser.error("--wrap-width and --font-size must be greater than zero")

    fonts = available_fonts(args.fonts)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    paragraphs = build_paragraphs(args.count, args.seed)
    for index, sentences in enumerate(paragraphs, start=1):
        font_name, font_path = fonts[(index - 1) % len(fonts)]
        raw_text = " ".join(sentences)
        image, wrapped_text = render_text(raw_text, font_path, args.font_size, args.wrap_width)
        stem = f"paragraph_{index:03d}"
        image_name = f"{stem}.png"
        truth_name = f"{stem}.txt"
        image.save(out / image_name)
        (out / truth_name).write_text(wrapped_text, encoding="utf-8")
        records.append({
            "image": image_name,
            "font": font_name,
            "ground_truth": truth_name,
            "paragraph_index": index,
            "sentence_count": len(sentences),
            "character_count": len(wrapped_text),
            "font_size": args.font_size,
            "wrap_width": args.wrap_width,
            "seed": args.seed,
        })

    fields = ["image", "font", "ground_truth", "paragraph_index", "sentence_count", "character_count", "font_size", "wrap_width", "seed"]
    with (out / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    (out / "README.txt").write_text(
        "Synthetic printed-English paragraph OCR dataset.\n"
        f"Paragraphs: {args.count}; sentences per paragraph: 10; seed: {args.seed}.\n"
        "Each PNG has a matching TXT ground truth file. Text uses ASCII English because this OCR project does not recognize Vietnamese diacritics.\n"
        "The ground truth keeps the same visual line wraps as its PNG so the evaluator can compare line breaks too.\n",
        encoding="utf-8",
    )
    print(f"Created {len(records)} paragraphs, {len(records)} images, and {len(records)} ground-truth files in {out.resolve()}")
    print(f"Fonts used: {', '.join(dict.fromkeys(str(row['font']) for row in records))}")
    print(f"Manifest: {(out / 'manifest.csv').resolve()}")


if __name__ == "__main__":
    main()
