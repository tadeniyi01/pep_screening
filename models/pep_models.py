from dataclasses import dataclass
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


# ---------- Non-Pydantic Domain Result ----------

@dataclass
class EntityLinkResult:
    confidence: float
    signals: List[str]


# ---------- Common ----------

class ConfidenceValue(BaseModel):
    value: str
    confidence: str = Field(..., pattern="^(High|Medium|Low)$")


# ---------- Education ----------

class Education(BaseModel):
    degree: str
    certification: str
    institution: str
    graduation_date: str
    source: str


# ---------- Life Status ----------

class LifeStatus(BaseModel):
    status: str = Field(..., pattern="^(Alive|Deceased|Unknown)$")
    date_of_death: str = ""


# ---------- Image ----------

class ImageSource(BaseModel):
    link: str
    name: str


class ProfileImage(BaseModel):
    url: str
    confidence: str = Field(..., pattern="^(High|Medium|Low)$")
    description: str
    source: ImageSource


# ---------- Additional Information ----------

class AdditionalInformation(BaseModel):
    linkedin_profile: Dict = Field(default_factory=dict)
    instagram_profile: Dict = Field(default_factory=dict)
    facebook_profile: Dict = Field(default_factory=dict)
    twitter_profile: Dict = Field(default_factory=dict)
    notable_achievements: List[str] = Field(default_factory=list)


# ---------- Main PEP Profile ----------

class PEPProfile(BaseModel):
    name: str

    gender: Optional[ConfidenceValue] = None
    middle_name: str = ""

    aliases: List[str] = Field(default_factory=list)
    other_names: List[str] = Field(default_factory=list)

    is_pep: bool
    pep_level: str

    organisation_or_party: str = ""

    current_positions: List[str] = Field(default_factory=list)
    previous_positions: List[str] = Field(default_factory=list)

    date_of_birth: str = ""
    age: Optional[ConfidenceValue] = None

    education: List[Education] = Field(default_factory=list)

    relatives: List[str] = Field(default_factory=list)
    associates: List[str] = Field(default_factory=list)

    state: str = ""
    country: str

    reason: List[str] = Field(default_factory=list)

    alive_or_deceased: Optional[LifeStatus] = None

    pep_association: bool = False
    basis_for_pep_association: str = ""

    links: List[str] = Field(default_factory=list)

    information_recency: str = ""

    image: List[ProfileImage] = Field(default_factory=list)

    additional_information: AdditionalInformation = Field(
        default_factory=AdditionalInformation
    )

    titles: List[str] = Field(default_factory=list)
