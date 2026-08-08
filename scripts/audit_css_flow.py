#!/usr/bin/env python3
"""Static CSS flow audit for PES Arena.

V1.3.38: scans CSS recursively and reports module ownership/cascade risks:
- repeated selectors inside one file
- exact selectors declared across multiple CSS modules
- !important density
- display:none / visibility:hidden / opacity:0 rules
- room-specific conflicts separately from global CSS
Keyframes are ignored.
"""
from __future__ import annotations
import collections
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
CSS_FILES = [ROOT / "static/style.css", *sorted((ROOT / "static/css").rglob("*.css"))]
# Compatibility index contains only imports; exclude it from ownership statistics.
CSS_FILES = [p for p in CSS_FILES if p.name != "arena_room_v2.css"]


def blocks(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"@(?:-webkit-)?keyframes\s+[^\{]+\{(?:[^{}]*\{[^{}]*\})+\s*\}", "", text, flags=re.S)
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", text, flags=re.S):
        raw, body = m.group(1).strip(), m.group(2)
        if raw.startswith("@") or raw in {"from", "to"} or re.fullmatch(r"\d+%", raw):
            continue
        yield raw, body


selector_files = collections.defaultdict(set)
repeated_by_file = {}
hiding = []
important_by_file = {}

for path in CSS_FILES:
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8", errors="ignore")
    important_by_file[rel] = text.count("!important")
    local = collections.Counter()
    for raw, body in blocks(text):
        for selector in [" ".join(s.split()) for s in raw.split(",") if s.strip()]:
            selector_files[selector].add(rel)
            local[selector] += 1
            if re.search(r"(?:display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0(?:\D|$))", body, re.I):
                hiding.append((rel, selector))
    repeated_by_file[rel] = [(s, c) for s, c in local.items() if c > 1]

cross = [(s, sorted(v)) for s, v in selector_files.items() if len(v) > 1]
room_files = {p.relative_to(ROOT).as_posix() for p in CSS_FILES if "/room/" in p.as_posix()}
room_cross = [(s, fs) for s, fs in cross if any(f in room_files for f in fs)]

print("PES Arena CSS Module Flow Audit")
print("================================")
print(f"CSS source files: {len(CSS_FILES)}")
print(f"!important total: {sum(important_by_file.values())}")
print(f"Cross-file exact duplicate selectors: {len(cross)}")
print(f"Cross-file selectors touching Room modules: {len(room_cross)}")
print(f"Selectors that can hide UI: {len(hiding)}")

print("\n!important by file")
for f, count in sorted(important_by_file.items(), key=lambda x: -x[1]):
    if count:
        print(f"  {count:4d}  {f}")

print("\nRepeated selectors inside each Room module")
for f in sorted(room_files):
    repeats = repeated_by_file.get(f, [])
    print(f"  {f}: {len(repeats)} repeated selectors")
    for s, count in sorted(repeats, key=lambda x: (-x[1], x[0]))[:8]:
        print(f"      x{count:<2} {s}")

print("\nCross-module Room selector ownership conflicts (top 50)")
for s, files in sorted(room_cross, key=lambda x: (-len(x[1]), x[0]))[:50]:
    print(f"  {s} -> {', '.join(files)}")

print("\nState-hiding selectors relevant to room/invite (top 60)")
for f, s in [x for x in hiding if any(k in x[1] for k in ("room", "invite", "modal", "hidden"))][:60]:
    print(f"  {f}: {s}")
