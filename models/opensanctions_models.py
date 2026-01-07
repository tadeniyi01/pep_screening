# models/opensanctions_models.py

from pydantic import BaseModel
from typing import List, Optional

class OpenSanctionsPosition(BaseModel):
    title: str
    start_date: Optional[str]
    end_date: Optional[str]

class OpenSanctionsEntity(BaseModel):
    name: str
    score: float
    datasets: List[str]
    positions: List[OpenSanctionsPosition]
    topics: List[str]
    entity_id: str
