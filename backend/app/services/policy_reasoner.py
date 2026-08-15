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
    ("LOAN_RESTRUCTURE", [r"loan restructur(?:e|ing)", r"term extension", r"repayment restructur"]),
    ("CUSTOMER_NOTIFICATION", [r"customer notifications?", r"customer notice", r"notify (?:the )?customer"]),
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
        "engine": "JurisTwin Policy Atom Reasoner v3",
    }
