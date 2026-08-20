from __future__ import annotations

from collections import Counter
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Evidence, Integration
from .common import loads


def source_key(source: str | None) -> str | None:
    s=(source or '').lower()
    if 'teams' in s: return 'teams'
    if 'outlook' in s: return 'outlook'
    if 'gmail' in s: return 'gmail'
    if 'sharepoint' in s or 'fsd' in s: return 'sharepoint'
    if 'onedrive' in s: return 'onedrive'
    if 'clickup' in s: return 'clickup'
    if 'customer core' in s: return 'customer_core'
    if 'qa repository' in s: return 'qa'
    if 'decision ledger' in s: return 'postgres'
    if 'document vault' in s: return 'customer_core'
    return None


def integration_policy(db: Session, key: str | None) -> dict:
    if not key:
        return {
            'retrieval_enabled': True,
            'policy_authority_enabled': True,
            'scope_label': 'Governed internal source',
            'client_training_allowed': False,
        }
    row=db.execute(select(Integration).where(Integration.key==key)).scalar_one_or_none()
    if not row:
        return {
            'retrieval_enabled': True,
            'policy_authority_enabled': False,
            'scope_label': 'Unregistered source · context only',
            'client_training_allowed': False,
        }
    d=loads(row.details_json,{})
    return {
        'retrieval_enabled': bool(d.get('retrieval_enabled', True)),
        'policy_authority_enabled': bool(d.get('policy_authority_enabled', key not in {'customer_core','webhook'})),
        'scope_label': d.get('scope_label') or d.get('ingestion_scope') or 'Configured source scope',
        'channel_scope': d.get('channel_scope'),
        'personal_dm_allowed': bool(d.get('personal_dm_allowed', False)),
        'official_only': bool(d.get('official_only', False)),
        'allowed_channels': d.get('allowed_channels', []),
        'allowed_sender_roles': d.get('allowed_sender_roles', []),
        'allowed_libraries': d.get('allowed_libraries', []),
        'freshness_sla_minutes': d.get('freshness_sla_minutes'),
        'client_training_allowed': bool(d.get('client_training_allowed', False)),
        'status': row.status,
    }


def evidence_scope(db: Session, evidence: Evidence) -> dict:
    """Explain whether evidence may enter retrieval and policy-resolution paths.

    Scope controls are deliberately stricter than normal RBAC. They answer a different question:
    *should the connector ingest/index this class of content at all?*  A user being allowed to view a
    record never implies that personal DMs or casual mail may influence policy resolution.
    """
    key=source_key(evidence.source)
    policy=integration_policy(db,key)
    meta=loads(evidence.metadata_json,{})
    reasons=[]

    retrieval=bool(policy.get('retrieval_enabled',True)) and policy.get('status','connected')!='inactive'
    policy_authority=retrieval and bool(policy.get('policy_authority_enabled',False))

    if key=='teams':
        channel_type=str(meta.get('channel_type') or '').lower()
        is_personal=bool(meta.get('personal_dm')) or channel_type in {'personal_dm','dm','direct_message','1:1'}
        if is_personal and not policy.get('personal_dm_allowed',False):
            retrieval=False; policy_authority=False; reasons.append('Personal/1:1 Teams message blocked by privacy scope')
        elif channel_type and channel_type not in {'group_chat','channel','team_channel'}:
            retrieval=False; policy_authority=False; reasons.append('Only approved Teams group/channel conversations are indexed')
        else:
            allowed_channels=[str(x).strip().lower() for x in policy.get('allowed_channels',[]) if str(x).strip()]
            channel_name=str(meta.get('conversation_scope') or meta.get('channel_name') or meta.get('team_channel') or '').strip().lower()
            if allowed_channels and channel_name and not any(a in channel_name or channel_name in a for a in allowed_channels):
                retrieval=False; policy_authority=False; reasons.append('Teams group/channel is outside the administrator-approved channel list')
            elif allowed_channels and not channel_name:
                retrieval=False; policy_authority=False; reasons.append('Teams evidence has no approved group/channel identity')
            else:
                reasons.append('Teams group/channel scope allowed')

    if key in {'outlook','gmail'}:
        mail_class=str(meta.get('mail_classification') or '').lower()
        official=bool(meta.get('official_sender')) or mail_class in {'official_management','policy_approval','customer_service'}
        if policy.get('official_only') and not official:
            retrieval=False; policy_authority=False; reasons.append('Casual/unapproved mailbox traffic excluded')
        elif official:
            allowed_roles=[str(x).strip().lower() for x in policy.get('allowed_sender_roles',[]) if str(x).strip()]
            sender_role=str(meta.get('sender_role') or evidence.authority or '').strip().lower()
            if allowed_roles and sender_role and sender_role not in allowed_roles:
                retrieval=False; policy_authority=False; reasons.append('Official email sender role is outside the administrator-approved sender list')
            elif allowed_roles and not sender_role:
                retrieval=False; policy_authority=False; reasons.append('Official email has no approved sender-role identity')
            else:
                reasons.append('Official/approved mailbox scope allowed')
        if mail_class in {'customer_service','customer_message'}:
            # Customer communications can prove operational impact, never company policy authority.
            policy_authority=False; reasons.append('Customer communication is context-only, not policy authority')

    if key=='sharepoint':
        allowed_libraries=[str(x).strip().lower() for x in policy.get('allowed_libraries',[]) if str(x).strip()]
        library=str(meta.get('library') or '').strip().lower()
        if allowed_libraries and library not in allowed_libraries:
            retrieval=False; policy_authority=False; reasons.append('Document is outside the administrator-approved SharePoint libraries')
        elif allowed_libraries:
            reasons.append('Approved SharePoint library scope allowed')

    if key=='customer_core':
        policy_authority=False
        reasons.append('Customer data is operational impact only; never used to define policy')

    if meta.get('governance_use')=='context_only':
        policy_authority=False
        reasons.append('Evidence explicitly marked context-only')
    if meta.get('exclude_from_index') is True:
        retrieval=False; policy_authority=False
        reasons.append('Administrator excluded this content from the governed index')

    if evidence.superseded or str(evidence.status or '').lower() in {'superseded','outdated'}:
        policy_authority=False
        reasons.append('Superseded/outdated material cannot win a policy decision')

    return {
        'connector_key': key or 'internal',
        'retrieval_eligible': bool(retrieval),
        'policy_authority_eligible': bool(policy_authority),
        'client_training_allowed': False,  # hard boundary for bank/client data in this PoC
        'scope_label': policy.get('scope_label'),
        'reason': '; '.join(reasons) if reasons else 'Allowed by governed source scope',
    }


