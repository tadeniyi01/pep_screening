# models/resolved_claims.py

from pydantic import BaseModel
from typing import List, Optional
from models.evidence_models import Evidence

class ResolvedClaim(BaseModel):
    claim_type: str
    claim_value: str
    confidence: float
    sources: List[str]
    evidences: List[Evidence]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
