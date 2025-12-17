import json
from typing import Optional, List, Dict, Callable


class LLMService:
    """
    Provider-agnostic LLM interface with tool support.
    """

    def __init__(
        self,
        client=None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        tools: Optional[List[dict]] = None,
        tool_map: Optional[Dict[str, Callable]] = None,
    ):
        self.client = client
        self.model = model
        self.temperature = temperature
        self.tools = tools or []
        self.tool_map = tool_map or {}

    def generate(self, prompt: str) -> str:
        if not self.client:
            return "LLM_GENERATED_TEXT"

        messages = [
            {"role": "system", "content": "You are a compliance intelligence system."},
            {"role": "user", "content": prompt},
        ]

        while True:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                tools=self.tools if self.tools else None,
                tool_choice="auto" if self.tools else "none",
            )

            choice = completion.choices[0]
            finish_reason = choice.finish_reason

            # Tool execution loop
            if finish_reason == "tool_calls":
                messages.append(choice.message)

                for tool_call in choice.message.tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)

                    if name not in self.tool_map:
                        raise RuntimeError(f"Unknown tool: {name}")

                    result = self.tool_map[name](**args)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": name,
                        "content": json.dumps(result),
                    })

                continue

            # Final answer
            return choice.message.content.strip()
