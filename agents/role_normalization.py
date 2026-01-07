# agents/role_normalization.py
import re
from typing import Dict, Any, List


class RoleNormalizer:
    """
    Normalizes role titles, organisations, and supporting evidence
    into canonical, extractor-friendly forms.

    Deterministic, explainable, auditable.
    """

    ROLE_PATTERNS = [
        (r"\bpresident\b", "President"),
        (r"\bvice president\b", "Vice President"),
        (r"\bgovernor\b", "Governor"),
        (r"\bdeputy governor\b", "Deputy Governor"),
        (r"\bsenator\b", "Senator"),
        (r"\bminister\b", "Minister"),
        (r"\bcommissioner\b", "Commissioner"),
    ]

    ORG_NORMALIZATION = {
        "federal republic of nigeria": "Federal Republic of Nigeria",
        "federal government of nigeria": "Federal Republic of Nigeria",
        "lagos state government": "Lagos State Government",
    }

    # -----------------------------
    # ROLE NORMALIZATION
    # -----------------------------
    def normalize_title(self, title: str) -> str:
        if not title:
            return ""

        t = title.lower()
        for pattern, canonical in self.ROLE_PATTERNS:
            if re.search(pattern, t):
                return canonical

        return title.strip().title()

    def normalize_org(self, org: str) -> str:
        if not org:
            return ""

        key = org.lower().strip()
        return self.ORG_NORMALIZATION.get(key, org.strip())

    # -----------------------------
    # EVIDENCE NORMALIZATION
    # -----------------------------
    def normalize_evidence(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts raw Wikidata / News evidence into a canonical format
        expected by BiographicEnrichmentAgent extractors.
        """

        text_parts: List[str] = []

        dob = raw.get("date_of_birth")
        state = raw.get("state")
        aliases = raw.get("aliases", [])
        images = raw.get("image", [])

        if dob:
            text_parts.append(f"Born on {dob}.")

        if state:
            text_parts.append(f"Born in {state}.")

        for alias in aliases:
            text_parts.append(f"Also known as {alias}.")

        # News articles already come with text
        if raw.get("text"):
            text_parts.append(raw["text"])

        return {
            "source": raw.get("source", "unknown"),
            "text": " ".join(text_parts).strip(),
            "date_of_birth": dob,
            "state": state,
            "aliases": aliases,
            "image": images,
            "confidence": raw.get("confidence", 0.6),
        }
