# models/evidence_models.py

from pydantic import BaseModel
from typing import Optional

class Evidence(BaseModel):
    claim_type: str
    claim_value: str
    source: str
    confidence: float
    source_weight: float
    asserted: bool = True
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    retrieved_at: Optional[str] = None
