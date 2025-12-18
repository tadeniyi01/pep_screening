# agents/confidence/attribute_confidence.py
from collections import Counter


SOURCE_WEIGHTS = {
    "registry": 1.0,
    "wikidata": 0.9,
    "news": 0.75,
    "llm": 0.55
}


def score_attribute_confidence(
    attribute: str,
    evidence: list[dict]
) -> float:
    if not evidence:
        return 0.0

    values = [e["value"] for e in evidence]
    sources = [e["source"] for e in evidence]

    value_counts = Counter(values)
    most_common_value, freq = value_counts.most_common(1)[0]

    base = max(
        SOURCE_WEIGHTS.get(s, 0.5)
        for s in sources
    )

    agreement_boost = min(0.2, (freq - 1) * 0.1)
    conflict_penalty = 0.2 if len(value_counts) > 1 else 0.0

    confidence = base + agreement_boost - conflict_penalty

    return round(min(confidence, 0.99), 2)
