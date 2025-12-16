from typing import List
from pydantic import BaseModel, Field


# ---------- Individual Media Item ----------

class MediaItem(BaseModel):
    date: str
    source: str
    headline: str
    excerpt: str

    score: float = Field(..., ge=0, le=100)
    credibility_score: float = 0.0


    inferring: str = Field(..., pattern="^(Negative|Neutral|Positive)$")

    tags: List[list] = []

    language: str = Field(..., pattern="^en$")

    persons: List[str] = []
    organizations: List[str] = []

    country: str = ""


# ---------- Aggregate Adverse Media ----------

class AdverseMediaResult(BaseModel):
    query: str

    total: int = Field(..., ge=0)

    media: List[MediaItem]

    weighted_score: float = Field(..., ge=0, le=100)

    reason: str

    status: str = Field(
        ...,
        pattern="^(Clear|Medium Risk|Potential High Risk)$"
    )
