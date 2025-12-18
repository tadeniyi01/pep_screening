# agents/social_profile_agent.py
from typing import Dict
from services.llm_service import LLMService
import json


class SocialProfileAgent:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    def resolve(self, name: str, country: str) -> Dict[str, dict]:
        prompt = f"""
You are a compliance intelligence system.

Task:
Identify publicly known and widely referenced social media profiles
belonging to the political figure below.

Rules:
- Only include profiles that are commonly cited by reputable sources
- Do NOT guess or fabricate
- If unsure, return an empty object for that platform
- Return strict JSON only

Entity:
Name: {name}
Country: {country}

Output JSON schema:
{{
  "linkedin_profile": {{ "url": "", "verified": false }},
  "twitter_profile": {{ "url": "", "verified": false }},
  "facebook_profile": {{ "url": "", "verified": false }},
  "instagram_profile": {{ "url": "", "verified": false }}
}}
"""

        try:
            response = self.llm.generate(prompt)
            return json.loads(response)
        except Exception:
            return {
                "linkedin_profile": {},
                "twitter_profile": {},
                "facebook_profile": {},
                "instagram_profile": {}
            }
