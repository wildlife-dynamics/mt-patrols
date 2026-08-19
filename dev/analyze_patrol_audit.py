"""Audit patrols per side (Triangle/Reserve) from audit_data.json:
1. missing patrol_information
2. patrol type vs patrol info mismatch (mandate / transport / team)
3. patrol info present but fields missing

Usage: run fetch_patrol_audit.py first (writes audit_data.json to the cwd),
then run this from the same directory; it prints the report to stdout.
Needs only the stdlib, so plain `python3` works.

Side classification comes from the patrol-type display suffix
"(Triangle)"/"(Reserve)"; unlabeled types (Cheetah Monitoring, Operations)
are excluded. The team check compares that side against the patrol info
Team_name prefix (triangle_* / res_*). If new patrol types or team-name
prefixes appear, update MANDATE_MAP / team_side accordingly.
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


def team_side(team_name):
    # Team_name values encode the side: "triangle_puru" vs "res_keek"
    if (team_name or "").startswith("triangle_"):
        return "Triangle"
    if (team_name or "").startswith("res_"):
        return "Reserve"
    return None


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
        team_sides = {(dt.get("Team_name"), team_side(dt.get("Team_name"))) for dt in dets if dt.get("Team_name")}
        wrong = sorted(tn for tn, ts in team_sides if ts and ts != side)
        if wrong:
            mm_team.append((r["serial"], r["ptype_display"], wrong))
    any_mm = sorted({s for s, *_ in mm_mand} | {s for s, *_ in mm_trans} | {s for s, *_ in mm_team})
    print(f"\nQ2. type vs patrol-info mismatch (any field): {len(any_mm)}/{len(withinfo)} -> {any_mm}")
    print(f"    mandate mismatches: {len(mm_mand)}")
    for s, ty, got in mm_mand:
        print(f"      #{s}  {ty}  -> info mandate: {got}")
    print(f"    transport mismatches: {len(mm_trans)}")
    for s, ty, got in mm_trans:
        print(f"      #{s}  {ty}  -> info transport: {got}")
    print(f"    team mismatches (Team_name belongs to the other side): {len(mm_team)}")
    for s, ty, names in mm_team:
        print(f"      #{s}  {ty}  -> info team name: {names}")

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