def eligible_policy_evidence(db: Session, rule_key: str) -> tuple[list[Evidence], list[dict]]:
    rows=db.execute(select(Evidence).where(Evidence.rule_key==rule_key).order_by(Evidence.id.desc())).scalars().all()
    allowed=[]; excluded=[]
    for e in rows:
        scope=evidence_scope(db,e)
        if scope['policy_authority_eligible']:
            allowed.append(e)
        else:
            excluded.append({'evidence_ref':e.evidence_ref,'source':e.source,'title':e.title,'reason':scope['reason']})
    return allowed, excluded


def resolve_by_authority_then_majority(db: Session, rule_key: str) -> dict:
    """Resolve policy safely: authority first, majority only inside the same authority tier.

    A majority of informal chat messages can never outvote one approved Product Owner/Compliance
    source. Majority is a fallback only when there is no active approved canonical record, and only
    among equally authoritative, scope-eligible evidence.
    """
    allowed, excluded=eligible_policy_evidence(db,rule_key)
    active=[e for e in allowed if not e.superseded and str(e.status or '').lower() not in {'superseded','outdated'}]
    approved=[e for e in active if bool(e.approved)]
    pool=approved or active
    if not pool:
        return {'winner':None,'support':[],'mode':'NO_ELIGIBLE_SOURCE','excluded':excluded,'eligible_count':0}

    top_level=max(int(e.authority_level or 0) for e in pool)
    top=[e for e in pool if int(e.authority_level or 0)==top_level]
    if len(top)==1:
        return {
            'winner':top[0], 'support':[top[0]],
            'mode':'APPROVED_AUTHORITY' if approved else 'HIGHEST_AUTHORITY',
            'authority_level':top_level,'eligible_count':len(active),'excluded':excluded,
            'majority':{'needed':False,'votes':1,'population':1},
        }

    # Same authority tier: identical claims count as a vote. Missing claim uses normalized body.
    def key(e:Evidence):
        return ' '.join((e.claim or e.body or '').lower().split())
    counts=Counter(key(e) for e in top)
    winning_key, votes=counts.most_common(1)[0]
    tied=sum(1 for _,v in counts.items() if v==votes)>1
    support=[e for e in top if key(e)==winning_key]
    if tied or votes <= len(top)/2:
        return {
            'winner':None,'support':support,'mode':'MAJORITY_TIE_REVIEW',
            'authority_level':top_level,'eligible_count':len(active),'excluded':excluded,
            'majority':{'needed':True,'votes':votes,'population':len(top),'tie':True},
        }
    support.sort(key=lambda e:(bool(e.approved),e.created_at,e.id),reverse=True)
    return {
        'winner':support[0],'support':support,'mode':'SAME_TIER_MAJORITY',
        'authority_level':top_level,'eligible_count':len(active),'excluded':excluded,
        'majority':{'needed':True,'votes':votes,'population':len(top),'tie':False},
    }
