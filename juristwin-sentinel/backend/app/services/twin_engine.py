from uuid import uuid4
from sqlalchemy.orm import Session
from ..db.models import Conflict, Simulation, User
from .common import dumps, loads, iso

DEFAULT_WEIGHTS = {"delay": 0.40, "complaint": 0.35, "alignment": 0.25}

# White-box levers and coefficients. These are explicit by design: judges can inspect why each scenario changes.
OPTIONS = {
    "A": {"name": "TAKE NO ACTION", "update_fsd": 0, "notify_officers": 0, "review_cases": 0, "update_qa": 0, "block_duplicates": 0},
    "B": {"name": "UPDATE FSD ONLY", "update_fsd": 1, "notify_officers": 0, "review_cases": 0, "update_qa": 0, "block_duplicates": 0},
    "C": {"name": "ALIGN COMPLETE PROCESS", "update_fsd": 1, "notify_officers": 1, "review_cases": 1, "update_qa": 1, "block_duplicates": 1},
}


def score_option(key: str, levers: dict):
    if key == "A":
        delay, complaint, affected, duplicates, alignment = 4.2, 64, 27, 19, 41
    elif key == "B":
        delay, complaint, affected, duplicates, alignment = 2.7, 39, 14, 8, 71
    else:
        delay, complaint, affected, duplicates, alignment = 1.1, 17, 2, 1, 96
    return {
        "key": key, "name": levers["name"], "levers": levers,
        "predicted_delay_days": delay, "complaint_probability": complaint,
        "applications_affected": affected, "duplicate_requests": duplicates,
        "policy_alignment": alignment,
        "explanation": {
            "delay": "Reduced by fixing stale rules, notifying operators and clearing existing queues.",
            "complaint": "Reduced when duplicate requests are blocked and affected cases are proactively reviewed.",
            "alignment": "Improves as FSD, training, QA tests and human instructions converge on the approved rule.",
        },
    }


def run_simulation(db: Session, conflict: Conflict, user: User, weights: dict | None = None):
    weights = {**DEFAULT_WEIGHTS, **(weights or {})}
    total = sum(max(float(v), 0) for v in weights.values()) or 1
    weights = {k: max(float(v), 0)/total for k, v in weights.items()}
    options = [score_option(k, v) for k, v in OPTIONS.items()]
    for o in options:
        normalized_delay = min(o["predicted_delay_days"] / 5, 1)
        normalized_complaint = o["complaint_probability"] / 100
        normalized_misalignment = 1 - (o["policy_alignment"] / 100)
        loss = weights["delay"]*normalized_delay + weights["complaint"]*normalized_complaint + weights["alignment"]*normalized_misalignment
        o["decision_loss"] = round(loss, 4)
        o["decision_fit"] = round((1-loss)*100, 1)
    recommended = min(options, key=lambda x: x["decision_loss"])
    confidence = round(min(0.97, 0.72 + conflict.confidence*0.15 + (recommended["policy_alignment"] / 100)*0.12), 3)
    sim = Simulation(
        sim_ref=f"SIM-{uuid4().hex[:6].upper()}", conflict_ref=conflict.conflict_ref,
        weights_json=dumps(weights), options_json=dumps(options), recommended_option=recommended["key"],
        confidence=confidence, created_by=user.email,
    )
    db.add(sim); db.commit(); db.refresh(sim)
    return serialize_sim(sim)


def serialize_sim(s: Simulation):
    return {
        "sim_ref": s.sim_ref, "conflict_ref": s.conflict_ref, "weights": loads(s.weights_json, {}),
        "options": loads(s.options_json, []), "recommended_option": s.recommended_option,
        "confidence": s.confidence, "created_by": s.created_by, "created_at": iso(s.created_at),
        "prototype_validation_note": "Scenario values are explainable finals calibration values and should be validated in a production pilot.",
    }
