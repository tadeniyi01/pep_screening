import json
from pathlib import Path
from models.role_models import DiscoveredRole


class RegistryRoleSource:
    SOURCE_NAME = "Registry"

    def __init__(self):
        self.registry_path = Path(
            "data/registries/ng_public_offices.json"
        )

    def fetch(self, name: str, country: str):
        if country != "NG" or not self.registry_path.exists():
            return []

        name_lower = name.lower()
        roles = []

        with open(self.registry_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        for record in records:
            if record["name"].lower() != name_lower:
                continue

            roles.append(
                DiscoveredRole(
                    title=record["title"],
                    organisation=record["organisation"],
                    country=country,
                    start_year=record.get("start_year"),
                    end_year=record.get("end_year"),
                    source=self.SOURCE_NAME,
                    confidence=0.80,
                    raw_reference=json.dumps(record),  # ✅ FIX
                )
            )

        return roles
