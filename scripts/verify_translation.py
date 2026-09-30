import json, re, pathlib, sys
root=pathlib.Path(__file__).resolve().parents[1]
book=json.loads((root/'book.json').read_text())
failed=False
for c in book['chapters']:
    p=root/(c['id']+'.zh.md')
    if not p.exists():
        print(f"[MISSING] {c['id']}: no Chinese file")
        failed=True; continue
    text=p.read_text()
    source_text='\n'.join(x['text'] for x in c['blocks'])
    # English residue heuristic; proper names and technical abbreviations are allowed.
    residue=re.findall(r'\b(?:the|and|with|that|this|from|you|your|chapter|introduction|appendix|notes)\b', text, re.I)
    headings=len(re.findall(r'^#{1,3} ',text,re.M))
    paras=len([x for x in re.split(r'\n\s*\n',text) if x.strip() and not x.lstrip().startswith('#')])
    ratio=len(text.encode())/max(1,len(source_text.encode()))
    print(f"[OK] {c['id']}: source_blocks={len(c['blocks'])} zh_bytes={len(text.encode())} source_bytes={len(source_text.encode())} ratio={ratio:.2f} headings={headings} paras={paras} english_residue={len(residue)}")
    if residue or ratio < .72:
        print(f"  [REVIEW] {c['id']}: byte ratio below 0.72 or English residue found")
        failed=True
sys.exit(1 if failed else 0)
