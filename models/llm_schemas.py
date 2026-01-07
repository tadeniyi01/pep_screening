from typing import List, Optional
from pydantic import BaseModel, Field
from models.pep_models import Education

# For ReasonSummarizationAgent
class PEPReasoningList(BaseModel):
    reasons: List[str] = Field(
        ..., 
        description="List of concise reasons explaining why the individual is a PEP."
    )

# For SocialProfileAgent
class SocialProfileItem(BaseModel):
    url: str = ""
    verified: bool = False

class SocialMediaProfiles(BaseModel):
    linkedin_profile: Optional[SocialProfileItem] = None
    twitter_profile: Optional[SocialProfileItem] = None
    facebook_profile: Optional[SocialProfileItem] = None
    instagram_profile: Optional[SocialProfileItem] = None

# For Bio Helpers (Generic list of strings)
class StringList(BaseModel):
    items: List[str]

class EducationList(BaseModel):
    items: List[Education]

class DateOfBirth(BaseModel):
    dob: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$|", description="YYYY-MM-DD format or empty string")

class StateRegion(BaseModel):
    state: str

class AdverseClassification(BaseModel):
    sentiment: str = Field(..., pattern="^(Negative|Neutral|Positive)$")
    is_adverse_involvement: bool = Field(..., description="True if the subject is directly involved in or accused of a crime/scandal, False if they are just reporting on it or performing official duties.")
    reasoning: str = Field(..., description="Brief explanation for the classification.")
