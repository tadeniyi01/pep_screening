from utils.nigeria_pep_taxonomy import NIGERIA_PEP_TAXONOMY


class NigeriaPEPTaxonomyService:
    def classify(self, positions: list):
        for level, data in NIGERIA_PEP_TAXONOMY.items():
            for role in data["roles"]:
                if any(role.lower() in p.lower() for p in positions):
                    return {
                        "pep_level": data["risk"],
                        "matched_role": role
                    }
        return {
            "pep_level": "Not a PEP",
            "matched_role": None
        }

    ROLE_PRIORITY = {
            "President": 100,
            "Head of State": 100,
            "Head of Government": 95,
            "Vice President": 90,
            "Governor": 80,
            "Minister": 75,
            "Judge": 70,
            "Senator": 60,
            "Member of Parliament": 60,
            "MP": 60,
            "SOE Executive": 50,
        }

    def role_priority(self, title: str) -> int:
        """
        Returns the authority rank of a role.
        Unknown roles are treated as low priority.
        """
        if not title:
            return 0

        normalized = title.strip().title()

        return self.ROLE_PRIORITY.get(normalized, 10)