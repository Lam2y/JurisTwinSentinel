from __future__ import annotations

import hashlib
import math
import random

DEFAULT_WEIGHTS = {"delay": 0.40, "complaint": 0.35, "alignment": 0.25}

SCENARIO_PROFILES = {
    "income_document_rule": {
        "label": "Income-document eligibility",
        "options": {
            "A": {"name": "TAKE NO ACTION", "summary": "Keep the current process unchanged."},
            "B": {"name": "UPDATE ONE SOURCE", "summary": "Correct the main policy artefact only."},
            "C": {"name": "ALIGN COMPLETE PROCESS", "summary": "Align policy, frontline guidance, exposed cases and QA controls."},
        },
        "base": {
            "A": {"delay": 4.2, "complaint": 64, "affected": 27, "duplicates": 19, "alignment": 41},
            "B": {"delay": 2.7, "complaint": 39, "affected": 14, "duplicates": 8, "alignment": 71},
            "C": {"delay": 1.1, "complaint": 17, "affected": 2, "duplicates": 1, "alignment": 96},
        },
        "recommended_title": "Align the complete process — not just one document.",
        "actions": ["Update governed rule", "Notify officers", "Review exposed cases", "Update QA", "Block legacy behaviour"],
    },
    "loan_restructure_rule": {
        "label": "Loan restructuring approval",
        "options": {
            "A": {"name": "TAKE NO ACTION", "summary": "Leave the competing threshold in circulation."},
            "B": {"name": "SYNC THRESHOLD ONLY", "summary": "Update the threshold but leave historical cases and controls unchanged."},
            "C": {"name": "ALIGN + RECALCULATE", "summary": "Synchronise the threshold, re-evaluate exposed cases and update controls."},
        },
        "base": {
            "A": {"delay": 3.8, "complaint": 48, "affected": 11, "duplicates": 7, "alignment": 46},
            "B": {"delay": 2.2, "complaint": 31, "affected": 6, "duplicates": 3, "alignment": 75},
            "C": {"delay": 0.9, "complaint": 13, "affected": 1, "duplicates": 0, "alignment": 97},
        },
        "recommended_title": "Synchronise the threshold and recalculate every exposed case.",
        "actions": ["Sync risk threshold", "Recalculate exposed cases", "Notify Risk Ops", "Update QA", "Block legacy threshold"],
    },
    "notification_deadline": {
        "label": "Customer notification deadline",
        "options": {
            "A": {"name": "TAKE NO ACTION", "summary": "Leave calendar-day and business-day logic unresolved."},
            "B": {"name": "UPDATE SCHEDULER ONLY", "summary": "Fix automation but leave manual guidance and exposed notices unchanged."},
            "C": {"name": "ALIGN SLA + OPERATIONS", "summary": "Align the SLA, scheduler, operating guidance and exposed notices."},
        },
        "base": {
            "A": {"delay": 3.0, "complaint": 36, "affected": 6, "duplicates": 4, "alignment": 52},
            "B": {"delay": 1.8, "complaint": 22, "affected": 3, "duplicates": 2, "alignment": 79},
            "C": {"delay": 0.7, "complaint": 8, "affected": 1, "duplicates": 0, "alignment": 98},
        },
        "recommended_title": "Align the SLA definition, scheduler and frontline guidance.",
        "actions": ["Update scheduler", "Update guidance", "Review affected notices", "Notify Operations", "Block calendar-day rule"],
    },
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _normalize(weights: dict | None) -> dict[str, float]:
    merged = {**DEFAULT_WEIGHTS, **(weights or {})}
    total = sum(max(float(v), 0.0) for v in merged.values()) or 1.0
    return {k: max(float(v), 0.0) / total for k, v in merged.items()}


def _loss(option: dict, weights: dict) -> float:
    return (
        weights["delay"] * min(option["predicted_delay_days"] / 5.0, 1.0)
        + weights["complaint"] * (option["complaint_probability"] / 100.0)
        + weights["alignment"] * (1.0 - option["policy_alignment"] / 100.0)
    )


def _score(key: str, option_def: dict, base: dict, weights: dict) -> dict:
    b = base[key]
    dd = weights["delay"] - DEFAULT_WEIGHTS["delay"]
    dc = weights["complaint"] - DEFAULT_WEIGHTS["complaint"]
    da = weights["alignment"] - DEFAULT_WEIGHTS["alignment"]
    intensity = {"A": 0.15, "B": 0.72, "C": 1.0}[key]
    delay = b["delay"] * (1 - 0.55 * dd * intensity + 0.28 * dc * intensity + 0.34 * da * intensity)
    complaint = b["complaint"] * (1 + 0.30 * dd * intensity - 0.62 * dc * intensity - 0.18 * da * intensity)
    alignment = b["alignment"] + (30 * da - 11 * dd + 8 * dc) * intensity
    duplicates = b["duplicates"] * (1 + 0.18 * dd * intensity - 0.40 * dc * intensity - 0.16 * da * intensity)
    affected = b["affected"] * (1 + 0.08 * dd * intensity - 0.14 * dc * intensity - 0.10 * da * intensity)
    result = {
        "key": key,
        "name": option_def["name"],
        "summary": option_def["summary"],
        "predicted_delay_days": round(_clamp(delay, 0.5, 6.0), 1),
        "complaint_probability": round(_clamp(complaint, 5, 90)),
        "applications_affected": int(round(_clamp(affected, 1, 40))),
        "duplicate_requests": int(round(_clamp(duplicates, 0, 30))),
        "policy_alignment": round(_clamp(alignment, 25, 99)),
    }
    result["decision_loss"] = round(_loss(result, weights), 4)
    result["decision_fit"] = round((1 - result["decision_loss"]) * 100, 1)
    return result


def _percentile(values: list[float], p: float) -> float:
    xs = sorted(values)
    if not xs:
        return 0.0
    pos = (len(xs) - 1) * p
    low = math.floor(pos)
    high = math.ceil(pos)
    if low == high:
        return xs[low]
    return xs[low] * (high - pos) + xs[high] * (pos - low)


def _uncertainty(option: dict, weights: dict, rng: random.Random, samples: int = 500) -> dict:
    delays, complaints, alignments, losses = [], [], [], []
    spread = {"A": 1.0, "B": 0.78, "C": 0.58}[option["key"]]
    for _ in range(samples):
        delay = _clamp(rng.gauss(option["predicted_delay_days"], 0.38 * spread), 0.3, 7.0)
        complaint = _clamp(rng.gauss(option["complaint_probability"], 6.5 * spread), 1, 99)
        alignment = _clamp(rng.gauss(option["policy_alignment"], 5.2 * spread), 1, 100)
        loss = _loss({"predicted_delay_days": delay, "complaint_probability": complaint, "policy_alignment": alignment}, weights)
        delays.append(delay)
        complaints.append(complaint)
        alignments.append(alignment)
        losses.append(loss)
    return {
        "samples": samples,
        "delay_days_p10_p50_p90": [round(_percentile(delays, p), 2) for p in (0.10, 0.50, 0.90)],
        "complaint_pct_p10_p50_p90": [round(_percentile(complaints, p), 1) for p in (0.10, 0.50, 0.90)],
        "alignment_pct_p10_p50_p90": [round(_percentile(alignments, p), 1) for p in (0.10, 0.50, 0.90)],
        "fit_pct_p10_p50_p90": [round((1 - _percentile(losses, p)) * 100, 1) for p in (0.90, 0.50, 0.10)],
    }


def _sensitivity(weights: dict, options_def: dict, base: dict) -> list[dict]:
    base_options = [_score(k, v, base, weights) for k, v in options_def.items()]
    base_rec = min(base_options, key=lambda x: x["decision_loss"])["key"]
    rows = []
    for driver in DEFAULT_WEIGHTS:
        for delta in (-0.10, 0.10):
            trial = dict(weights)
            trial[driver] = max(0.01, trial[driver] + delta)
            trial = _normalize(trial)
            options = [_score(k, v, base, trial) for k, v in options_def.items()]
            rec = min(options, key=lambda x: x["decision_loss"])
            rows.append({
                "driver": driver,
                "direction": "+10pp" if delta > 0 else "-10pp",
                "recommended_option": rec["key"],
                "recommended_fit": rec["decision_fit"],
                "recommendation_changed": rec["key"] != base_rec,
            })
    return rows


def _pareto(options: list[dict]) -> list[str]:
    frontier = []
    for a in options:
        dominated = False
        for b in options:
            if a["key"] == b["key"]:
                continue
            no_worse = (
                b["predicted_delay_days"] <= a["predicted_delay_days"]
                and b["complaint_probability"] <= a["complaint_probability"]
                and b["policy_alignment"] >= a["policy_alignment"]
            )
            strictly_better = (
                b["predicted_delay_days"] < a["predicted_delay_days"]
                or b["complaint_probability"] < a["complaint_probability"]
                or b["policy_alignment"] > a["policy_alignment"]
            )
            if no_worse and strictly_better:
                dominated = True
                break
        if not dominated:
            frontier.append(a["key"])
    return frontier


def run_decision_twin(rule_key: str, weights: dict | None = None) -> dict:
    profile = SCENARIO_PROFILES.get(rule_key)
    if not profile:
        raise ValueError("No Digital Twin profile is configured for this policy domain.")
    weights = _normalize(weights)
    options = [_score(k, v, profile["base"], weights) for k, v in profile["options"].items()]
    recommended = min(options, key=lambda x: x["decision_loss"])

    seed_text = rule_key + repr(sorted(weights.items()))
    rng = random.Random(int(hashlib.sha256(seed_text.encode()).hexdigest()[:12], 16))
    for option in options:
        option["uncertainty"] = _uncertainty(option, weights, rng, 500)

    sensitivity = _sensitivity(weights, profile["options"], profile["base"])
    changed = sum(1 for row in sensitivity if row["recommendation_changed"])
    stability = round(100 * (1 - changed / max(1, len(sensitivity))), 1)
    fits = sorted([o["decision_fit"] for o in options], reverse=True)
    fit_margin = round(fits[0] - fits[1], 1) if len(fits) > 1 else 0.0
    frontier = _pareto(options)
    p10 = next(o["uncertainty"]["fit_pct_p10_p50_p90"][0] for o in options if o["key"] == recommended["key"])
    certificate = {
        "recommended_option": recommended["key"],
        "pareto_frontier": frontier,
        "pareto_optimal": recommended["key"] in frontier,
        "worst_case_fit_p10": p10,
        "sensitivity_stability_pct": stability,
        "fit_margin": fit_margin,
        "status": "ROBUST" if recommended["key"] in frontier and stability >= 80 and p10 >= 70 else "REVIEW",
    }
    return {
        "engine": "JurisTwin White-Box Decision Digital Twin v11",
        "method": "transparent operational coefficients + deterministic 1,500-scenario Monte Carlo stress test + sensitivity analysis + Pareto certificate",
        "scenario_profile": rule_key,
        "scenario_label": profile["label"],
        "scenario_count": 1500,
        "weights": weights,
        "options": options,
        "recommended_option": recommended["key"],
        "recommended_title": profile["recommended_title"],
        "recommended_actions": profile["actions"],
        "decision_certificate": certificate,
        "sensitivity": sensitivity,
        "validation_note": "Prototype-calibrated white-box operational assumptions, not a trained production forecast. Monte Carlo, sensitivity and Pareto analysis test whether the recommendation remains robust when assumptions move.",
    }
