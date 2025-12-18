from typing import List, Dict
from collections import Counter
import re
from datetime import datetime


DATE_PATTERNS = [
    r"\b(\d{4}-\d{2}-\d{2})\b",        # 1952-03-29
    r"\b(\d{1,2}\s+[A-Za-z]+\s+\d{4})\b"  # 29 March 1952
]


def extract_date_of_birth(
    subject_name: str,
    sources: List[Dict]
) -> Dict[str, float | str | None]:
    """
    Extract date of birth conservatively from structured sources.
    """

    candidates = []

    for src in sources:
        dob = src.get("date_of_birth") or src.get("dob")
        text = src.get("text", "")

        if dob:
            candidates.append(dob)
            continue

        for pattern in DATE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                candidates.append(match.group(1))

    if not candidates:
        return {"value": None, "confidence": 0.0}

    counts = Counter(candidates)
    most_common, freq = counts.most_common(1)[0]

    confidence = min(0.6 + (freq / len(candidates)), 0.95)

    try:
        # sanity check
        datetime.fromisoformat(most_common.replace(" ", "-"))
    except Exception:
        return {"value": None, "confidence": 0.3}

    return {
        "value": most_common,
        "confidence": round(confidence, 2)
    }
