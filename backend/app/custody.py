import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models import CustodyLog


def log_event(
    session: Session,
    item_id: Optional[uuid.UUID],
    event_type: str,
    actor: str,
    payload_hash: str,
    reason: Optional[str] = None,
) -> None:
    session.add(
        CustodyLog(
            item_id=item_id,
            event_type=event_type,
            actor=actor,
            reason=reason,
            payload_hash=payload_hash,
        )
    )
