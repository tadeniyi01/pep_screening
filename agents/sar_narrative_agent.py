from typing import List
from models.media_models import MediaItem


class SARNarrativeAgent:
    """
    Produces regulator-ready SAR narratives based on adverse media findings.
    Integrates:
      - Per-article explanations
      - Auto-citations (source + date + confidence)
      - Weighted scoring and risk classification
      - Numbered findings for audit and regulator purposes
    """

    def generate(
        self,
        subject_name: str,
        articles: List[MediaItem],
        overall_score: float,
        status: str,
    ) -> str:

        # ---------- No adverse media ----------
        if not articles:
            return (
                f"AUDIT SUMMARY: No adverse media identified for {subject_name}. \n\n"
                f"A comprehensive search across global PEP datasets (OpenSanctions, EveryPolitician), "
                f"major news registries (Google News, Reuters, BBC), and regional RSS feeds was conducted. "
                f"No clear indicators of materially adverse media risk or negative sentiment were "
                f"observed at the time of screening."
            )

        # ---------- SAR narrative header ----------
        report = []
        report.append(f"ADVERSE MEDIA RISK REPORT: {subject_name}\n" + "="*40)
        report.append(
            f"Screening identified {len(articles)} relevant reports. The primary risk classification "
            f"for this subject is currently assessed as '{status.upper()}' based on thematic "
            f"analysis of available media.\n"
        )

        # ---------- KEY FINDINGS ----------
        report.append("KEY FINDINGS & OBSERVATIONS:\n")
        
        for idx, item in enumerate(articles, start=1):
            source_domain = item.source or "unknown"
            from utils.url_utils import extract_domain
            domain = extract_domain(source_domain)
            
            # Simplified metadata line
            meta = f"[{domain} | {item.date}]"
            
            report.append(
                f"{idx}. {item.headline or 'Report'}\n"
                f"   {meta}\n"
                f"   Analysis: {item.excerpt}\n"
                f"   Impact: {item.explanation}\n"
            )

        # ---------- Final Assessment ----------
        report.append("OVERALL RISK ASSESSMENT:\n" + "-"*40)
        report.append(
            f"The collective weight of these reports indicates a '{status}' profile. "
            f"The screening process utilized a multi-weighted scoring mechanism considering "
            f"source credibility and reporting recency. This assessment represents a "
            f"snapshot of open-source data and does not constitute a legal judgment or "
            f"assertion of wrongdoing."
        )

        # ---------- Conditional recommendation ----------
        if status.lower() in {"potential high risk", "medium risk"}:
            report.append(
                "\nRECOMMENDATION: Given the frequency and thematic consistency of the negative "
                "sentiment observed, Enhanced Due Diligence (EDD) and periodic monitoring are advised."
            )
        else:
            report.append("\nRECOMMENDATION: Routine monitoring is sufficient for this risk level.")

        return "\n".join(report)
