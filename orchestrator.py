from services.audit_service import AuditService
from models.audit_models import AuditTrace


class ScreeningOrchestrator:
    def __init__(self):
        from agents.identity_agent import IdentityAgent
        from agents.pep_agent import PEPAgent
        from agents.adverse_media_agent import AdverseMediaAgent

        self.identity = IdentityAgent()
        self.pep = PEPAgent()
        self.media = AdverseMediaAgent()
        self.audit = AuditService()

    def run(
        self,
        query: str,
        country: str = "",
        start_date: str | None = None,
        end_date: str | None = None
    ):
        trace = AuditTrace()

        # ---------- INPUT ----------
        trace.add_event(
            "INPUT_RECEIVED",
            {
                "query": query,
                "country": country,
                "start_date": start_date,
                "end_date": end_date
            }
        )

        # ---------- IDENTITY ----------
        normalized_name = self.identity.normalize_name(query)
        trace.add_event(
            "NAME_NORMALIZED",
            {"normalized_name": normalized_name}
        )

        # ---------- PEP ----------
        pep_profile = self.pep.evaluate(normalized_name, country)
        trace.add_event(
            "PEP_EVALUATED",
            {
                "is_pep": pep_profile.is_pep,
                "pep_level": pep_profile.pep_level,
                "reason": pep_profile.reason
            }
        )

        # ---------- ADVERSE MEDIA ----------
        media_result = self.media.analyze(
            normalized_name,
            start_date=start_date,
            end_date=end_date
        )
        trace.add_event(
            "ADVERSE_MEDIA_ANALYZED",
            {
                "total": media_result.total,
                "weighted_score": media_result.weighted_score,
                "status": media_result.status
            }
        )

        # ---------- AUDIT ----------
        self.audit.persist(trace)

        # ---------- RESPONSE ----------
        return {
            "pep": pep_profile.dict(),
            "adverse_media": media_result.dict(),
            "audit_trace_id": trace.trace_id
        }
