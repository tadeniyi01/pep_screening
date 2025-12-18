from typing import List
from models.media_models import MediaItem


class SARNarrativeAgent:
    """
    Produces regulator-ready SAR narratives based on adverse media findings.
    """

    def generate(
        self,
        subject_name: str,
        articles: List[MediaItem],
        overall_score: float,
        status: str,
    ) -> str:

        if not articles:
            return (
                f"No adverse media was identified for {subject_name}. "
                f"Based on available open-source intelligence, no indicators "
                f"of elevated adverse media risk were observed at the time of screening."
            )

        paragraphs = [
            (
                f"This report summarizes adverse media findings relating to {subject_name}. "
                f"A total of {len(articles)} potentially relevant adverse media articles "
                f"were identified through open-source monitoring."
            )
        ]

        for idx, item in enumerate(articles, start=1):
            paragraphs.append(
                (
                    f"Article {idx}: On {item.date}, {item.source} reported that "
                    f"{item.excerpt}. Based on contextual analysis, this article "
                    f"was assessed as indicating a {item.inferring.lower()} risk signal "
                    f"and assigned a final weighted score of {item.final_score}. "
                    f"{item.explanation}"
                )
            )

        paragraphs.append(
            (
                f"The aggregated adverse media score for {subject_name} is {overall_score}, "
                f"resulting in an overall adverse media classification of '{status}'. "
                f"This assessment is derived exclusively from publicly available information "
                f"and does not assert criminal activity or legal wrongdoing."
            )
        )

        if status.upper() in {"HIGH", "MEDIUM"}:
            paragraphs.append(
                "Given the nature, frequency, and thematic consistency of the identified "
                "media coverage, enhanced due diligence and further review may be warranted."
            )

        return "\n\n".join(paragraphs)
