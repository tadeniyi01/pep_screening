from typing import List, Dict


TRUSTED_IMAGE_DOMAINS = [
    "wikimedia.org",
    "wikipedia.org",
    "gov.ng",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "facebook.com"
]


def extract_images(
    subject_name: str,
    sources: List[Dict]
) -> Dict[str, List[Dict] | float]:
    """
    Extract verified image URLs from trusted sources only.
    """

    images: List[Dict] = []

    for src in sources:
        image_url = src.get("image_url")
        source_name = src.get("source", "unknown")

        if not image_url:
            continue

        if not any(domain in image_url for domain in TRUSTED_IMAGE_DOMAINS):
            continue

        images.append({
            "url": image_url,
            "source": source_name,
            "confidence": 0.85 if "wikimedia" in image_url else 0.75
        })

    if not images:
        return {
            "value": [],
            "confidence": 0.0
        }

    # Deduplicate by URL
    unique = {img["url"]: img for img in images}
    deduped = list(unique.values())

    # Overall confidence = average confidence
    avg_confidence = sum(img["confidence"] for img in deduped) / len(deduped)

    return {
        "value": deduped,
        "confidence": round(avg_confidence, 2)
    }
