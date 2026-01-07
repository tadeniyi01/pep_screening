# agents/social_profile_agent.py
from typing import Dict
from services.llm_service import LLMService
from models.llm_schemas import SocialMediaProfiles
from config.prompts import Prompts
import json


class SocialProfileAgent:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    async def resolve(self, name: str, country: str) -> Dict[str, dict]:
        prompt = Prompts.SOCIAL_MEDIA_DISCOVERY.format(name=name, country=country)

        try:
            result = await self.llm.generate_structured(prompt, SocialMediaProfiles)
            return result.model_dump(exclude_none=True)
        except Exception:
            return {
                "linkedin_profile": {},
                "twitter_profile": {},
                "facebook_profile": {},
                "instagram_profile": {}
            }
