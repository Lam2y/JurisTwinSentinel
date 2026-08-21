from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.security import current_user
from ..db.database import get_db
from ..db.models import AnswerFeedback, Interaction, User
from ..schemas import AskRequest, FeedbackRequest
from ..services.ledger import append_entry
from ..services.resolution_engine import answer_question, record_feedback_gap, redact_sensitive

router = APIRouter(prefix="/ask", tags=["ask"])


@router.post("")
def ask(body: AskRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return answer_question(db, user, body.question)


@router.post("/feedback")
def feedback(body: FeedbackRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    interaction = db.execute(select(Interaction).where(Interaction.interaction_ref == body.interaction_ref)).scalar_one_or_none()
    if not interaction:
        raise HTTPException(404, "Answer interaction not found")
    if interaction.user_id != user.id and user.role != "superadmin":
        raise HTTPException(403, "You can only rate your own answer interactions")
    existing = db.execute(select(AnswerFeedback).where(AnswerFeedback.interaction_ref == body.interaction_ref)).scalar_one_or_none()
    if existing:
        return {"ok": True, "feedback_ref": existing.feedback_ref, "helpful": existing.helpful, "escalated": existing.escalated, "already_recorded": True}

    comment = redact_sensitive(body.comment or "", db) or None
    row = AnswerFeedback(
        feedback_ref=f"FB-{uuid4().hex[:10].upper()}",
        interaction_ref=interaction.interaction_ref,
        helpful=body.helpful,
        comment_masked=comment,
        escalated=False,
    )
    db.add(row)
    db.flush()

    gap_ref = None
    if not body.helpful and interaction.status == "ANSWERED":
        gap = record_feedback_gap(db, user, interaction.question_masked)
        row.escalated = True
        gap_ref = gap.gap_ref
    append_entry(db, "ANSWER_FEEDBACK_RECORDED", user.email, {
        "feedback_ref": row.feedback_ref,
        "interaction_ref": row.interaction_ref,
        "helpful": body.helpful,
        "escalated": row.escalated,
    })
    db.commit()
    return {"ok": True, "feedback_ref": row.feedback_ref, "helpful": row.helpful, "escalated": row.escalated, "review_ref": gap_ref}
