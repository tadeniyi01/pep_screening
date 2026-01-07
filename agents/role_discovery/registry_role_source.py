import json
from pathlib import Path
from models.role_models import DiscoveredRole


class RegistryRoleSource:
    SOURCE_NAME = "Registry"

    NIGERIA_ALIASES = {
        "NG",
        "NGA",
        "NIGERIA",
        "FEDERAL REPUBLIC OF NIGERIA",
        "NAIJA",
        "9JA",
    }

    def __init__(self):
        self.registry_path = Path("data/registries/ng_public_offices.json")

    async def fetch(self, name: str, country: str):
        if not self.registry_path.exists():
            return []

        country_norm = country.strip().upper()

        if country_norm not in self.NIGERIA_ALIASES:
            return []

        name_lower = name.lower()
        roles = []

        with open(self.registry_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        for record in records:
            if record.get("name", "").lower() != name_lower:
                continue

            roles.append(
                DiscoveredRole(
                    title=record["title"],
                    organisation=record["organisation"],
                    country="NG",  # ✅ normalize output
                    start_year=record.get("start_year"),
                    end_year=record.get("end_year"),
                    source=self.SOURCE_NAME,
                    confidence=0.80,
                    raw_reference=json.dumps(record),
                )
            )

        return roles
