from typing import List, Dict
from collections import Counter

IGNORED_TOKENS = {
    "mr", "mrs", "ms", "dr", "prof", "sir", "hon", "h.e.", "his", "excellency"
}


def extract_middle_name(
    subject_name: str,
    sources: List[Dict]
) -> Dict[str, float | str]:
    """
    Extract middle name conservatively from full names in sources.
    """

    candidates = []

    # Normalize subject first/last
    subject_parts = subject_name.lower().split()
    if len(subject_parts) < 2:
        return {"value": "", "confidence": 0.0}

    first = subject_parts[0]
    last = subject_parts[-1]

    for src in sources:
        full_name = src.get("full_name") or src.get("name")
        if not full_name:
            continue

        tokens = [
            t.lower().strip(".")
            for t in full_name.split()
            if t.lower().strip(".") not in IGNORED_TOKENS
        ]

        if len(tokens) < 3:
            continue

        if tokens[0] == first and tokens[-1] == last:
            middle = " ".join(tokens[1:-1])
            candidates.append(middle)

    if not candidates:
        return {"value": "", "confidence": 0.0}

    counts = Counter(candidates)
    most_common, freq = counts.most_common(1)[0]

    confidence = min(0.5 + (freq / len(candidates)), 0.95)

    if confidence < 0.75:
        return {"value": "", "confidence": confidence}

    return {
        "value": most_common.title(),
        "confidence": round(confidence, 2)
    }
