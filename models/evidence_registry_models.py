# models/evidence_registry_models.py

from pydantic import BaseModel
from typing import List
from models.resolved_claims import ResolvedClaim

class EvidenceRegistryResult(BaseModel):
    resolved_claims: List[ResolvedClaim]
