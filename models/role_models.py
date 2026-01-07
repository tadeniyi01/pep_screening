# models/role_models.py UNIFIED ROLE MODEL
from pydantic import BaseModel, Field
from typing import Optional


class DiscoveredRole(BaseModel):
    title: str
    organisation: str
    country: str

    start_year: Optional[int] = None
    end_year: Optional[int] = None

    source: str = Field(
        ..., description="wikidata | registry | news | llm"
    )

    source_detail: Optional[str] = None

    confidence: float = Field(
        ..., ge=0.0, le=1.0
    )

    raw_reference: Optional[str] = Field(
        None, description="URL, SPARQL ID, or document reference"
    )
