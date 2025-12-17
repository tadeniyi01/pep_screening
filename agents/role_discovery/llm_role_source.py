import json
from typing import List
from pydantic import BaseModel, Field
from models.role_models import DiscoveredRole
from services.llm_service import LLMService


# ============================
#   STRICT RESPONSE SCHEMA
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
#   ROLE SOURCE
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
            print(f"[LLMRoleSource] Failure: {e}")
            return []

        roles: List[DiscoveredRole] = []

        for r in parsed.roles:
            roles.append(
                DiscoveredRole(
                    title=r.title.strip(),
                    organisation=r.organisation.strip(),
                    country=r.country.upper(),
                    start_year=r.start_year,
                    end_year=r.end_year,
                    source=self.SOURCE_NAME,
                    confidence=min(r.confidence, 0.70),  # 🔒 HARD CAP
                )
            )

        return roles

    # ============================
    #   PROMPT
    # ============================

    def _build_prompt(self, name: str, country: str) -> str:
        return f"""
You are a compliance intelligence system.

TASK:
Identify PUBLIC OFFICES held by the person below.

RULES:
- Use tools if needed (e.g. search, registry)
- ONLY public/government roles
- NO private or speculative roles
- OMIT uncertain roles
- Return STRICT JSON ONLY

PERSON:
Name: {name}
Country: {country}

OUTPUT FORMAT:
{{
  "roles": [
    {{
      "title": "string",
      "organisation": "string",
      "country": "{country}",
      "start_year": number | null,
      "end_year": number | null,
      "confidence": number (0.0 - 1.0)
    }}
  ]
}}
"""

    # ============================
    #   SAFE PARSING
    # ============================

    def _parse(self, raw: str) -> LLMRoleResponse:
        raw = raw.strip()
        raw = raw.removeprefix("```json").removesuffix("```")
        return LLMRoleResponse.model_validate(json.loads(raw))
