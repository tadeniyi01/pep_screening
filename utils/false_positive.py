from typing import List
from models.media_models import MediaItem


def suppress_false_positives(
    media: List[MediaItem],
    subject_name: str
) -> List[MediaItem]:
    """
    Removes weak, ambiguous, or non-specific mentions.
    """

    filtered = []

    for item in media:
        if subject_name not in item.persons:
            continue

        if item.entity_link_confidence < 0.6:
            continue

        if item.credibility_score < 0.7:
            continue

        filtered.append(item)

    return filtered
