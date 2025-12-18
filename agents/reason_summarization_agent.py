# agents/reason_summarization_agent.py
from typing import List, Any
import json
import re

from services.llm_service import LLMService


class ReasonSummarizationAgent:
    """
    Produces explainable, UI-safe PEP reasoning.

    GUARANTEE:
    - Always returns List[str]
    - Never returns a string
    """

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    def summarize(self, payload: dict) -> List[str]:
        prompt = self._build_prompt(payload)
        raw = self.llm.generate(prompt)

        paragraphs = self._parse_llm_output(raw)

        if not isinstance(paragraphs, list):
            raise ValueError("ReasonSummarizationAgent must return List[str]")

        return self._clean_paragraphs(paragraphs)

    # -------------------------
    # INTERNALS
    # -------------------------

    def _parse_llm_output(self, raw: Any) -> List[str]:
        """
        Guarantees List[str] even if the LLM double-encodes JSON.
        """

        if isinstance(raw, list):
            return self._flatten_list(raw)

        if not isinstance(raw, str):
            return []

        raw = raw.strip()

        # Case 1: JSON array as string
        if raw.startswith("[") and raw.endswith("]"):
            try:
                parsed = json.loads(raw)
                return self._flatten_list(parsed)
            except json.JSONDecodeError:
                pass

        # Case 2: fallback text
        return self._split_and_clean(raw)
    def _flatten_list(self, items: list) -> List[str]:
        """
        Handles cases like:
        ["A", "B"]
        ["[\"A\", \"B\"]"]
        [["A", "B"]]
        """
    
        flattened: List[str] = []
    
        for item in items:
            # Already correct
            if isinstance(item, str) and not item.strip().startswith("["):
                flattened.append(item)
                continue
            
            # Stringified JSON list
            if isinstance(item, str) and item.strip().startswith("["):
                try:
                    parsed = json.loads(item)
                    if isinstance(parsed, list):
                        flattened.extend(str(p) for p in parsed)
                except json.JSONDecodeError:
                    continue
                
            # Nested list
            elif isinstance(item, list):
                flattened.extend(self._flatten_list(item))
    
        return flattened
    

    def _build_prompt(self, payload: dict) -> str:
        return f"""
You are a compliance analyst producing an explainable PEP determination.

STRICT OUTPUT FORMAT (MANDATORY):
- Return a JSON ARRAY of STRINGS
- Each string = exactly ONE reason
- NO numbering
- NO newlines
- NO markdown
- NO headings

CONTENT RULES:
- Distinguish confirmed vs excluded roles
- Use confidence values
- Conservative tone for exclusions

DATA:
{json.dumps(payload, indent=2)}
"""

    def _split_and_clean(self, text: str) -> List[str]:
        text = text.replace("\r\n", "\n").strip()
        parts = re.split(r"\n+|\.\s+(?=[A-Z])", text)

        cleaned = []
        for p in parts:
            p = re.sub(r"^\s*(?:\d+[\.\)]|[-•])\s*", "", p)
            p = re.sub(r"\s+", " ", p).strip()
            if p:
                cleaned.append(p)

        return cleaned

    def _clean_paragraphs(self, paragraphs: List[str]) -> List[str]:
        cleaned = []
        for p in paragraphs:
            if not isinstance(p, str):
                continue
            p = re.sub(r"\s+", " ", p).strip()
            if p:
                cleaned.append(p)
        return cleaned
