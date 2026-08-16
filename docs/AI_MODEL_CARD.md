# JurisTwin Sentinel — Hybrid Policy AI Model Card

## Purpose

The learned component improves policy-domain and policy-stance recognition for unseen language. It is **not** the source of organisational truth and has no publication authority.

## Runtime model

- Engine: `JurisTwin Hybrid Policy Intelligence v1`
- Features: word TF-IDF 1–2 grams + character-window TF-IDF 3–5 grams
- Estimator: class-weighted Logistic Regression
- Tasks:
  - policy-domain classification
  - policy-stance classification
- Training corpus: 152 curated labelled development examples
- Internet required: no
- Retrained on startup: yes

## Deterministic held-out development benchmark

- Held-out samples: 31
- Domain accuracy: 0.9677
- Domain macro-F1: **0.9035**
- Stance accuracy: 0.9677
- Stance macro-F1: **0.9666**

These figures are a hackathon development benchmark, **not production validation**.

## Safety architecture

```text
Unseen evidence / question
        ↓
Learned domain + stance proposal
        ↓
confidence gate / abstention
        ↓
Policy Atom Reasoner
        ↓
authority + version checks
        ↓
Sentinel Authority-Weighted Hybrid Consensus
        ↓
conflict / aligned / needs-review verdict
        ↓
HUMAN GOVERNANCE required for publication
```

### The model cannot

- publish a decision;
- canonicalise new evidence;
- bypass RBAC/DLP;
- overwrite a Decision Contract;
- silently resolve disagreement with the symbolic verifier.

Low confidence or unresolved learned/symbolic disagreement causes abstention/review.

## Why this design is suitable for regulated decisions

JurisTwin uses ML where statistical generalisation is useful, but keeps policy authority, collision logic and publication controls inspectable. The system exposes probability distributions and model limits rather than hiding them behind a single generated answer.
