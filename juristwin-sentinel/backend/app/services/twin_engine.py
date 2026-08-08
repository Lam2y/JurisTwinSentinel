from uuid import uuid4
from sqlalchemy.orm import Session
from ..db.models import Conflict, Simulation, User
from .common import dumps, loads, iso

DEFAULT_WEIGHTS = {"delay": 0.40, "complaint": 0.35, "alignment": 0.25}
OPTIONS = {
    "A": {"name": "TAKE NO ACTION", "update_fsd": 0, "notify_officers": 0, "review_cases": 0, "update_qa": 0, "block_duplicates": 0},
    "B": {"name": "UPDATE FSD ONLY", "update_fsd": 1, "notify_officers": 0, "review_cases": 0, "update_qa": 0, "block_duplicates": 0},
    "C": {"name": "ALIGN COMPLETE PROCESS", "update_fsd": 1, "notify_officers": 1, "review_cases": 1, "update_qa": 1, "block_duplicates": 1},
}
BASE = {
    "A": {"delay":4.2,"complaint":64,"affected":27,"duplicates":19,"alignment":41},
    "B": {"delay":2.7,"complaint":39,"affected":14,"duplicates":8,"alignment":71},
    "C": {"delay":1.1,"complaint":17,"affected":2,"duplicates":1,"alignment":96},
}

def _clamp(v, lo, hi): return max(lo, min(hi, v))

def score_option(key: str, levers: dict, weights: dict):
    b = BASE[key]
    # The weights are operational resource priorities, not cosmetic scoring knobs.
    # Moving resources toward speed shortens rollout but sacrifices some validation;
    # complaint/alignment emphasis spends more time on review, communications and QA.
    dd = weights["delay"] - DEFAULT_WEIGHTS["delay"]
    dc = weights["complaint"] - DEFAULT_WEIGHTS["complaint"]
    da = weights["alignment"] - DEFAULT_WEIGHTS["alignment"]
    intensity = {"A":0.15,"B":0.72,"C":1.0}[key]
    delay = b["delay"] * (1 - 0.55*dd*intensity + 0.28*dc*intensity + 0.34*da*intensity)
    complaint = b["complaint"] * (1 + 0.30*dd*intensity - 0.62*dc*intensity - 0.18*da*intensity)
    alignment = b["alignment"] + (30*da - 11*dd + 8*dc)*intensity
    duplicates = b["duplicates"] * (1 + .18*dd*intensity - .40*dc*intensity - .16*da*intensity)
    affected = b["affected"] * (1 + .08*dd*intensity - .14*dc*intensity - .10*da*intensity)
    delay = round(_clamp(delay, .5, 6.0), 1)
    complaint = round(_clamp(complaint, 5, 90))
    alignment = round(_clamp(alignment, 25, 99))
    duplicates = int(round(_clamp(duplicates, 0, 30)))
    affected = int(round(_clamp(affected, 1, 40)))
    return {
        "key": key, "name": levers["name"], "levers": levers,
        "predicted_delay_days": delay, "complaint_probability": complaint,
        "applications_affected": affected, "duplicate_requests": duplicates,
        "policy_alignment": alignment,
        "explanation": {
            "delay": "Changes when resources are shifted toward rapid rollout versus deeper review and alignment.",
            "complaint": "Changes with proactive customer review, communications and duplicate-request blocking effort.",
            "alignment": "Changes with the amount of effort allocated to FSD, training, QA and human-instruction convergence.",
        },
    }

def run_simulation(db: Session, conflict: Conflict, user: User, weights: dict | None = None):
    weights = {**DEFAULT_WEIGHTS, **(weights or {})}
    total = sum(max(float(v), 0) for v in weights.values()) or 1
    weights = {k: max(float(v), 0)/total for k, v in weights.items()}
    options = [score_option(k, v, weights) for k, v in OPTIONS.items()]
    for o in options:
        normalized_delay = min(o["predicted_delay_days"] / 5, 1)
        normalized_complaint = o["complaint_probability"] / 100
        normalized_misalignment = 1 - (o["policy_alignment"] / 100)
        loss = weights["delay"]*normalized_delay + weights["complaint"]*normalized_complaint + weights["alignment"]*normalized_misalignment
        o["decision_loss"] = round(loss, 4)
        o["decision_fit"] = round((1-loss)*100, 1)
    recommended = min(options, key=lambda x: x["decision_loss"])
    confidence = round(min(0.97, 0.72 + conflict.confidence*0.15 + (recommended["policy_alignment"] / 100)*0.12), 3)
    sim = Simulation(sim_ref=f"SIM-{uuid4().hex[:6].upper()}", conflict_ref=conflict.conflict_ref,
                     weights_json=dumps(weights), options_json=dumps(options), recommended_option=recommended["key"],
                     confidence=confidence, created_by=user.email)
    db.add(sim); db.commit(); db.refresh(sim)
    return serialize_sim(sim)

def serialize_sim(s: Simulation):
    return {"sim_ref": s.sim_ref, "conflict_ref": s.conflict_ref, "weights": loads(s.weights_json, {}),
            "options": loads(s.options_json, []), "recommended_option": s.recommended_option,
            "confidence": s.confidence, "created_by": s.created_by, "created_at": iso(s.created_at),
            "prototype_validation_note": "White-box finals calibration: weight changes alter operational assumptions and recompute projected outcomes. Production coefficients require pilot validation."}
