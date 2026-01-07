# agents/biographic_enrichment_agent.py

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from agents.extractors.state_extractor import extract_state_of_origin
from agents.extractors.relatives_extractor import extract_relatives
from agents.extractors.associates_extractor import extract_associates
from agents.extractors.dob_extractor import extract_date_of_birth
from agents.extractors.education_extractor import extract_education
from agents.extractors.alias_extractor import extract_aliases
from agents.extractors.other_names_extractor import extract_other_names
from agents.extractors.image_extractor import extract_images
from agents.extractors.middle_name_extractor import extract_middle_name
from agents.extractors.gender_extractor import infer_gender_from_sources


logger = logging.getLogger(__name__)

class BiographicEnrichmentAgent:
    """
    Enriches biographic attributes using normalized evidence sources.
    Conservative by design.
    """

    def enrich(
        self,
        name: str,
        country: str,
        roles: list,
        sources: List[Dict] | None = None
    ) -> Dict[str, Any]:

        sources = sources or []

        def _format_result(result, key_name="value"):
            """
            Wrap result with provenance info.
            """
            value = result.get(key_name)
            confidence = result.get("confidence", 0.0)
            evidence = result.get("value") if isinstance(result.get("value"), list) else [value]
            evidence_sources = [src.get("source", "unknown") if isinstance(src, dict) else "unknown" 
                                for src in evidence if src]
            return {
                "value": value,
                "confidence": confidence,
                "sources": list(set(evidence_sources))
            }

        # --- STATE OF ORIGIN ---
        state_result = extract_state_of_origin(subject_name=name, country=country, sources=sources)
        state = state_result["value"] if state_result["confidence"] >= 0.60 else None

        # --- MIDDLE NAME ---
        middle_result = extract_middle_name(subject_name=name, sources=sources)
        middle_name = middle_result["value"] if middle_result["confidence"] >= 0.60 else None

        # --- DATE OF BIRTH ---
        dob_result = extract_date_of_birth(subject_name=name, sources=sources)
        date_of_birth = dob_result["value"] if dob_result["confidence"] >= 0.60 else None
        age = None
        if date_of_birth:
            try:
                birth_year = int(date_of_birth[:4])
                age = datetime.now().year - birth_year
            except Exception:
                pass

        # --- EDUCATION ---
        education_result = extract_education(subject_name=name, sources=sources)

        # --- RELATIVES ---
        relatives_result = extract_relatives(subject_name=name, sources=sources)

        # --- ASSOCIATES ---
        associates_result = extract_associates(subject_name=name, sources=sources)

        # --- ALIASES ---
        aliases_result = extract_aliases(subject_name=name, sources=sources)

        # --- OTHER NAMES ---
        other_names_result = extract_other_names(subject_name=name, sources=sources)

        # --- IMAGES ---
        images_result = extract_images(subject_name=name, sources=sources)

        # --- GENDER ---
        gender_result = infer_gender_from_sources(name=name, sources=sources)
        gender = gender_result["value"]
        gender_confidence = gender_result["confidence"]
        gender_sources = gender_result["sources"]

        return {
            "state": state,
            "state_confidence": state_result["confidence"],
            "state_sources": _format_result(state_result).get("sources", []),

            "date_of_birth": date_of_birth,
            "date_of_birth_confidence": dob_result["confidence"],
            "date_of_birth_sources": _format_result(dob_result).get("sources", []),

            "age": age,

            "middle_name": middle_name,
            "middle_name_confidence": middle_result["confidence"],
            "middle_name_sources": _format_result(middle_result).get("sources", []),

            "education": education_result["value"] if education_result["confidence"] >= 0.60 else [],
            "education_confidence": education_result["confidence"],
            "education_sources": _format_result(education_result).get("sources", []),

            "relatives": relatives_result["value"] if relatives_result["confidence"] >= 0.60 else [],
            "relatives_confidence": relatives_result["confidence"],
            "relatives_sources": _format_result(relatives_result).get("sources", []),

            "associates": associates_result["value"] if associates_result["confidence"] >= 0.60 else [],
            "associates_confidence": associates_result["confidence"],
            "associates_sources": _format_result(associates_result).get("sources", []),

            "aliases": [a["name"] for a in aliases_result["value"]] if aliases_result["confidence"] >= 0.60 else [],
            "aliases_confidence": aliases_result["confidence"],
            "aliases_sources": _format_result(aliases_result).get("sources", []),

            "other_names": [n["name"] for n in other_names_result["value"]] if other_names_result["confidence"] >= 0.60 else [],
            "other_names_confidence": other_names_result["confidence"],
            "other_names_sources": _format_result(other_names_result).get("sources", []),

            "image": [img["url"] for img in images_result["value"]] if images_result["confidence"] >= 0.60 else [],
            "image_confidence": images_result["confidence"],
            "image_sources": _format_result(images_result).get("sources", []),

            "gender": gender,
            "gender_sources": gender_sources
        }
