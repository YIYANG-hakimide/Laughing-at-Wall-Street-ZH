"""Auditable structural inventory for the translated reader files.

This is a structural check, not a claim that machine output is semantically
perfect. It reports source block counts, translated Markdown units, headings,
images and tables so a reviewer can inspect discrepancies chapter by chapter.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
book = json.loads((ROOT / "book.json").read_text())

for chapter in book["chapters"]:
    cid = chapter["id"]
    path = ROOT / f"{cid}.zh.md"
    if not path.exists():
        print(f"MISSING {cid}: translated file absent")
        continue
    text = path.read_text()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    headings = [line for line in lines if re.match(r"^#{1,3}\s+", line)]
    images = [line for line in lines if re.match(r"^!\[.*\]\(.+\)$", line)]
    table_rows = [line for line in lines if line.startswith("|")]
    units = [line for line in lines if not line.startswith("---")]
    source_bytes = sum(len(block["text"].encode()) for block in chapter["blocks"])
    ratio = path.stat().st_size / source_bytes if source_bytes else 0
    print(
        f"{cid}: source_blocks={len(chapter['blocks'])} "
        f"translated_units={len(units)} headings={len(headings)} "
        f"images={len(images)} table_rows={len(table_rows)} "
        f"byte_ratio={ratio:.2f}"
    )
    if ratio < 0.72:
        print(f"  FAIL {cid}: unusually short translation; manual review required")
