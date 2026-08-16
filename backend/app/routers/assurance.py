from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..core.security import current_user, require_capability
from ..db.database import get_db
from ..db.models import Conflict, CustomerCase, DecisionContract, Evidence, Integration, LiveChallenge, SecurityAlert, User
from ..services.assurance import governance_gate, invariant_report, progressive_rollout_plan, decision_replay, proof_pack, verify_proof_signature
from ..services.observability import telemetry
from ..schemas import ProofVerifyRequest

router = APIRouter(prefix="/assurance", tags=["assurance"])


@router.get("/overview")
def overview(db: Session = Depends(get_db), user: User = Depends(current_user)):
    metrics=telemetry.snapshot()
    inv=invariant_report(db)
    gate=governance_gate(db,"CF-INCOME-001")
    return {
        "status":"OPERATIONAL" if inv["status"]=="HEALTHY" else "DEGRADED",
        "platform":"JurisTwin Sentinel Championship v5.5",
        "telemetry":metrics,
        "invariants":inv,
        "flagship_governance_gate":gate,
        "estate":{
            "cases":db.execute(select(func.count(CustomerCase.id))).scalar_one(),
            "evidence":db.execute(select(func.count(Evidence.id))).scalar_one(),
            "decisions":db.execute(select(func.count(DecisionContract.id))).scalar_one(),
            "live_challenges":db.execute(select(func.count(LiveChallenge.id))).scalar_one(),
            "open_security_alerts":db.execute(select(func.count(SecurityAlert.id)).where(SecurityAlert.status=='open')).scalar_one(),
            "connected_integrations":db.execute(select(func.count(Integration.id)).where(Integration.status=='connected')).scalar_one(),
        },
        "production_patterns":["request tracing","rate containment","security headers","governance gates","progressive rollout plan","decision replay","tamper-evident proof pack","offline-safe fallback"],
    }


@router.get("/governance-gate/{conflict_ref}")
def gate(conflict_ref: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    d=governance_gate(db, conflict_ref)
    if d.get('status')=='BLOCKED':
        raise HTTPException(404,d.get('reason','Conflict not found'))
    return d


@router.get("/invariants")
def invariants(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return invariant_report(db)


@router.get("/rollout-plan/{conflict_ref}")
def rollout_plan(conflict_ref: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    d=progressive_rollout_plan(db, conflict_ref)
    if d.get('status')=='BLOCKED':
        raise HTTPException(404,'Conflict not found')
    return d


@router.get("/replay/{decision_ref}")
def replay(decision_ref: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    d=decision_replay(db, decision_ref)
    if d.get('status')=='NOT_FOUND':
        raise HTTPException(404,'Decision contract not found')
    return d


@router.get("/proof-pack")
def get_proof_pack(
    conflict_ref: str = Query(default="CF-INCOME-001", max_length=80),
    decision_ref: str | None = Query(default=None, max_length=80),
    download: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    d=proof_pack(db, conflict_ref, decision_ref)
    if d.get('status')=='NOT_FOUND':
        raise HTTPException(404,'Conflict not found')
    headers={}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="juristwin-proof-pack-{conflict_ref}.json"'
    return JSONResponse(content=d, headers=headers)


@router.post("/verify-proof")
def verify_proof(body: ProofVerifyRequest, user: User = Depends(current_user)):
    digest = body.digest or body.bundle_digest
    if not digest:
        raise HTTPException(422, "Provide digest or bundle_digest from the proof pack")
    return verify_proof_signature(digest.lower(), body.signature.lower())
