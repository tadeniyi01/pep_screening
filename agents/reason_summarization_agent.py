# agents/reason_summarization_agent.py
from typing import List, Any
import json
import re

from services.llm_service import LLMService
from models.llm_schemas import PEPReasoningList
from config.prompts import Prompts


class ReasonSummarizationAgent:
    """
    Produces explainable, UI-safe PEP reasoning using structured outputs.
    """

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    async def summarize(self, payload: dict) -> List[str]:
        prompt = Prompts.SUMMARIZE_DETERMINATION.format(payload=json.dumps(payload, indent=2))
        
        try:
            result = await self.llm.generate_structured(prompt, PEPReasoningList)
            return self._clean_paragraphs(result.reasons)
        except Exception as e:
            # Fallback (log and return empty or retry?)
            print(f"[ReasonSummarizationAgent Error] {e}")
            return []

    def _clean_paragraphs(self, paragraphs: List[str]) -> List[str]:
        cleaned = []
        for p in paragraphs:
            if not isinstance(p, str):
                continue
            p = re.sub(r"\s+", " ", p).strip()
            if p:
                cleaned.append(p)
        return cleaned
