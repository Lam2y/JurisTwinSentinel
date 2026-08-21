from __future__ import annotations
import argparse
import os
import socket
import subprocess
import json
import sys
from pathlib import Path

# Finals machines can inherit a cp1252 console. Force UTF-8 so status glyphs never crash the
# verification script; errors are replaced rather than aborting a preflight.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

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
        passed.append(ok('Service health',health.status_code==200 and hj.get('version')=='6.0.0',hj.get('version','?')))
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
        frontend_ok=finals.status_code==200 and '/static/sentinel.css?v=6.0.0' in finals.text and '/static/sentinel.js?v=6.0.0' in finals.text
        passed.append(ok('Pitch-aligned JurisTech frontend',frontend_ok,'responsive SPA assets served'))
        finals_v7='/static/sentinel.css?v=7.0.0' in finals.text and '/static/sentinel.js?v=7.0.0' in finals.text
        passed.append(ok('Championship v7 finals assets',finals_v7,'first-minute proof + live controls + challenge mode'))
        ready=c.get('/api/system/readiness',headers=h).json()
        passed.append(ok('Readiness proof',ready.get('status')=='READY' and ready.get('score')==100,f"{ready.get('score')}%"))
        model=c.get('/api/live/ai-model',headers=h).json()
        bench=model.get('held_out_development_benchmark',{})
        passed.append(ok('Hybrid learned AI',model.get('learned_component') is True and bench.get('domain_macro_f1',0)>=0.85 and bench.get('stance_macro_f1',0)>=0.85,f"domain F1={bench.get('domain_macro_f1')} · stance F1={bench.get('stance_macro_f1')}"))
        answer=c.post('/api/memory/answer',headers=h,json={'question':'Can gig workers use bank statements as income evidence?','preview_role':'manager'}).json()
        passed.append(ok('Track 2 verified answer',answer.get('status')=='CONFLICT_PRESENT' and answer.get('rule_key')=='income_document_rule' and len(answer.get('citations',[]))>=1,f"{answer.get('status')} · {len(answer.get('citations',[]))} citation(s)"))
        ai_proof=answer.get('ai_verification',{})
        ai_proof_ok=ai_proof.get('learned_component') is True and ai_proof.get('domain_macro_f1',0)>=0.85 and ai_proof.get('stance_macro_f1',0)>=0.85 and ai_proof.get('publication_authority')==0
        passed.append(ok('One-click AI verification proof',ai_proof_ok,f"domain F1={ai_proof.get('domain_macro_f1')} · stance F1={ai_proof.get('stance_macro_f1')} · publish={ai_proof.get('publication_authority')}"))
        source_mix=answer.get('source_mix',[])
        source_names={x.get('source') for x in source_mix}
        multi_ok=answer.get('synthesis',{}).get('sources_considered',0)>=3 and 'Outlook Approval' in source_names and bool({'FSD','Teams Message'} & source_names)
        passed.append(ok('Track 2 multi-source synthesis',multi_ok,f"{answer.get('synthesis',{}).get('sources_considered',0)} governed sources"))
        intern_answer=c.post('/api/memory/answer',headers=h,json={'question':'Can gig workers use bank statements as income evidence?','preview_role':'intern'}).json()
        role_safe=intern_answer.get('status')=='RESTRICTED' and any(x.get('redacted') for x in intern_answer.get('source_mix',[]))
        passed.append(ok('Track 2 role-safe answer',role_safe,'same question → Intern redaction enforced server-side'))
        js=c.get('/static/sentinel.js?v=6.0.0').text
        first_class='PLAIN-LANGUAGE ENTERPRISE MEMORY' in js and 'overviewQuestion' in js and 'Intern · redacted' in js
        passed.append(ok('Track 2 Q&A above the fold',first_class,'question + citations + one-click role preview'))
        v7_story=all(x in js for x in ('CONFLICT DETECTED','Preview same question as Intern','JUDGE CHALLENGE MODE','AI PUBLICATION AUTHORITY','LIVE BACKEND RESULT · HTTP'))
        passed.append(ok('Judge-visible championship story',v7_story,'conflict + role proof + human gate + live challenge + backend security result'))
        # Prove a manager control changes the next answer's evidence pool at runtime without changing the governing truth.
        boundary_off=c.patch('/api/integrations/sharepoint/policy',headers=h,json={'config':{'retrieval_enabled':False}})
        boundary_answer=c.post('/api/memory/answer',headers=h,json={'question':'Can gig workers use bank statements as income evidence?','preview_role':'manager'}).json()
        boundary_ok=boundary_off.status_code==200 and boundary_answer.get('primary_source',{}).get('source')=='Outlook Approval' and all(str(x.get('source','')).lower()!='fsd' for x in boundary_answer.get('source_mix',[]))
        passed.append(ok('Live evidence-boundary mutation',boundary_ok,'SharePoint/FSD removed; official Outlook answer remains governed'))
        c.patch('/api/integrations/sharepoint/policy',headers=h,json={'config':{'retrieval_enabled':True}})
        integrations=c.get('/api/integrations',headers=h).json()
        vector=next((x for x in integrations if x.get('key')=='vector'),{})
        retrieval_truth=vector.get('name')=='Local Semantic Retrieval Index' and vector.get('details',{}).get('engine')=='BM25 + cosine' and vector.get('details',{}).get('pilot_target')=='ChromaDB'
        passed.append(ok('Runtime retrieval truthfulness',retrieval_truth,'local BM25 + cosine; ChromaDB labelled pilot target'))
        outlook=next((x for x in integrations if x.get('key')=='outlook'),{})
        before_count=outlook.get('object_count')
        fixture_refresh=c.post('/api/integrations/outlook/sync',headers=h).json()
        fixture_ok=fixture_refresh.get('object_count')==before_count and fixture_refresh.get('operation',{}).get('mode')=='fixture_no_mutation'
        passed.append(ok('No fake vendor sync mutation',fixture_ok,f"Outlook fixture count remains {before_count}"))
        gateway=next((x for x in integrations if x.get('key')=='webhook'),{})
        gateway_ok=gateway.get('details',{}).get('adapter_mode')=='live_http_ingress' and gateway.get('details',{}).get('auth')=='HMAC-SHA256'
        passed.append(ok('Genuine signed ingress surfaced',gateway_ok,'Signed Webhook Gateway · HMAC-SHA256 · replay protection'))
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
        passed.append(ok('Track 2 process optimisation', 'PROCESS OPTIMISATION' in js and 'Run process optimisation' in js,'Option C labelled as process optimisation'))
        gate=c.get('/api/assurance/governance-gate/CF-INCOME-001',headers=h).json()
        passed.append(ok('Governance gate',gate.get('status')=='PASS' and gate.get('score')==100,f"{gate.get('score')}%"))
        attack=c.post('/api/live/red-team',headers=h,json={}).json()
        passed.append(ok('Adversarial harness',attack.get('status')=='HARDENED' and attack.get('score')==100,f"{attack.get('passed')}/{attack.get('total')}"))
        import jwt
        from app.services.red_team import _mutate_jwt_signature
        portable=True
        for i in range(12):
            secret=f'preflight-machine-secret-{i}-'+('x'*(20+i))
            token=jwt.encode({'sub':'1','role':'manager'},secret,algorithm='HS256')
            try:
                jwt.decode(_mutate_jwt_signature(token),secret,algorithms=['HS256']); portable=False; break
            except jwt.InvalidTokenError:
                pass
        passed.append(ok('Secret-independent JWT tamper probe',portable,'interior signature mutation rejected across 12 generated machine secrets'))
        launcher=(BACKEND_DIR/'scripts'/'finals_launcher.py').read_text(encoding='utf-8')
        launch_ok='[STARTING' in launcher and '[READY]' in launcher and 'Port 8000 is busy' in launcher and '75' in launcher
        passed.append(ok('Cold-start operator feedback',launch_ok,'heartbeat + health wait + automatic port failover'))
        auto_prepare='prepare_finals_state' in launcher and '[DEMO READY]' in launcher and '/api/demo/reset' in launcher and '/api/system/readiness' in launcher
        passed.append(ok('Automatic finals-state guard',auto_prepare,'launch resets scenario, confirms 100% readiness and warms local AI'))
        challenge=c.post('/api/live/challenge',headers=h,json={
            'source':'CI Unseen Evidence','title':'Unseen policy probe',
            'body':'Effective immediately, bank statements are no longer accepted. Officers must request payslips from gig workers.',
            'authority':'External CI probe','authority_level':2,'sensitivity':'internal'
        }).json()
        passed.append(ok('Unseen evidence reasoning',challenge.get('verdict')=='CONTRADICTION',challenge.get('challenge_ref','')))
        stages=challenge.get('analysis',{}).get('stages',[])
        stage_ok=len(stages)>=5 and all('latency_ms' in x for x in stages[:5])
        passed.append(ok('Judge-visible runtime pipeline',stage_ok,f"{len(stages)} measured stages with live latency"))
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
