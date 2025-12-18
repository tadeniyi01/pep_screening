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

class ReasoningAgent:
    def __init__(self):
        self.llm = LLMService()

    def pep_reason(self, name: str, positions: list, level: str) -> list:
        prompt = f"""
        Explain why {name} qualifies as a Politically Exposed Person.
        Positions: {positions}
        Risk Level: {level}
        Respond concisely.
        """
        return [self.llm.generate(prompt)]

    def adverse_media_reason(self, name: str, headline: str) -> str:
        prompt = f"""
        Explain the adverse media risk for {name}.
        Headline: {headline}
        """
        return self.llm.generate(prompt)
