"""JurisTwin v3 white-box policy reasoning engine.

Turns unstructured policy language into structured policy atoms and explains *why* two
statements collide. This is intentionally deterministic and inspectable for regulated use:
no hidden LLM call is required for a verdict.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, asdict


MODALITY_RANK = {"UNSPECIFIED": 0, "PERMITTED": 1, "REQUIRED": 2, "PROHIBITED": 3}

OBJECT_PATTERNS = [
    ("BANK_STATEMENT", [r"bank statements?", r"account statements?"]),
    ("PAYSLIP", [r"pay\s?slips?", r"salary slips?"]),
    ("INCOME_EVIDENCE", [r"income (?:proof|evidence|document)", r"proof of income"]),
    ("LOAN_RESTRUCTURE", [r"loan restructur(?:e|ing)", r"restructur(?:e|ing|ing desk)", r"term extension", r"repayment restructur", r"risk score.{0,25}(?:threshold|approval|restructur)"]),
    ("CUSTOMER_NOTIFICATION", [r"customer notifications?", r"customer notice", r"notify (?:the )?customer", r"notification deadline", r"adverse decision notices?", r"notification sla"]),
]

SUBJECT_PATTERNS = [
    ("GIG_WORKER", [r"gig workers?", r"freelancers?", r"self[- ]employed"]),
    ("OFFICER", [r"officers?", r"operations staff", r"agents?"]),
    ("CUSTOMER", [r"customers?", r"applicants?"]),
]

ACTION_PATTERNS = [
    ("ACCEPT", [r"accept(?:ed|able)?", r"valid", r"eligible"]),
    ("SUBMIT", [r"submit", r"provide", r"present"]),
    ("REQUEST", [r"request", r"ask for", r"collect"]),
    ("APPROVE", [r"approve(?:d|al)?", r"authori[sz]e"]),
    ("NOTIFY", [r"notify", r"inform", r"send .*notice"]),
]


def _first(patterns, text: str, default: str):
    for label, regs in patterns:
        if any(re.search(r, text, re.I) for r in regs):
            return label
    return default


def _modality(text: str, obj: str) -> tuple[str, list[str]]:
    t = text.lower()
    reasons = []
    prohibited = [
        r"no longer accept", r"not accept", r"cannot (?:be )?(?:use|accept|submit)",
        r"must not", r"prohibit", r"invalid", r"not permitted", r"not allowed",
    ]
    required = [
        r"must (?:provide|submit|request|use|be)", r"required", r"requires?",
        r"mandatory", r"compulsory", r"only (?:accept|use|submit|provide|request)",
    ]
    permitted = [
        r"may (?:be )?(?:accept|submit|use|provide)", r"can (?:be )?(?:accept|submit|use|provide)",
        r"accepted", r"permitted", r"allowed", r"acceptable", r"eligible",
    ]
    if any(re.search(p, t) for p in prohibited):
        reasons.append("Explicit prohibition/negation language detected.")
        return "PROHIBITED", reasons
    if any(re.search(p, t) for p in required):
        reasons.append("Mandatory/required modality detected.")
        return "REQUIRED", reasons
    if any(re.search(p, t) for p in permitted):
        reasons.append("Permission/acceptance modality detected.")
        return "PERMITTED", reasons
    reasons.append("No explicit deontic modality detected.")
    return "UNSPECIFIED", reasons


def _conditions(text: str) -> list[str]:
    out = []
    for m in re.finditer(r"\b(?:if|when|where|provided that|unless|for)\b\s+([^.;]{3,90})", text, re.I):
        value = m.group(0).strip()
        if value not in out:
            out.append(value)
    return out[:4]


def _effective(text: str) -> str | None:
    if re.search(r"\beffective immediately\b|\bwith immediate effect\b", text, re.I):
        return "IMMEDIATE"
    m = re.search(r"\b(?:effective|from|starting)\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})", text, re.I)
    return m.group(1) if m else None



NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10,
}

def _number(value: str) -> int | None:
    value = (value or "").lower().strip()
    if value.isdigit():
        return int(value)
    return NUMBER_WORDS.get(value)

def _parameters(text: str, obj: str) -> dict:
    """Extract structured numeric/temporal constraints for non-deontic policy collisions."""
    low = (text or "").lower()
    out = {}
    if obj == "LOAN_RESTRUCTURE":
        m = re.search(r"risk score(?:\s+(?:of|is|at|up to|<=|less than or equal to))?\s*(\d{1,3})", low)
        if m:
            out["risk_score_threshold"] = int(m.group(1))
            if re.search(r"(?:or below|maximum|max|up to|<=|not exceed)", low):
                out["risk_score_operator"] = "MAX"
    if obj == "CUSTOMER_NOTIFICATION":
        m = re.search(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|\d{1,2})[ -](business|working|calendar)[ -]days?\b", low)
        if m:
            out["deadline_days"] = _number(m.group(1))
            out["deadline_basis"] = "BUSINESS" if m.group(2) in {"business", "working"} else "CALENDAR"
        else:
            m = re.search(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|\d{1,2})\s+(business|working|calendar)\s+days?\b", low)
            if m:
                out["deadline_days"] = _number(m.group(1))
                out["deadline_basis"] = "BUSINESS" if m.group(2) in {"business", "working"} else "CALENDAR"
    return out

def extract_policy_atoms(text: str, rule_key: str | None = None) -> list[dict]:
    """Extract one or more normalized policy atoms from prose.

    Multiple objects are emitted separately so a sentence like "bank statements are prohibited;
    officers must request payslips" becomes two independently comparable obligations.
    """
    text = (text or "").strip()
    found_objects = []
    for label, regs in OBJECT_PATTERNS:
        if any(re.search(r, text, re.I) for r in regs):
            found_objects.append(label)
    if not found_objects:
        found_objects = ["GENERAL_POLICY"]
    subject = _first(SUBJECT_PATTERNS, text, "ORGANISATION")
    action = _first(ACTION_PATTERNS, text, "GOVERN")
    conditions = _conditions(text)
    effective = _effective(text)
    atoms = []
    for obj in found_objects[:4]:
        modality, reasons = _modality(text, obj)
        # Object-specific refinement for common mixed-modality sentences.
        low = text.lower()
        if obj == "BANK_STATEMENT":
            if re.search(r"bank statements?.{0,35}(?:no longer|not|cannot|prohibit|invalid)", low):
                modality = "PROHIBITED"
                reasons = ["Bank-statement clause contains explicit prohibition."]
            elif re.search(r"bank statements?.{0,40}(?:may|can|accepted|acceptable|allowed)", low):
                modality = "PERMITTED"
                reasons = ["Bank-statement clause contains explicit permission."]
        if obj == "PAYSLIP":
            if re.search(r"(?:must|mandatory|compulsory|only).{0,30}pay\s?slips?|pay\s?slips?.{0,30}(?:must|mandatory|compulsory|required)", low):
                modality = "REQUIRED"
                reasons = ["Payslip clause contains mandatory language."]
            elif re.search(r"pay\s?slips?.{0,25}(?:may|can|accepted|acceptable|allowed)", low):
                modality = "PERMITTED"
                reasons = ["Payslip clause contains explicit permission."]
            else:
                modality = "UNSPECIFIED"
                reasons = ["Payslip is referenced but no direct modality is asserted for it."]
        atoms.append({
            "subject": subject,
            "object": obj,
            "action": action,
            "modality": modality,
            "conditions": conditions,
            "effective": effective,
            "parameters": _parameters(text, obj),
            "rule_key": rule_key,
            "explanation": reasons,
        })
    return atoms


def compare_policy_atoms(canonical_atoms: list[dict], incoming_atoms: list[dict]) -> dict:
    """Return explainable collisions between normalized policy atoms."""
    collisions = []
    alignments = []
    for ca in canonical_atoms:
        for ia in incoming_atoms:
            same_object = ca["object"] == ia["object"] or "GENERAL_POLICY" in {ca["object"], ia["object"]}
            if not same_object:
                continue
            cm, im = ca["modality"], ia["modality"]
            collision = (
                {cm, im} == {"PERMITTED", "PROHIBITED"}
                or {cm, im} == {"REQUIRED", "PROHIBITED"}
            )
            if collision:
                collisions.append({
                    "type": "MODALITY_COLLISION",
                    "object": ia["object"],
                    "canonical_modality": cm,
                    "incoming_modality": im,
                    "explanation": f"{ia['object']} is {cm.lower()} by the canonical rule but {im.lower()} by the incoming evidence.",
                })
            elif cm != "UNSPECIFIED" and im != "UNSPECIFIED" and cm == im:
                alignments.append({
                    "type": "MODALITY_ALIGNMENT",
                    "object": ia["object"],
                    "modality": im,
                })
    # Structured-parameter collisions catch policy drift that is not a simple permission word.
    # Examples: risk threshold 60 vs 70, or business-day vs calendar-day deadlines.
    for ca in canonical_atoms:
        for ia in incoming_atoms:
            if ca.get("object") != ia.get("object"):
                continue
            cp, ip = ca.get("parameters") or {}, ia.get("parameters") or {}
            if ca.get("object") == "LOAN_RESTRUCTURE" and cp.get("risk_score_threshold") is not None and ip.get("risk_score_threshold") is not None and cp.get("risk_score_threshold") != ip.get("risk_score_threshold"):
                collisions.append({
                    "type": "NUMERIC_THRESHOLD_COLLISION", "object": "LOAN_RESTRUCTURE",
                    "canonical_modality": f"RISK_SCORE_MAX_{cp['risk_score_threshold']}",
                    "incoming_modality": f"RISK_SCORE_MAX_{ip['risk_score_threshold']}",
                    "explanation": f"The governed restructuring threshold is {cp['risk_score_threshold']} but incoming evidence uses {ip['risk_score_threshold']}.",
                })
            if ca.get("object") == "CUSTOMER_NOTIFICATION" and cp.get("deadline_basis") and ip.get("deadline_basis") and (cp.get("deadline_basis") != ip.get("deadline_basis") or cp.get("deadline_days") != ip.get("deadline_days")):
                collisions.append({
                    "type": "TEMPORAL_SEMANTICS_COLLISION", "object": "CUSTOMER_NOTIFICATION",
                    "canonical_modality": f"{cp.get('deadline_days')}_{cp.get('deadline_basis')}_DAYS",
                    "incoming_modality": f"{ip.get('deadline_days')}_{ip.get('deadline_basis')}_DAYS",
                    "explanation": f"The governed deadline is {cp.get('deadline_days')} {str(cp.get('deadline_basis')).lower()} days but incoming evidence uses {ip.get('deadline_days')} {str(ip.get('deadline_basis')).lower()} days.",
                })

    # Cross-object exclusivity: canonical bank statement permission versus incoming compulsory payslip.
    c_bank = any(a["object"] == "BANK_STATEMENT" and a["modality"] == "PERMITTED" for a in canonical_atoms)
    i_pay_req = any(a["object"] == "PAYSLIP" and a["modality"] == "REQUIRED" for a in incoming_atoms)
    i_bank_block = any(a["object"] == "BANK_STATEMENT" and a["modality"] == "PROHIBITED" for a in incoming_atoms)
    if c_bank and i_pay_req and not i_bank_block:
        collisions.append({
            "type": "EXCLUSIVITY_COLLISION",
            "object": "INCOME_EVIDENCE",
            "canonical_modality": "BANK_STATEMENT_PERMITTED",
            "incoming_modality": "PAYSLIP_REQUIRED",
            "explanation": "Incoming evidence makes payslips compulsory while canonical policy permits bank statements as an alternative.",
        })
    confidence = min(0.99, 0.78 + 0.07 * len(collisions)) if collisions else (0.88 if alignments else 0.55)
    return {
        "collision": bool(collisions),
        "collisions": collisions,
        "alignments": alignments,
        "confidence": round(confidence, 3),
        "engine": "JurisTwin Policy Atom Reasoner v4",
    }
