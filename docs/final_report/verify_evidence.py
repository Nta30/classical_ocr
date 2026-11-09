"""Recompute report evidence without changing existing benchmark files."""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from classical_ocr.evaluation import evaluate_text

def audit(relative, dataset):
    rows = list(csv.DictReader((ROOT / relative).open(encoding='utf-8')))
    grouped = defaultdict(list)
    for row in rows:
        ref = row['ground_truth'].replace('\\n', '\n')
        pred = row['prediction'].replace('\\n', '\n')
        actual = (ROOT / dataset / Path(row['image']).with_suffix('.txt')).read_text(encoding='utf-8')
        assert ref == actual, row['image']
        score = evaluate_text(ref, pred)
        assert score.edit_distance == int(row['edit_distance']), row['image']
        assert len(ref) == int(row['reference_characters'])
        assert abs(score.cer - float(row['cer'])) < 1e-12
        assert score.exact_match == (row['exact_match'] == 'True')
        grouped[row['font']].append(row)
    def summarize(items):
        edits = sum(int(r['edit_distance']) for r in items)
        chars = sum(int(r['reference_characters']) for r in items)
        return dict(images=len(items), edits=edits, reference_characters=chars,
                    cer=edits/chars, character_accuracy=max(0, 1-edits/chars),
                    macro_cer=sum(float(r['cer']) for r in items)/len(items),
                    exact=sum(r['exact_match']=='True' for r in items),
                    archived_mean_seconds=sum(float(r['seconds']) for r in items)/len(items))
    return dict(source=relative, total=summarize(rows), fonts={k:summarize(v) for k,v in grouped.items()})

if __name__ == '__main__':
    results = [audit('evaluation_pixel.csv', 'sample_images/evaluation'),
               audit('sample_images/paragraph_evaluation/evaluation_pixel.csv', 'sample_images/paragraph_evaluation')]
    out = Path(__file__).parent / '_qa'
    out.mkdir(exist_ok=True)
    (out / 'evidence.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(results, ensure_ascii=False, indent=2))
