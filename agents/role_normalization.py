import re


class RoleNormalizer:
    """
    Normalizes role titles and organisations into canonical forms.
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

    def normalize_title(self, title: str) -> str:
        t = title.lower()

        for pattern, canonical in self.ROLE_PATTERNS:
            if re.search(pattern, t):
                return canonical

        # fallback: title-case cleaned string
        return title.strip().title()

    def normalize_org(self, org: str) -> str:
        if not org:
            return ""

        key = org.lower().strip()
        return self.ORG_NORMALIZATION.get(key, org.strip())
