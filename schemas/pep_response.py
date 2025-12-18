# schemas/pep_response.py
from typing import List, Optional
from pydantic import BaseModel, Field


class ConfidenceValueSchema(BaseModel):
    value: str
    confidence: str


class LifeStatusSchema(BaseModel):
    status: str
    date_of_death: str = ""


class AdditionalInformationSchema(BaseModel):
    linkedin_profile: dict = Field(default_factory=dict)
    instagram_profile: dict = Field(default_factory=dict)
    facebook_profile: dict = Field(default_factory=dict)
    twitter_profile: dict = Field(default_factory=dict)
    notable_achievements: List[str] = Field(default_factory=list)


class PEPProfileSchema(BaseModel):
    name: str
    gender: Optional[ConfidenceValueSchema]
    middle_name: str = ""
    aliases: List[str] = Field(default_factory=list)
    other_names: List[str] = Field(default_factory=list)

    is_pep: bool
    pep_level: str
    organisation_or_party: str

    current_positions: List[str] = Field(default_factory=list)
    previous_positions: List[str] = Field(default_factory=list)

    date_of_birth: str = ""
    age: Optional[int]
    education: List[str] = Field(default_factory=list)
    relatives: List[dict] = Field(default_factory=list)
    associates: List[dict] = Field(default_factory=list)
    state: str = ""
    country: str

    reason: List[str] = Field(default_factory=list)

    alive_or_deceased: Optional[LifeStatusSchema]
    pep_association: bool
    basis_for_pep_association: str = ""

    links: List[str] = Field(default_factory=list)
    information_recency: str = ""
    image: List[str] = Field(default_factory=list)

    additional_information: AdditionalInformationSchema
    titles: List[str] = Field(default_factory=list)


class ScreeningResponseSchema(BaseModel):
    pep: PEPProfileSchema
    adverse_media: dict
    audit_trace_id: str
