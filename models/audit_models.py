from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime, timezone
import uuid


@dataclass
class AuditEvent:
    event_id: str
    event_type: str
    timestamp: str
    payload: Dict


@dataclass
class AuditTrace:
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    events: List[AuditEvent] = field(default_factory=list)

    def add_event(self, event_type: str, payload: Dict):
        self.events.append(
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                timestamp=datetime.now(timezone.utc).isoformat(),
                payload=payload,
            )
        )
