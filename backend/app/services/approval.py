import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlmodel import Session
from backend.app.models.entities import AuditLog, ReplyDraft

# Valid transition map per SRS Section 4.3
VALID_TRANSITIONS = {
    "draft": {"edited", "approved", "rejected"},
    "edited": {"edited", "approved", "rejected"},
    "approved": {"posted", "edited"},
    "rejected": {"draft"},  # via regenerate
    "posted": set(),         # terminal state
}


def validate_draft_transition(
    session: Session,
    draft: ReplyDraft,
    new_status: Optional[str] = None,
    new_text: Optional[str] = None,
    user_id: Optional[str] = None,
) -> ReplyDraft:
    """
    Enforces server-side draft approval state machine and writes audit log.
    Raises 409 Conflict if transition is not permitted.
    """
    old_status = draft.status

    # If text is modified without changing status, status automatically becomes 'edited'
    if new_text is not None and new_text != draft.text:
        draft.text = new_text
        if new_status is None and old_status in {"draft", "approved"}:
            new_status = "edited"

    if new_status and new_status != old_status:
        allowed = VALID_TRANSITIONS.get(old_status, set())
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Invalid draft transition from '{old_status}' to '{new_status}'. Allowed: {sorted(list(allowed))}",
            )
        draft.status = new_status

        if new_status == "approved":
            draft.approved_at = datetime.now(timezone.utc)
        elif new_status == "edited" and old_status == "approved":
            # Re-approval required after editing an already approved draft
            draft.approved_at = None

    if user_id:
        draft.edited_by = user_id

    session.add(draft)

    # Record Audit Log entry (FR-5, M3-QA-1)
    audit = AuditLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        action=f"transition:{old_status}->{draft.status}",
        entity="reply_draft",
        entity_id=draft.id,
        details=f"Draft status updated to '{draft.status}'",
        timestamp=datetime.now(timezone.utc),
    )
    session.add(audit)
    session.commit()
    session.refresh(draft)

    return draft
