from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# Simple heuristics mapping
GENDER_KEYWORDS = {
    "male": ["he", "him", "his", "mr", "sir", "president", "king", "prince"],
    "female": ["she", "her", "hers", "mrs", "ms", "queen", "princess", "first lady"],
}

ALLOWED_SOURCES = {
    "wikidata",
    "official_registry",
    "news"
}

def infer_gender_from_sources(name: str, sources: List[Dict]) -> Dict[str, object]:
    """
    Determine likely gender from structured sources.
    Returns:
        {
            "value": "Male" | "Female" | None,
            "confidence": float,
            "sources": list[str]
        }
    """
    gender_votes = []
    contributing_sources = []

    name_lower = name.lower()

    for src in sources:
        text = src.get("text", "") or src.get("summary", "")
        src_type = src.get("source", "unknown").lower()

        if not text or src_type not in ALLOWED_SOURCES:
            continue

        text_lower = text.lower()
        # Check for explicit gender metadata from structured sources
        if src_type == "wikidata":
            # Wikidata may provide P21 (sex or gender)
            gender_val = src.get("gender")
            if gender_val:
                if gender_val.lower() in ["male", "female"]:
                    gender_votes.append(gender_val.capitalize())
                    contributing_sources.append("Wikidata")
                    continue

        # Heuristic text scan
        for g, keywords in GENDER_KEYWORDS.items():
            if any(k in text_lower for k in keywords):
                gender_votes.append(g.capitalize())
                contributing_sources.append(src_type)
                break

    if not gender_votes:
        return {"value": None, "confidence": 0.0, "sources": []}

    # Majority vote
    value_counts = {v: gender_votes.count(v) for v in set(gender_votes)}
    most_likely = max(value_counts, key=value_counts.get)
    confidence = min(0.5 + 0.1 * value_counts[most_likely], 0.95)

    return {
        "value": most_likely,
        "confidence": round(confidence, 2),
        "sources": list(set(contributing_sources))
    }
