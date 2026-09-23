import uuid

from sqlalchemy.orm import Session

from app.models import CustodyLog


def log_event(
    session: Session,
    item_id: uuid.UUID | None,
    event_type: str,
    actor: str,
    payload_hash: str,
    reason: str | None = None,
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
