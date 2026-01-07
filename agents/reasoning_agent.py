import json
from typing import List, Union
from services.llm_service import LLMService

def normalize_reason_output(reason: Union[str, List[str]]) -> List[str]:
    """
    Ensures reason output is always List[str], even if LLM
    returns a stringified list.
    """

    if reason is None:
        return []

    # Case 1: Already correct
    if isinstance(reason, list):
        if all(isinstance(r, str) for r in reason):
            # Check for stringified list inside list
            if len(reason) == 1 and reason[0].strip().startswith("["):
                try:
                    parsed = json.loads(reason[0])
                    if isinstance(parsed, list):
                        return [str(p).strip() for p in parsed]
                except json.JSONDecodeError:
                    pass
            return [r.strip() for r in reason]

    # Case 2: Plain string
    if isinstance(reason, str):
        s = reason.strip()
        if s.startswith("["):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(p).strip() for p in parsed]
            except json.JSONDecodeError:
                pass
        return [s]

    # Fallback
    return [str(reason)]

from models.llm_schemas import PEPReasoningList
from config.prompts import Prompts

class ReasoningAgent:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    async def pep_reason(self, name: str, positions: list, level: str) -> list:
        prompt = Prompts.PEP_REASON.format(name=name, positions=positions, level=level)
        try:
            result = await self.llm.generate_structured(prompt, PEPReasoningList)
            return result.reasons
        except Exception:
            return [f"Detailed reasoning unavailable for {name}"]

    async def adverse_media_reason(self, name: str, headline: str) -> str:
        prompt = Prompts.ADVERSE_MEDIA_REASON.format(name=name, headline=headline)
        return await self.llm.generate(prompt)
