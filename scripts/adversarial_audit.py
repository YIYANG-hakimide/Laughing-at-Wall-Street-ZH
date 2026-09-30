"""Adversarial chapter spot audit.

This deliberately checks correspondence beyond byte length: it samples the first,
middle and last substantive source blocks in every section, compares translated
sample placement, and checks that numeric facts, URLs, percentages, currencies,
and acronyms present in the source are represented in the nearby translation.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = json.loads((ROOT / "book.json").read_text())

def source_substantive(blocks):
    out=[]
    for b in blocks:
        t=b.get("text", "").strip()
        if len(t) < 45: continue
        if re.fullmatch(r"[0-9 .—–-]+", t): continue
        if t.upper() == t and sum(ch.isalpha() for ch in t) > 8: continue
        out.append(t)
    return out

def md_units(text):
    out=[]
    for raw in text.splitlines():
        s=raw.strip()
        if not s or s.startswith("#") or s.startswith("!") or s.startswith("|") or re.fullmatch(r"[-*_ ]{3,}", s):
            continue
        s=re.sub(r"^(?:[-*•]|\d+[.)])\s+", "", s)
        if len(s) >= 30: out.append(s)
    return out

def anchors(s):
    vals=[]
    vals += re.findall(r"https?://[^\s)]+|(?:www\.)[^\s)]+", s, re.I)
    vals += re.findall(r"\$\s?[\d,]+(?:\.\d+)?|\b\d[\d,]*(?:\.\d+)?%?\b", s)
    vals += re.findall(r"\b[A-Z]{2,}(?:[-&][A-Z0-9]+)*\b", s)
    return vals

def norm_num(x):
    return re.sub(r"[^0-9.]", "", x)

failed=False
for c in BOOK["chapters"]:
    src=source_substantive(c["blocks"])
    p=ROOT / f"{c['id']}.zh.md"
    if not p.exists():
        print(f"FAIL {c['id']}: missing translation")
        failed=True; continue
    dst=md_units(p.read_text())
    if not src or not dst:
        print(f"FAIL {c['id']}: no substantive units")
        failed=True; continue
    positions=sorted(set([0, len(src)//2, len(src)-1]))
    print(f"\n[{c['id']}] source_units={len(src)} translated_units={len(dst)} samples={positions}")
    for pos in positions:
        target=dst[min(len(dst)-1, round(pos*(len(dst)-1)/max(1,len(src)-1)))]
        sa=anchors(src[pos]); da=anchors(target)
        missing=[]
        for a in sa:
            if a.lower().startswith(('http','www.')):
                if a.lower().rstrip('.,') not in target.lower(): missing.append(a)
            elif a[:1].isdigit() and norm_num(a) and norm_num(a) not in ''.join(norm_num(x) for x in da):
                missing.append(a)
            elif a.isupper() and len(a)>=3 and a not in target:
                # Acronyms may reasonably be translated; report only for review.
                missing.append(a)
        print(f"  sample {pos+1}: source={src[pos][:92]!r}")
        print(f"             zh={target[:92]!r}")
        if missing:
            print(f"             REVIEW anchors={missing}")
print("\nRESULT: spot samples generated; REVIEW lines require human inspection.")
sys.exit(1 if failed else 0)
