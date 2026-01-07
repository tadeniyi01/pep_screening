from datetime import datetime, date
from typing import List

from models.media_models import MediaItem
from utils.source_registry import SOURCE_CREDIBILITY
from utils.url_utils import extract_domain


# ============================================================
# RECENCY DECAY
# ============================================================

def recency_decay(published_date: date) -> float:
    """
    Step-based decay function aligned with AML best practice.

    Age of article        Weight
    ------------------    ------
    0–12 months           1.00
    1–3 years             0.70
    3–5 years             0.40
    >5 years              0.20
    """

    years_old = (date.today() - published_date).days / 365.25

    if years_old <= 1:
        return 1.0
    if years_old <= 3:
        return 0.7
    if years_old <= 5:
        return 0.4
    return 0.2


# ============================================================
# PER-ITEM SCORING
# ============================================================

def score_item(item: MediaItem) -> float:
    """
    Computes final adverse media score for a single article.
    Mutates item with:
      - credibility_score
      - final_score
      - explanation
    """

    # --- Source credibility ---
    domain = extract_domain(item.source)
    credibility = SOURCE_CREDIBILITY.get(domain, SOURCE_CREDIBILITY["unknown"])
    item.credibility_score = credibility

    # --- Sentiment multiplier ---
    sentiment_multiplier = {
        "Negative": 1.5,
        "Neutral": 1.0,
        "Positive": 0.3,
    }.get(item.inferring, 1.0)

    # --- Published date handling ---
    try:
        published_date = datetime.strptime(item.date, "%Y-%m-%d").date()
    except Exception:
        published_date = date.today()

    decay = recency_decay(published_date)

    # --- Final score ---
    raw_score = item.score * credibility * sentiment_multiplier * decay
    final_score = round(min(raw_score, 100.0), 2)
    item.final_score = final_score

    # --- Per-article explanation (Professional Narrative) ---
    recency_desc = "recent" if decay == 1.0 else "historic" if decay < 0.5 else "past"
    item.explanation = (
        f"This article from {item.date} was published by {domain} and is classified as "
        f"{item.inferring.lower()} in sentiment. Given the source's market presence and "
        f"the {recency_desc} nature of the report, it contributes to the overall risk profile."
    )

    return final_score


# ============================================================
# FALSE-POSITIVE SUPPRESSION
# ============================================================

def suppress_false_positives(
    media: List[MediaItem],
    subject_name: str
) -> List[MediaItem]:
    """
    Conservative suppression rules:
    - Subject must be explicitly mentioned
    - Only negative or materially adverse items retained
    """

    subject_lower = subject_name.strip().lower()
    filtered: List[MediaItem] = []

    for item in media:
        # Must explicitly reference subject
        if not any(subject_lower == p.lower() for p in item.persons):
            continue

        # Ignore non-adverse signals
        if item.inferring != "Negative":
            continue

        filtered.append(item)

    return filtered


# ============================================================
# AGGREGATION
# ============================================================

def calculate_weighted_score(media: List[MediaItem]) -> float:
    """
    Aggregates per-article final scores using credibility as weight.
    """

    if not media:
        return 0.0

    weighted_sum = 0.0
    total_weight = 0.0

    for item in media:
        if item.final_score is None:
            continue

        weight = item.credibility_score or SOURCE_CREDIBILITY["unknown"]
        weighted_sum += item.final_score * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    return round(weighted_sum / total_weight, 2)


def derive_risk_status(score: float) -> str:
    """
    Risk banding aligned with AML screening norms.
    """

    if score >= 75:
        return "Potential High Risk"
    if score >= 40:
        return "Medium Risk"
    return "Clear"
