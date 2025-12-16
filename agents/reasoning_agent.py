from services.llm_service import LLMService


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
