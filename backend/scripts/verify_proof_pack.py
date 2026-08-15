from __future__ import annotations
import hashlib
import hmac
import json
import os
import sys
from pathlib import Path


def main(path: str):
    p=Path(path)
    data=json.loads(p.read_text(encoding='utf-8'))
    proof=data.get('proof') or {}
    claimed_digest=proof.get('bundle_digest','')
    claimed_signature=proof.get('signature','')
    clone=dict(data); clone.pop('proof',None); clone.pop('status',None)
    canonical=json.dumps(clone,sort_keys=True,separators=(',',':'),default=str)
    actual_digest=hashlib.sha256(canonical.encode()).hexdigest()
    secret=os.getenv('PROOF_SIGNING_SECRET','juristwin-finals-proof-signing-secret')
    expected_signature=hmac.new(secret.encode(),actual_digest.encode(),hashlib.sha256).hexdigest()
    digest_ok=hmac.compare_digest(actual_digest,claimed_digest)
    signature_ok=hmac.compare_digest(expected_signature,claimed_signature)
    print(f"Digest:    {'VALID' if digest_ok else 'INVALID'}")
    print(f"Signature: {'VALID' if signature_ok else 'INVALID'}")
    print(f"SHA-256:   {actual_digest}")
    return 0 if digest_ok and signature_ok else 2


if __name__=='__main__':
    if len(sys.argv)!=2:
        print('Usage: python backend/scripts/verify_proof_pack.py <proof-pack.json>')
        raise SystemExit(1)
    raise SystemExit(main(sys.argv[1]))
