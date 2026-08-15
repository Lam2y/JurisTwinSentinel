from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR=Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0,str(BACKEND_DIR))
from fastapi.testclient import TestClient

from app.main import app


def ok(label, condition, detail=""):
    mark="PASS" if condition else "FAIL"
    print(f"[{mark}] {label}" + (f" — {detail}" if detail else ""))
    return bool(condition)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--ci', action='store_true', help='compact output suitable for CI')
    args=parser.parse_args()
    passed=[]
    with TestClient(app) as c:
        login=c.post('/api/auth/login',json={'email':'operations@regulatedbank.com','password':'Finals2026!'})
        passed.append(ok('Authentication',login.status_code==200,f"HTTP {login.status_code}"))
        if login.status_code!=200:
            return 1
        h={'Authorization':f"Bearer {login.json()['access_token']}"}
        reset=c.post('/api/demo/reset',headers=h)
        passed.append(ok('Deterministic reset',reset.status_code==200))
        health=c.get('/api/system/health',headers=h)
        hj=health.json()
        passed.append(ok('Service health',health.status_code==200 and hj.get('version')=='5.3.0',hj.get('version','?')))
        passed.append(ok('Security headers',health.headers.get('x-frame-options')=='DENY' and bool(health.headers.get('content-security-policy'))))
        finals=c.get('/finals')
        frontend_ok=finals.status_code==200 and '/static/sentinel.css?v=5.3.0' in finals.text and '/static/sentinel.js?v=5.3.0' in finals.text
        passed.append(ok('Pitch-aligned JurisTech frontend',frontend_ok,'responsive SPA assets served'))
        ready=c.get('/api/system/readiness',headers=h).json()
        passed.append(ok('Readiness proof',ready.get('status')=='READY' and ready.get('score')==100,f"{ready.get('score')}%"))
        sim=c.post('/api/simulations/conflict/CF-INCOME-001/run',headers=h,json={}).json()
        cert=sim.get('analysis',{}).get('decision_certificate',{})
        passed.append(ok('Twin robustness certificate',cert.get('status')=='ROBUST',f"stability={cert.get('sensitivity_stability_pct')}%"))
        gate=c.get('/api/assurance/governance-gate/CF-INCOME-001',headers=h).json()
        passed.append(ok('Governance gate',gate.get('status')=='PASS' and gate.get('score')==100,f"{gate.get('score')}%"))
        attack=c.post('/api/live/red-team',headers=h,json={}).json()
        passed.append(ok('Adversarial harness',attack.get('status')=='HARDENED' and attack.get('score')==100,f"{attack.get('passed')}/{attack.get('total')}"))
        challenge=c.post('/api/live/challenge',headers=h,json={
            'source':'CI Unseen Evidence','title':'Unseen policy probe',
            'body':'Effective immediately, bank statements are no longer accepted. Officers must request payslips from gig workers.',
            'authority':'External CI probe','authority_level':2,'sensitivity':'internal'
        }).json()
        passed.append(ok('Unseen evidence reasoning',challenge.get('verdict')=='CONTRADICTION',challenge.get('challenge_ref','')))
        passed.append(ok('Explainable blast radius',challenge.get('blast_radius')==27,'27 cases'))
        pack=c.get('/api/assurance/proof-pack',headers=h).json()
        passed.append(ok('Proof Pack digest',len(pack.get('proof',{}).get('bundle_digest',''))==64,pack.get('status','')))
        passed.append(ok('Ledger verification',pack.get('ledger',{}).get('verified') is True,f"{pack.get('ledger',{}).get('entries',0)} entries"))
        inv=c.get('/api/assurance/invariants',headers=h).json()
        passed.append(ok('Operational invariants',inv.get('status')=='HEALTHY'))
        overview=c.get('/api/assurance/overview',headers=h).json()
        passed.append(ok('Runtime telemetry',overview.get('telemetry',{}).get('requests',0)>0,f"p95={overview.get('telemetry',{}).get('latency_ms',{}).get('p95',0)}ms"))
        # Leave finals database clean and deterministic after preflight.
        c.post('/api/demo/reset',headers=h)

    score=round(100*sum(passed)/max(1,len(passed)))
    if not args.ci:
        print('\nJURISTWIN CHAMPIONSHIP PREFLIGHT')
        print(f"{sum(passed)}/{len(passed)} controls passed · {score}%")
    return 0 if all(passed) else 2


if __name__=='__main__':
    sys.exit(main())
