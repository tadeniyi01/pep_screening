import json
import re
from typing import List
from pydantic import BaseModel, Field
from models.role_models import DiscoveredRole
from services.llm_service import LLMService
import logging

logger = logging.getLogger(__name__)

# ============================
# STRICT RESPONSE SCHEMA
# ============================

class LLMRoleSchema(BaseModel):
    title: str
    organisation: str
    country: str
    start_year: int | None = Field(None, ge=1900, le=2100)
    end_year: int | None = Field(None, ge=1900, le=2100)
    confidence: float = Field(..., ge=0.0, le=1.0)


class LLMRoleResponse(BaseModel):
    roles: List[LLMRoleSchema]


# ============================
# ROLE SOURCE
# ============================

class LLMRoleSource:
    """
    LLM-based role discovery (supplementary only).
    Tool-aware, schema-validated, confidence-capped.
    """

    SOURCE_NAME = "LLM"

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    def fetch(self, name: str, country: str) -> List[DiscoveredRole]:
        prompt = self._build_prompt(name, country)

        try:
            raw = self.llm.generate(prompt)
            parsed = self._parse(raw)
        except Exception as e:
            logger.warning(f"[LLMRoleSource] Failure generating or parsing LLM output: {e}")
            logger.debug(f"[LLMRoleSource] Raw LLM output: {raw if 'raw' in locals() else 'N/A'}")
            return []

        roles: List[DiscoveredRole] = []

        for r in parsed.roles:
            roles.append(
                DiscoveredRole(
                    title=r.title.strip(),
                    organisation=r.organisation.strip(),
                    country=r.country.upper() if r.country else country.upper(),
                    start_year=r.start_year,
                    end_year=r.end_year,
                    source=self.SOURCE_NAME,
                    confidence=min(r.confidence, 0.70),  # 🔒 HARD CAP
                )
            )

        return roles

    # ============================
    # PROMPT
    # ============================

    def _build_prompt(self, name: str, country: str) -> str:
        return f"""
    You are a compliance intelligence system.
    
    TASK:
    Identify PUBLIC OFFICES held by the person below.
    
    RULES:
    - Use reliable sources only.
    - ONLY include public/government roles.
    - OMIT private, speculative, or uncertain roles.
    - RETURN STRICT JSON ONLY — no extra text, commentary, or explanation.
    - JSON keys and types MUST match this schema:
      {{
        "roles": [
          {{
            "title": "string",
            "organisation": "string",
            "country": "{country}",
            "start_year": number or null,
            "end_year": number or null,
            "confidence": number (0.0 - 1.0)
          }}
        ]
      }}
    
    PERSON:
    Name: {name}
    Country: {country}
    
    EXAMPLES OF CORRECT JSON:
    {{
      "roles": [
        {{
          "title": "President of the Federal Republic of Nigeria",
          "organisation": "Federal Government",
          "country": "{country}",
          "start_year": 2023,
          "end_year": null,
          "confidence": 0.7
        }},
        {{
          "title": "Governor of Lagos State",
          "organisation": "Lagos State Government",
          "country": "{country}",
          "start_year": 1999,
          "end_year": 2007,
          "confidence": 0.65
        }}
      ]
    }}
    
    STRICTLY FOLLOW THIS FORMAT. DO NOT OUTPUT ANYTHING ELSE.
    """


    # ============================
    # SAFE PARSING
    # ============================

    def _parse(self, raw: str) -> LLMRoleResponse:
        """
        Try strict JSON parsing first.
        If it fails, do a best-effort extraction of role titles.
        """
        raw = raw.strip()
        raw = raw.removeprefix("```json").removesuffix("```")

        try:
            return LLMRoleResponse.model_validate(json.loads(raw))
        except json.JSONDecodeError as e:
            logger.warning(f"[LLMRoleSource] JSON parse failure: {e}")
            logger.warning(f"[LLMRoleSource] Raw output: {raw}")

            # Fallback: extract role titles from lines that look like roles
            # Very permissive regex: grabs non-empty lines inside "roles" array if present
            lines = re.findall(r'\s*[\-\*]?\s*([A-Za-z0-9 ,.-]+)\s*', raw)
            roles = [
                LLMRoleSchema(
                    title=line.strip(),
                    organisation="",
                    country="",
                    confidence=0.5
                )
                for line in lines if line.strip()
            ]
            logger.info(f"[LLMRoleSource] Recovered {len(roles)} role(s) from fallback parsing")
            return LLMRoleResponse(roles=roles)
