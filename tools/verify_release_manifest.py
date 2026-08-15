from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'RELEASE_MANIFEST.json').read_text(encoding='utf-8'))
errors=[]
for rel,expected in manifest['files'].items():
    p=ROOT/rel
    if not p.exists():
        errors.append(f'MISSING {rel}'); continue
    actual=hashlib.sha256(p.read_bytes()).hexdigest()
    if actual!=expected: errors.append(f'CHANGED {rel}')
material='\n'.join(f'{k}:{v}' for k,v in sorted(manifest['files'].items()))
tree=hashlib.sha256(material.encode()).hexdigest()
if tree!=manifest['source_tree_sha256']: errors.append('TREE DIGEST MISMATCH')
if errors:
    print('\n'.join(errors)); sys.exit(2)
print(f"VALID release {manifest['release']} · {manifest['file_count']} files · {tree}")
