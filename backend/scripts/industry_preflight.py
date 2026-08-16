from __future__ import annotations
import argparse
import os
import socket
import subprocess
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
        passed.append(ok('Service health',health.status_code==200 and hj.get('version')=='5.5.0',hj.get('version','?')))
        passed.append(ok('Security headers',health.headers.get('x-frame-options')=='DENY' and bool(health.headers.get('content-security-policy'))))
        from app.core.config import get_settings
        settings=get_settings()
        old_markers=('juristwin-finals-local-secret-change-me','juristwin-finals-webhook-secret','juristwin-finals-proof-signing-secret')
        secret_ok=all(len(v)>=32 and not any(m in v for m in old_markers) for v in (settings.SECRET_KEY,settings.WEBHOOK_SECRET,settings.PROOF_SIGNING_SECRET))
        passed.append(ok('Runtime secret hygiene',secret_ok,settings.SECURITY_SECRET_MODE))
        # Execute the port chooser while deliberately occupying a requested start port. This proves
        # the finals launcher can recover from the exact clean-clone port collision found in assessment.
        hold=socket.socket(socket.AF_INET,socket.SOCK_STREAM);hold.bind(('127.0.0.1',0));hold.listen(1);busy=hold.getsockname()[1]
        env=dict(os.environ);env['JURISTWIN_PORT']=str(busy)
        choice=subprocess.check_output([sys.executable,str(BACKEND_DIR/'scripts'/'choose_port.py')],env=env,text=True).strip()
        hold.close()
        port_ok=choice.isdigit() and int(choice)!=busy
        passed.append(ok('Automatic port failover',port_ok,f"busy={busy} → selected={choice}"))
        finals=c.get('/finals')
        frontend_ok=finals.status_code==200 and '/static/sentinel.css?v=5.5.0' in finals.text and '/static/sentinel.js?v=5.5.0' in finals.text
        passed.append(ok('Pitch-aligned JurisTech frontend',frontend_ok,'responsive SPA assets served'))
        ready=c.get('/api/system/readiness',headers=h).json()
        passed.append(ok('Readiness proof',ready.get('status')=='READY' and ready.get('score')==100,f"{ready.get('score')}%"))
        model=c.get('/api/live/ai-model',headers=h).json()
        bench=model.get('held_out_development_benchmark',{})
        passed.append(ok('Hybrid learned AI',model.get('learned_component') is True and bench.get('domain_macro_f1',0)>=0.85 and bench.get('stance_macro_f1',0)>=0.85,f"domain F1={bench.get('domain_macro_f1')} · stance F1={bench.get('stance_macro_f1')}"))
        answer=c.post('/api/memory/answer',headers=h,json={'question':'Can gig workers use bank statements as income evidence?','preview_role':'manager'}).json()
        passed.append(ok('Track 2 verified answer',answer.get('status')=='CONFLICT_PRESENT' and answer.get('rule_key')=='income_document_rule' and len(answer.get('citations',[]))>=1,f"{answer.get('status')} · {len(answer.get('citations',[]))} citation(s)"))
        conflict=c.get('/api/conflicts/CF-INCOME-001',headers=h).json()
        plain=conflict.get('plain_explanation',{})
        clarity_ok=bool(plain.get('canonical',{}).get('message')) and len(plain.get('conflicting_evidence',[]))>=2 and 'two different answers' in plain.get('why_it_matters','').lower()
        passed.append(ok('Judge clarity — exact conflict messages',clarity_ok,'approved vs conflicting evidence + plain-English impact'))
        sim=c.post('/api/simulations/conflict/CF-INCOME-001/run',headers=h,json={}).json()
        cert=sim.get('analysis',{}).get('decision_certificate',{})
        passed.append(ok('Twin robustness certificate',cert.get('status')=='ROBUST',f"stability={cert.get('sensitivity_stability_pct')}%"))
        simple=sim.get('analysis',{}).get('plain_language',{})
        rec_ok='organisation' in simple.get('headline','').lower() and 'one document' in simple.get('why_not_b','').lower() and len(simple.get('reasons',[]))>=3
        passed.append(ok('Judge clarity — recommendation rationale',rec_ok,'Why not A / Why not B / Why C exposed before technical proof'))
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
        proof=pack.get('proof',{})
        verified=c.post('/api/assurance/verify-proof',headers=h,json={'bundle_digest':proof.get('bundle_digest'),'signature':proof.get('signature')}).json()
        passed.append(ok('Live Proof verification',verified.get('valid') is True,'digest + HMAC signature verified through API'))
        passed.append(ok('Ledger verification',pack.get('ledger',{}).get('verified') is True,f"{pack.get('ledger',{}).get('entries',0)} entries"))
        inv=c.get('/api/assurance/invariants',headers=h).json()
        passed.append(ok('Operational invariants',inv.get('status')=='HEALTHY'))
        overview=c.get('/api/assurance/overview',headers=h).json()
        passed.append(ok('Runtime telemetry',overview.get('telemetry',{}).get('requests',0)>0,f"p95={overview.get('telemetry',{}).get('latency_ms',{}).get('p95',0)}ms"))
        # Leave finals database clean and deterministic after preflight.
        c.post('/api/demo/reset',headers=h)
        marker=BACKEND_DIR.parent/'.juristwin_port'
        if marker.exists(): marker.unlink()

    score=round(100*sum(passed)/max(1,len(passed)))
    if not args.ci:
        print('\nJURISTWIN CHAMPIONSHIP PREFLIGHT')
        print(f"{sum(passed)}/{len(passed)} controls passed · {score}%")
    return 0 if all(passed) else 2


if __name__=='__main__':
    sys.exit(main())
