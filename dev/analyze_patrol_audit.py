"""Audit July patrols per side (Triangle/Reserve) from audit_data.json:
1. missing patrol_information
2. patrol type vs patrol info mismatch (mandate / transport / team)
3. patrol info present but fields missing
"""
import json
import os
import re
from collections import Counter

path = "audit_data.json"
d = json.load(open(path))
events = d["events"]
july = [r for r in d["rows"] if r["in_july"] and r["side"] in ("Triangle", "Reserve")]

MANDATE_MAP = {
    "Anti-Harassment": "anti_animal_harassment",
    "Anti-Poaching": "anti_poaching",
    "Law Enforcement": "law_enforcement",
    "Rhino Monitoring": "rhino_monitoring",
}


def expected(disp):
    base = re.sub(r"\s*\((Triangle|Reserve)\)$", "", disp)
    if " - " in base:
        mand_name, transport = base.rsplit(" - ", 1)
    else:
        mand_name, transport = base, None
    return MANDATE_MAP.get(mand_name), transport.lower() if transport else None


def tokens(name):
    return [t for t in re.split(r"[^a-z]+", (name or "").lower()) if len(t) > 1]


def is_person(leader):
    # tracker devices look like "Cheetah 2", "SP051294-MMNR-..."; people have no digits
    return bool(leader) and not re.search(r"\d", leader)


def person_matches(leader, candidate):
    lt, ct = tokens(leader), tokens(candidate)
    return bool(lt) and bool(ct) and lt[0] in ct and lt[-1] in ct


for side in ("Triangle", "Reserve"):
    rows = [r for r in july if r["side"] == side]
    print(f"\n{'=' * 60}\n{side}: {len(rows)} July patrols")
    for disp, n in Counter(r["ptype_display"] for r in rows).most_common():
        print(f"   {n:4d}  {disp}")

    # Q1: missing patrol info
    missing = sorted(r["serial"] for r in rows if not r["pinfo_ids"])
    withinfo = [r for r in rows if r["pinfo_ids"]]
    multi = [r for r in rows if len(r["pinfo_ids"]) > 1]
    print(f"\nQ1. missing patrol_information: {len(missing)}/{len(rows)}")
    print(f"    serials: {missing}")
    if multi:
        print(f"    (with >1 patrol_information: {[r['serial'] for r in multi]})")

    # Q2: type vs info mismatches
    mm_mand, mm_trans, mm_team = [], [], []
    team_checkable = 0
    for r in withinfo:
        exp_m, exp_t = expected(r["ptype_display"])
        evs = [events[i] for i in r["pinfo_ids"] if i in events]
        dets = [e.get("event_details") or {} for e in evs]
        got_m = {dt.get("Mandate") for dt in dets if dt.get("Mandate")}
        got_t = {(dt.get("Transport_type") or "").lower() for dt in dets if dt.get("Transport_type")}
        if exp_m and got_m and exp_m not in got_m:
            mm_mand.append((r["serial"], r["ptype_display"], sorted(got_m)))
        if exp_t and got_t and exp_t not in got_t:
            mm_trans.append((r["serial"], r["ptype_display"], sorted(got_t)))
        if is_person(r["leader"]):
            team_checkable += 1
            names = []
            for dt in dets:
                names.append(dt.get("Team_leader") or "")
                names.extend(dt.get("Team_members") or [])
            if not any(person_matches(r["leader"], n) for n in names):
                mm_team.append((r["serial"], r["leader"], sorted(n for n in names if n)))
    any_mm = sorted({s for s, *_ in mm_mand} | {s for s, *_ in mm_trans} | {s for s, *_ in mm_team})
    print(f"\nQ2. type vs patrol-info mismatch (any field): {len(any_mm)}/{len(withinfo)} -> {any_mm}")
    print(f"    mandate mismatches: {len(mm_mand)}")
    for s, ty, got in mm_mand:
        print(f"      #{s}  {ty}  -> info mandate: {got}")
    print(f"    transport mismatches: {len(mm_trans)}")
    for s, ty, got in mm_trans:
        print(f"      #{s}  {ty}  -> info transport: {got}")
    print(f"    team mismatches (patrol leader not in info team; only {team_checkable} patrols have a person leader): {len(mm_team)}")
    for s, ld, names in mm_team:
        print(f"      #{s}  leader {ld!r}  -> info team: {names}")

    # Q3: patrol info present but fields missing
    core = ["Mandate", "Transport_type", "Team_leader", "Team_members"]
    extra = ["Team_name", "Sector", "Armed"]
    field_missing = Counter()
    incomplete = {}
    for r in withinfo:
        missing_fields = set()
        for i in r["pinfo_ids"]:
            dt = (events.get(i) or {}).get("event_details") or {}
            for f in core + extra:
                v = dt.get(f)
                if v is None or v == "" or v == []:
                    missing_fields.add(f)
        for f in missing_fields:
            field_missing[f] += 1
        if missing_fields & set(core):
            incomplete[r["serial"]] = sorted(missing_fields & set(core))
    print(f"\nQ3. patrol info present but core field missing (mandate/transport/team leader/team members): {len(incomplete)}/{len(withinfo)}")
    for s, fs in sorted(incomplete.items()):
        print(f"      #{s}: missing {fs}")
    print("    per-field missing counts (all fields):")
    for f in core + extra:
        print(f"      {f}: {field_missing.get(f, 0)}")
