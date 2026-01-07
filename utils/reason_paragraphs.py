from typing import List

def _number_reason_paragraphs(numbered_reasons: List[str]) -> List[str]:
    if not numbered_reasons:
        return []

    if isinstance(numbered_reasons, list):
        return [f"{i + 1}. {r}" for i, r in enumerate(numbered_reasons)]

    if isinstance(numbered_reasons, str):
        try:
            parsed = ast.literal_eval(numbered_reasons)
            if isinstance(parsed, list):
                return [f"{i + 1}. {r}" for i, r in enumerate(parsed)]
        except Exception as e:
            logger.error("Failed to parse numbered_reasons string: %s", e)

    raise ValueError(f"Invalid numbered_reasons format: {type(numbered_reasons)}")