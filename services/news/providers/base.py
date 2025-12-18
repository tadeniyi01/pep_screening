from abc import ABC, abstractmethod
from typing import List
from models.media_models import MediaItem


class NewsProvider(ABC):
    """
    Contract every news provider must follow.
    """

    name: str

    @abstractmethod
    def fetch(self, query: str) -> List[MediaItem]:
        pass
