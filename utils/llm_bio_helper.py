import logging
import json
import re
from datetime import datetime
from typing import List

from models.pep_models import ConfidenceValue, Education, LifeStatus
from schemas.pep_response import ConfidenceValueSchema, LifeStatusSchema
from models.llm_schemas import StringList, EducationList, DateOfBirth, StateRegion
from config.prompts import Prompts

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def _infer_gender(name: str, llm_service) -> ConfidenceValueSchema:
    """Return gender as ConfidenceValueSchema."""
    try:
        prompt = Prompts.GENDER_INFERENCE.format(name=name)
        return await llm_service.generate_structured(prompt, ConfidenceValueSchema)
    except Exception as e:
        logger.warning(f"Failed to infer gender for {name}: {e}")
        return ConfidenceValueSchema(value="Unknown", confidence="Low")

def _infer_age(dob: str) -> ConfidenceValueSchema:
    try:
        if dob:
            birth = datetime.strptime(dob, "%Y-%m-%d")
            age_val = (datetime.now() - birth).days // 365
            return ConfidenceValueSchema(value=str(age_val), confidence="High")
        return ConfidenceValueSchema(value="Unknown", confidence="Low")
    except Exception as e:
        logger.warning(f"Failed to calculate age from DOB {dob}: {e}")
        return ConfidenceValueSchema(value="Unknown", confidence="Low")

async def _infer_alive_or_deceased(name: str, llm_service) -> LifeStatusSchema:
    """Return LifeStatusSchema."""
    try:
        prompt = Prompts.LIFE_STATUS_INFERENCE.format(name=name)
        return await llm_service.generate_structured(prompt, LifeStatusSchema)
    except Exception as e:
        logger.warning(f"Failed to infer alive/deceased for {name}: {e}")
        return LifeStatusSchema(status="Unknown", date_of_death="")

async def _infer_aliases(name: str, llm_service) -> List[str]:
    try:
        prompt = Prompts.ALIASES_INFERENCE.format(name=name)
        result = await llm_service.generate_structured(prompt, StringList)
        return result.items
    except Exception as e:
        logger.warning(f"Failed to infer aliases for {name}: {e}")
        return []

async def _infer_dob(name: str, llm_service) -> str:
    """Return date of birth string YYYY-MM-DD or empty string."""
    try:
        prompt = Prompts.DOB_INFERENCE.format(name=name)
        result = await llm_service.generate_structured(prompt, DateOfBirth)
        return result.dob
    except Exception as e:
        logger.warning(f"Failed to infer DOB for {name}: {e}")
        return ""

async def _infer_education(name: str, llm_service) -> List[Education]:
    try:
        prompt = Prompts.EDUCATION_INFERENCE.format(name=name)
        result = await llm_service.generate_structured(prompt, EducationList)
        return result.items
    except Exception as e:
        logger.warning(f"Failed to infer education for {name}: {e}")
        return []

async def _infer_relatives(name: str, llm_service) -> List[str]:
    try:
        prompt = Prompts.RELATIVES_INFERENCE.format(name=name)
        result = await llm_service.generate_structured(prompt, StringList)
        return result.items
    except Exception as e:
        logger.warning(f"Failed to infer relatives for {name}: {e}")
        return []

async def _infer_associates(name: str, llm_service) -> List[str]:
    try:
        prompt = Prompts.ASSOCIATES_INFERENCE.format(name=name)
        result = await llm_service.generate_structured(prompt, StringList)
        return result.items
    except Exception as e:
        logger.warning(f"Failed to infer associates for {name}: {e}")
        return []

async def _infer_state(name: str, llm_service) -> str:
    try:
        prompt = Prompts.STATE_INFERENCE.format(name=name)
        result = await llm_service.generate_structured(prompt, StateRegion)
        return result.state
    except Exception as e:
        logger.warning(f"Failed to infer state for {name}: {e}")
        return ""

async def _infer_notable_achievements(name: str, llm_service) -> list[str]:
    try:
        prompt = Prompts.ACHIEVEMENTS_INFERENCE.format(name=name)
        result = await llm_service.generate_structured(prompt, StringList)
        return result.items
    except Exception:
        return []
