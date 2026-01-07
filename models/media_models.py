from typing import List, Optional
from pydantic import BaseModel, Field


# ---------- Media Item ----------

class MediaItem(BaseModel):
    # Core metadata
    date: str
    source: str
    headline: str
    excerpt: str

    # Initial provider-level score (0–100)
    score: float = Field(..., ge=0, le=100)

    # Sentiment inference
    inferring: str = Field(..., pattern="^(Negative|Neutral|Positive)$")

    # Classification
    tags: List[str] = Field(default_factory=list)
    language: str = Field(default="en", pattern="^en$")

    # Entity signals
    persons: List[str] = Field(default_factory=list)
    organizations: List[str] = Field(default_factory=list)
    country: str = ""

    # Scoring enrichments
    credibility_score: float = Field(0.0, ge=0, le=1)
    entity_link_confidence: Optional[float] = Field(None, ge=0, le=1)

    # Final computed score (after decay & weighting)
    final_score: Optional[float] = Field(None, ge=0, le=100)
    explanation: Optional[str] = None

    evidence_type: Optional[str] = None


# ---------- Aggregated Result ----------

class AdverseMediaResult(BaseModel):
    query: str

    total: int = Field(..., ge=0)
    media: List[MediaItem] = Field(default_factory=list)

    weighted_score: float = Field(..., ge=0, le=100)
    status: str = Field(
        ...,
        pattern="^(Clear|Medium Risk|Potential High Risk)$"
    )

    reason: List[str] = Field(default_factory=list)
    sar_narrative: str
