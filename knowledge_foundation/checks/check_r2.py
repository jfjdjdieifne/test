"""Consistency checks for knowledge_foundation (R2). Read-only; prints a report.

Run from the knowledge_foundation directory:  python3 checks/check_r2.py
"""
import json, re, glob, collections, sys

ROOT = "."
idx = json.load(open(f"{ROOT}/claims_index.json", encoding="utf-8"))
claims = idx["claims"]
ids = [c["id"] for c in claims]
idset = set(ids)
src_text = open(glob.glob(f"{ROOT}/12_*.md")[0], encoding="utf-8").read()
src_ids = set(re.findall(r"SRC-[A-Z0-9-]+", src_text))
problems = []

def check(name, bad):
    status = "PASS" if not bad else f"FAIL ({len(bad)})"
    print(f"[{status}] {name}")
    for b in bad[:20]:
        print("     ", b)
    problems.extend(bad)

# 1 JSON / uniqueness
check("claims_index.json parses; unique IDs", [] if len(ids) == len(idset) else ["duplicate IDs"])
print(f"      claims: {len(ids)}")

# 2 provenance / grade rules (file 13 §13.1 rules, R2 vocabulary)
rules = []
for c in claims:
    t, pv, g, s = c["type"], c["provenance"], c["grade"], c["sources"]
    if t == "E" and pv != "ICT-primary": rules.append(f"{c['id']}: E requires ICT-primary")
    if t == "E*" and pv != "secondary-community": rules.append(f"{c['id']}: E* requires secondary-community")
    if t == "G" and pv not in ("academic", "open-source", "secondary-academic") and not pv.startswith("mixed"): rules.append(f"{c['id']}: G requires academic/open-source")
    if g.startswith("P") and not (pv.startswith("ICT") or pv.startswith("mixed")): rules.append(f"{c['id']}: P grade requires ICT provenance")
    if g.startswith("AC") and pv not in ("academic", "secondary-academic") and not pv.startswith("mixed"): rules.append(f"{c['id']}: AC grade requires academic provenance")
    if g == "OS1" and pv != "open-source" and not pv.startswith("mixed"): rules.append(f"{c['id']}: OS1 requires open-source")
    if g == "NOT_SOURCE_BASED" and s: rules.append(f"{c['id']}: NOT_SOURCE_BASED must have no sources")
check("provenance/grade rules", rules)

# 3 referential integrity: related, conflicts, sources in file 12
bad = []
for c in claims:
    for r in c.get("related", []) + c.get("conflicts", []):
        if r not in idset: bad.append(f"{c['id']} -> unknown related/conflict {r}")
    for s in c.get("sources", []):
        if s not in src_ids: bad.append(f"{c['id']} -> source {s} not in file 12")
check("related/conflict/source references resolve", bad)

# 4 claim IDs cited in markdown exist (prefixes that are claim namespaces)
PREFIX = r"(?:CC|CF|PM|MS|LQ|OS|GP|FZ|IC|OB|FV|ZN|IC|CS|CH|UN|PAR|E|SP|SWS|LRN|CSM|TS|DC|MI|AC|S|OBP)"
cited = set()
for f in glob.glob(f"{ROOT}/*.md"):
    for m in re.findall(r"\b(" + r"[A-Z]{2,4}(?:\*)?-[A-Z0-9][A-Z0-9-]*" + r")\b", open(f, encoding="utf-8").read()):
        cited.add(m)
ignore_prefix = ("SRC-", "P-", "F-", "X-", "T-", "G-", "CASE-", "UN-", "REF-", "STR-", "PAR-", "XX-", "FACT-", "BSD-", "AAAI-", "IC-", "PRE-", "ICT-")
claim_like = {c for c in cited if not c.startswith(ignore_prefix)}
missing = sorted(c for c in claim_like if c not in idset and re.match(r"^(CC|CF|PM|MS|LQ|OS|GP|FZ|SP|SWS|LRN|CSM|OB|FV|ZN|CS|E|AC|DC|OBP|MI|SY|NC|AS|VS|LT)[-*]", c))
ALLOW = {"OB-C", "OB-P", "OS-01-"}  # generator names (G-OB-C, G-OB-P) and a trailing hyphen in prose; reviewed
missing = [m for m in missing if m not in ALLOW]
check("claim-like IDs cited in markdown exist in index (prefix-scoped; excludes task/parameter/finding/source namespaces; allowlist reviewed)", [f"missing {m}" for m in missing])
print("      cited claim-like IDs not in index are listed above; namespaces excluded by design:", ", ".join(ignore_prefix))

# 5 retired namespace
retired = [f for f in glob.glob(f"{ROOT}/*.md") if re.search(r"\bCH-0\d\b", open(f, encoding="utf-8").read())]
check("no retired CH-0n case labels remain", retired)

# 6 timestamp-like and percent tokens (for manual review)
ts = []
for f in sorted(glob.glob(f"{ROOT}/*.md")):
    for i, line in enumerate(open(f, encoding="utf-8"), 1):
        for m in re.findall(r"\b\d{1,2}:\d{2}\b", line):
            ts.append(f"{f}:{i}: {m}")
print(f"[INFO] mm:ss-like tokens: {len(ts)}")
for t in ts[:30]: print("     ", t)

pct = collections.Counter()
for f in sorted(glob.glob(f"{ROOT}/*.md")):
    pct[f] = len(re.findall(r"\d+(?:\.\d+)?\s?%|\d+\s?percent", open(f, encoding="utf-8").read()))
print("[INFO] percentage-like tokens per file:", {k.split('/')[-1][:3]: v for k, v in pct.items() if v})


# 7 cross-file references for R3 seed procedures and selectors
defined_sp = set(re.findall(r"^### (SP-\d{2})", open(f"{ROOT}/17_SEED_PROCEDURES.md", encoding="utf-8").read(), re.M))
cited_sp = set()
for f in glob.glob(f"{ROOT}/1[5-9]_*.md"):
    cited_sp |= set(re.findall(r"\bSP-\d{2}\b", open(f, encoding="utf-8").read()))
undefined_sp = sorted(x for x in cited_sp if x not in defined_sp)
check("every SP-NN cited in files 15-19 is defined in file 17 (### heading)", [f"undefined {x}" for x in undefined_sp])

sel_defined = set(re.findall(r"\*\*(SEL-[A-Z-]+)\*\*", open(f"{ROOT}/11_IMPLEMENTATION_KNOWLEDGE_CONTRACTS.md", encoding="utf-8").read()))
sel_cited = set()
for f in glob.glob(f"{ROOT}/*.md"):
    sel_cited |= set(re.findall(r"\bSEL-[A-Z-]+\b", open(f, encoding="utf-8").read()))
check("every SEL-* cited is defined in file 11", [f"undefined {x}" for x in sorted(sel_cited - sel_defined)])

print("\nClaim type distribution:", dict(collections.Counter(c["type"] for c in claims)))
print("Grade distribution:", dict(collections.Counter(c["grade"] for c in claims)))
print("\nTOTAL FAILURES:", len(problems))
sys.exit(1 if problems else 0)
