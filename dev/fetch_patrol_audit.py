"""Fetch July 2026 (EAT) patrols + patrol_information events from mmnr, persist to audit_data.json."""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import requests

SERVER = os.environ["ecoscope_workflows__connections__earthranger__mmnr__server"].rstrip("/")
USER = os.environ["ecoscope_workflows__connections__earthranger__mmnr__username"]
PWD = os.environ["ecoscope_workflows__connections__earthranger__mmnr__password"]

# July 2026 in East Africa Time (UTC+3)
LOWER = "2026-06-30T21:00:00Z"
UPPER = "2026-07-31T20:59:59Z"

r = requests.post(
    f"{SERVER}/oauth2/token",
    data={"grant_type": "password", "username": USER, "password": PWD, "client_id": "das_web_client"},
    timeout=60,
)
r.raise_for_status()
tok = r.json()["access_token"]
S = requests.Session()
S.headers["Authorization"] = f"Bearer {tok}"
API = f"{SERVER}/api/v1.0"


def get(url, **params):
    resp = S.get(url, params=params, timeout=90)
    resp.raise_for_status()
    return resp.json()["data"]


# patrol types: segments reference types by value (e.g. "anti_harass_vehicle")
ptypes = {p["value"]: p for p in get(f"{API}/activity/patrols/types")}

# patrols overlapping the window (paginate, dedupe by serial)
patrols_raw = []
url = f"{API}/activity/patrols"
params = {"filter": json.dumps({"date_range": {"lower": LOWER, "upper": UPPER}}), "page_size": 100}
while url:
    d = get(url, **params)
    patrols_raw.extend(d["results"])
    url = d.get("next")
    params = {}

seen = set()
rows = []
for p in patrols_raw:
    if p["serial_number"] in seen:
        continue
    seen.add(p["serial_number"])
    segs = p.get("patrol_segments") or []
    seg = segs[0] if segs else {}
    pt_id = seg.get("patrol_type")
    pt = ptypes.get(pt_id) or {}
    disp = pt.get("display", "") or ""
    side = "Triangle" if disp.endswith("(Triangle)") else "Reserve" if disp.endswith("(Reserve)") else "Other"
    start = ((seg.get("time_range") or {}).get("start_time")) or ""
    in_july = LOWER <= start.replace("+00:00", "Z") <= UPPER if start else False
    pinfo_ids = [
        e["id"]
        for s in segs
        for e in (s.get("events") or [])
        if e.get("event_type") == "patrol_information"
    ]
    leader = ((seg.get("leader") or {}).get("name")) or ""
    rows.append(
        dict(
            serial=p["serial_number"],
            title=p.get("title"),
            state=p.get("state"),
            ptype=pt.get("value"),
            ptype_display=disp,
            side=side,
            leader=leader,
            start=start,
            in_july=in_july,
            pinfo_ids=pinfo_ids,
        )
    )

july = [r_ for r_ in rows if r_["in_july"]]
print(f"fetched {len(patrols_raw)} raw, {len(rows)} unique, {len(july)} start in July", file=sys.stderr)

# fetch patrol_information events
all_ids = sorted({i for r_ in july for i in r_["pinfo_ids"]})
print(f"fetching {len(all_ids)} patrol_information events", file=sys.stderr)


def fetch_event(eid):
    return eid, get(f"{API}/activity/event/{eid}", include_details="true")


events = {}
with ThreadPoolExecutor(8) as ex:
    for eid, ev in ex.map(fetch_event, all_ids):
        events[eid] = ev

out = dict(rows=rows, events=events, ptypes={k: v.get("display") for k, v in ptypes.items()})
path = "audit_data.json"
json.dump(out, open(path, "w"))
print(f"wrote {path}", file=sys.stderr)
