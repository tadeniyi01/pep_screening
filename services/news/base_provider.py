from abc import ABC, abstractmethod
from typing import List, Optional
from models.media_models import MediaItem


class BaseProvider(ABC):
    """
    Base class for all evidence providers.
    """

    # REQUIRED METADATA
    name: str
    evidence_type: str  # "adverse_media" | "structured_pep"
    default_credibility: float  # 0.0 – 1.0

    @abstractmethod
    async def fetch(
        self,
        query: str,
        country: str = "",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[MediaItem]:
        pass
