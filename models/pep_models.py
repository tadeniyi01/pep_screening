from dataclasses import dataclass
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


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
    linkedin_profile: Dict = {}
    instagram_profile: Dict = {}
    facebook_profile: Dict = {}
    twitter_profile: Dict = {}
    notable_achievements: List[str] = []


# ---------- Main PEP Profile ----------

class PEPProfile(BaseModel):
    name: str

    gender: Optional[ConfidenceValue]
    middle_name: str = ""

    aliases: List[str] = []
    other_names: List[str] = []

    is_pep: bool
    pep_level: str

    organisation_or_party: str = ""

    current_positions: List[str] = []
    previous_positions: List[str] = []

    date_of_birth: str = ""
    age: Optional[ConfidenceValue] = None

    education: List[Education] = []

    relatives: List[str] = []
    associates: List[str] = []

    state: str = ""
    country: str

    reason: List[str] = []

    alive_or_deceased: Optional[LifeStatus]

    pep_association: bool = False
    basis_for_pep_association: str = ""

    links: List[str] = []

    information_recency: str = ""

    image: List[ProfileImage] = []

    additional_information: AdditionalInformation

    titles: List[str] = []
