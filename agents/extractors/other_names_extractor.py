# agents/extractors/other_names_extractor.py

from typing import List, Dict

from agents.confidence.attribute_confidence import score_attribute_confidence


def extract_other_names(
    subject_name: str,
    sources: List[Dict]
) -> Dict[str, object]:
    """
    Extract legitimate name variants (initials, reordered names).
    No aliases, no nicknames, no inference from text.
    """

    variants = []
    evidence = []

    parts = subject_name.split()

    if len(parts) >= 2:
        # Initials form: B. A. Tinubu
        initials = " ".join(p[0] + "." for p in parts[:-1]) + " " + parts[-1]
        variants.append(initials)

        # Reversed form: Tinubu Bola Ahmed
        reversed_name = f"{parts[-1]} {' '.join(parts[:-1])}"
        variants.append(reversed_name)

    # Normalize and remove self
    unique = {
        v for v in variants
        if v.lower() != subject_name.lower()
    }

    if not unique:
        return {
            "value": [],
            "confidence": 0.0
        }

    results = []
    for name in unique:
        results.append({
            "name": name,
            "source": "name-variant"
        })

        evidence.append({
            "value": name,
            "source": "name-variant"
        })

    # Conservative confidence for synthetic variants
    confidence = score_attribute_confidence(
        attribute="other_names",
        evidence=evidence
    )

    return {
        "value": results if confidence >= 0.7 else [],
        "confidence": round(confidence, 2)
    }
