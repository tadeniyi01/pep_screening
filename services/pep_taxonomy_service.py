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
