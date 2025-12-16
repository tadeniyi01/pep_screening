from typing import List
from models.media_models import MediaItem


from typing import List
from models.media_models import MediaItem
from utils.source_registry import SOURCE_CREDIBILITY
from utils.url_utils import extract_domain


def calculate_weighted_score(media: List[MediaItem]) -> float:
    if not media:
        return 0.0

    total_weight = 0.0
    weighted_sum = 0.0

    for item in media:
        domain = extract_domain(item.source)
        credibility = SOURCE_CREDIBILITY.get(domain, SOURCE_CREDIBILITY["unknown"])

        sentiment_weight = 1.0
        if item.inferring == "Negative":
            sentiment_weight = 1.5

        final_weight = credibility * sentiment_weight

        weighted_sum += item.score * final_weight
        total_weight += final_weight

    return round(weighted_sum / total_weight, 2)


def derive_risk_status(score: float) -> str:
    if score >= 75:
        return "Potential High Risk"
    elif score >= 40:
        return "Medium Risk"
    return "Clear"
