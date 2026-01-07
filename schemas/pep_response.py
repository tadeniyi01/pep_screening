# schemas/pep_response.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ============================================================
# COMMON
# ============================================================

class ConfidenceValueSchema(BaseModel):
    value: str = Field(default="Unknown")
    confidence: str = Field(default="Low")


class LifeStatusSchema(BaseModel):
    status: str = Field(default="Unknown")
    date_of_death: str = Field(default="")


class AdditionalInformationSchema(BaseModel):
    linkedin_profile: Dict = Field(default_factory=dict)
    instagram_profile: Dict = Field(default_factory=dict)
    facebook_profile: Dict = Field(default_factory=dict)
    twitter_profile: Dict = Field(default_factory=dict)
    notable_achievements: List[str] = Field(default_factory=list)


# ============================================================
# PEP PROFILE (API VIEW)
# ============================================================

class PEPProfileSchema(BaseModel):
    name: str

    # Identity
    gender: Optional[ConfidenceValueSchema] = None
    middle_name: str = ""
    aliases: List[str] = Field(default_factory=list)
    other_names: List[str] = Field(default_factory=list)

    # PEP status
    is_pep: bool
    pep_level: str
    pep_association: bool = False
    basis_for_pep_association: str = ""

    # Political / organizational
    organisation_or_party: str = ""
    current_positions: List[str] = Field(default_factory=list)
    previous_positions: List[str] = Field(default_factory=list)
    titles: List[str] = Field(default_factory=list)

    # Demographics
    date_of_birth: str = ""
    age: Optional[ConfidenceValueSchema] = None

    # Education & relations
    education: List[Any] = Field(default_factory=list)
    relatives: List[Any] = Field(default_factory=list)
    associates: List[Any] = Field(default_factory=list)

    # Geography
    state: str = ""
    country: str = ""

    # Evidence
    reason: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    information_recency: str = ""

    # Life status
    alive_or_deceased: Optional[LifeStatusSchema] = None

    # Media
    image: List[Any] = Field(default_factory=list)

    # Enrichment
    additional_information: AdditionalInformationSchema = Field(
        default_factory=AdditionalInformationSchema
    )


# ============================================================
# FINAL RESPONSE
# ============================================================

class ScreeningResponseSchema(BaseModel):
    pep: PEPProfileSchema
    adverse_media: Dict
    audit_trace_id: str
