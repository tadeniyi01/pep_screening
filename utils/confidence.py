def confidence_from_sources(source_count: int) -> str:
    if source_count >= 3:
        return "High"
    if source_count == 2:
        return "Medium"
    return "Low"
