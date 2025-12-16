import json
from models.audit_models import AuditTrace


class AuditService:
    def __init__(self, file_path="audit.log"):
        self.file_path = file_path

    def persist(self, trace: AuditTrace):
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(trace.__dict__, default=str))
            f.write("\n")
