from datetime import datetime, timezone
# from services.pep_taxonomy_service import NigeriaPEPTaxonomyService

# ------------------------
# Role resolution helpers
# ------------------------

def split_current_previous_roles(
    roles: list,
    taxonomy_service,
) -> tuple[list[str], list[str]]:
    """
    Robust role resolution for any PEP.
    Conservative by default.
    """

    current_year = datetime.now(timezone.utc).year

    resolved = []

    for r in roles:
        priority = taxonomy_service.role_priority(r.title)

        resolved.append({
            "title": r.title,
            "priority": priority,
            "start": r.start_year,
            "end": r.end_year,
            "source": r.source,
            "confidence": r.confidence,
        })

    # Explicitly ended roles
    previous = {
        r["title"] for r in resolved
        if r["end"] and r["end"] < current_year
    }

    # Candidate current roles
    candidates = [
        r for r in resolved
        if r["title"] not in previous
    ]

    # Prefer roles with explicit start and no end
    dated_current = [
        r for r in candidates
        if r["start"] and (r["end"] is None or r["end"] >= current_year)
    ]

    # If still ambiguous, pick highest priority
    active = dated_current or candidates
    active.sort(key=lambda r: (r["priority"], r["confidence"]), reverse=True)

    if not active:
        return [], list(previous)

    primary = active[0]

    current = [primary["title"]]

    # Everything else becomes previous
    for r in resolved:
        if r["title"] != primary["title"]:
            previous.add(r["title"])

    return list(dict.fromkeys(current)), list(dict.fromkeys(previous))