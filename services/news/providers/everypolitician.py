# services/news/providers/everypolitician.py
import csv
import httpx
from datetime import date
from pathlib import Path
from typing import List
from models.media_models import MediaItem
from services.news.base_provider import BaseProvider

CSV_URL = "https://everypolitician.github.io/everypolitician-names/names.csv"
LOCAL_CSV = Path("data/opensanctions_names.csv")


class EveryPoliticianProvider(BaseProvider):
    name = "EveryPolitician"

    def __init__(self):
        super().__init__()

    async def fetch(
        self,
        query: str,
        country: str = "",
        start_date=None,
        end_date=None
    ) -> List[MediaItem]:
        results: List[MediaItem] = []

        reader = None

        # Try remote CSV first
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                resp = await client.get(CSV_URL, headers=headers, timeout=20)
                resp.raise_for_status()
                decoded = resp.content.decode("utf-8").splitlines()
                reader = csv.DictReader(decoded)
        except Exception as e:
            print(f"[EveryPolitician ERROR] Failed to fetch remote CSV: {e}")

        # Fallback to local CSV
        if reader is None:
            if LOCAL_CSV.exists():
                try:
                    with LOCAL_CSV.open("r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                    print(f"[EveryPolitician] Using local CSV fallback: {LOCAL_CSV}")
                except Exception as e:
                    print(f"[EveryPolitician ERROR] Failed to read local CSV: {e}")
                    return []
            else:
                print(f"[EveryPolitician ERROR] Local CSV not found: {LOCAL_CSV}")
                return []

        # Process rows
        for row in reader:
            name = row.get("name", "")
            if query.lower() in name.lower():
                country_code = row.get("country", "")
                legislature = row.get("legislature", "")
                results.append(
                    MediaItem(
                        date=str(date.today()),
                        source=self.name,
                        headline=f"{name} found in EveryPolitician dataset",
                        excerpt=f"{name} is listed in the {legislature} of {country_code}",
                        score=50.0,
                        inferring="Neutral",
                        persons=[name],
                        organizations=[legislature],
                        country=country_code
                    )
                )

        print(f"[EveryPolitician] found {len(results)} items for '{query}'")
        return results
