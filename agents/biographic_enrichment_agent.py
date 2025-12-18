from typing import Dict, Any, List
from datetime import datetime

from agents.extractors.state_extractor import extract_state_of_origin
from agents.extractors.relatives_extractor import extract_relatives
from agents.extractors.associates_extractor import extract_associates
from agents.extractors.dob_extractor import extract_date_of_birth
from agents.extractors.education_extractor import extract_education
from agents.extractors.alias_extractor import extract_aliases
from agents.extractors.other_names_extractor import extract_other_names
from agents.extractors.image_extractor import extract_images
from agents.extractors.middle_name_extractor import extract_middle_name


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

        # --- STATE OF ORIGIN ---
        state_result = extract_state_of_origin(
            subject_name=name,
            country=country,
            sources=sources
        )
        state = state_result["value"] if state_result["confidence"] >= 0.75 else ""

        # --- MIDDLE NAME ---
        middle_name_result = extract_middle_name(
            subject_name=name,
            sources=sources
        )
        middle_name = (
            middle_name_result["value"]
            if middle_name_result["confidence"] >= 0.75
            else ""
        )

        # --- DATE OF BIRTH ---
        dob_result = extract_date_of_birth(
            subject_name=name,
            sources=sources
        )
        date_of_birth = (
            dob_result["value"]
            if dob_result["confidence"] >= 0.75
            else None
        )

        age = None
        if date_of_birth:
            try:
                birth_year = int(date_of_birth[:4])
                age = datetime.now().year - birth_year
            except Exception:
                pass

        # --- EDUCATION ---
        education_result = extract_education(
            subject_name=name,
            sources=sources
        )
        education = (
            education_result["value"]
            if education_result["confidence"] >= 0.75
            else []
        )

        # --- RELATIVES ---
        relatives_result = extract_relatives(
            subject_name=name,
            sources=sources
        )
        relatives = (
            relatives_result["value"]
            if relatives_result["confidence"] >= 0.75
            else []
        )

        # --- ASSOCIATES ---
        associates_result = extract_associates(
            subject_name=name,
            sources=sources
        )
        associates = (
            associates_result["value"]
            if associates_result["confidence"] >= 0.75
            else []
        )

        # --- ALIASES ---
        aliases_result = extract_aliases(
            subject_name=name,
            sources=sources
        )
        aliases = (
            aliases_result["value"]
            if aliases_result["confidence"] >= 0.75
            else []
        )

        # --- OTHER NAMES ---
        other_names_result = extract_other_names(
            subject_name=name,
            sources=sources
        )
        other_names = (
            other_names_result["value"]
            if other_names_result["confidence"] >= 0.75
            else []
        )

        # --- IMAGES ---
        images_result = extract_images(
            subject_name=name,
            sources=sources
        )
        images = (
            images_result["value"]
            if images_result["confidence"] >= 0.75
            else []
        )

        return {
            "state": state,
            "state_confidence": state_result["confidence"],

            "date_of_birth": date_of_birth,
            "date_of_birth_confidence": dob_result["confidence"],

            "age": age,

            "middle_name": middle_name,
            "middle_name_confidence": middle_name_result["confidence"],

            "education": education,
            "education_confidence": education_result["confidence"],

            "relatives": relatives,
            "relatives_confidence": relatives_result["confidence"],

            "associates": associates,
            "associates_confidence": associates_result["confidence"],

            "aliases": [a["name"] for a in aliases],
            "aliases_confidence": aliases_result["confidence"],

            "other_names": [n["name"] for n in other_names],
            "other_names_confidence": other_names_result["confidence"],

            "image": [img["url"] for img in images],
            "image_confidence": images_result["confidence"]
        }
