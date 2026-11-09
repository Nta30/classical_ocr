"""Transparent text metrics for OCR output with explicit ground truth."""

from __future__ import annotations

from dataclasses import dataclass


def levenshtein_distance(reference: str, hypothesis: str) -> int:
    """Compute edit distance in O(min(n,m)) memory."""
    if len(reference) < len(hypothesis):
        reference, hypothesis = hypothesis, reference
    previous = list(range(len(hypothesis) + 1))
    for i, ref_char in enumerate(reference, start=1):
        current = [i]
        for j, hyp_char in enumerate(hypothesis, start=1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (ref_char != hyp_char)))
        previous = current
    return previous[-1]


@dataclass
class Evaluation:
    reference: str
    hypothesis: str
    exact_match: bool
    character_accuracy: float
    cer: float
    edit_distance: int


def evaluate_text(reference: str, hypothesis: str) -> Evaluation:
    distance = levenshtein_distance(reference, hypothesis)
    denominator = max(1, len(reference))
    return Evaluation(
        reference=reference,
        hypothesis=hypothesis,
        exact_match=reference == hypothesis,
        character_accuracy=max(0.0, 1.0 - distance / denominator),
        cer=distance / denominator,
        edit_distance=distance,
    )
