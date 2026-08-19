"""Build synthetic mock-io fixtures for the base test case.

Real mmnr patrol data (GPS tracks, ranger names) is sensitive and must never
be committed — these fixtures are fully synthetic: deterministic random-walk
tracks inside the Mara Triangle bounding box, fake rangers/teams, and
patrol_information events shaped exactly like the production payloads
(title-mapped event_details keys, `patrols` id-list linkage as a native
arrow list so `explode` works after the parquet round-trip).

Run from the inner workflow env:
    cd ecoscope-workflows-mt-patrols-workflow
    pixi run python ../dev/fixtures/build_patrol_fixtures.py
"""

import json
import uuid
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

OUT_DIR = Path(__file__).resolve().parent
RNG = np.random.default_rng(20260701)

# (slug, display, area) — real patrol-type slugs (org config, already public
# in spec.yaml defaults); everything else below is synthetic
PATROL_TYPES = [
    ("general_law_enforcement", "Anti-Poaching - Foot (Triangle)", "triangle"),
    ("law_enforcement_vehicle", "Anti-Poaching - Vehicle (Triangle)", "triangle"),
    ("anti_harass_patrol", "Anti-Harassment - Foot (Triangle)", "triangle"),
    ("anti_harass_vehicle", "Anti-Harassment - Vehicle (Triangle)", "triangle"),
    ("rhino_monitoring_patrol", "Rhino Monitoring - Foot (Triangle)", "triangle"),
    ("community_outreach", "Community Outreach - Foot (Triangle)", "triangle"),
    ("law_enforcement_veh_reserve", "Law Enforcement - Vehicle (Reserve)", "reserve"),
    ("anti_harass_veh_reserve", "Anti-Harassment - Vehicle (Reserve)", "reserve"),
    ("rhino_monitor_patrol_reserve", "Rhino Monitoring - Foot (Reserve)", "reserve"),
]
MANDATES = {
    "general_law_enforcement": "Anti Poaching",
    "law_enforcement_vehicle": "Anti Poaching",
    "anti_harass_patrol": "Anti-Animal harassment",
    "anti_harass_vehicle": "Anti-Animal harassment",
    "rhino_monitoring_patrol": "Rhino Monitoring",
    "community_outreach": "Community Outreach",
    "law_enforcement_veh_reserve": "Anti Poaching",
    "anti_harass_veh_reserve": "Anti-Animal harassment",
    "rhino_monitor_patrol_reserve": "Rhino Monitoring",
}
TEAMS = {"triangle": ["Team Alpha", "Team Bravo"], "reserve": ["Team Charlie", "Team Delta"]}
RANGERS = [f"Ranger {i:02d}" for i in range(1, 9)]
TRANSPORTS = ["Foot", "Vehicle"]

# rough Mara Triangle / Reserve bounding box
LON0, LON1, LAT0, LAT1 = 34.90, 35.30, -1.60, -1.30


def fake_id(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"mt-patrols-fixture/{name}"))


patrol_rows, obs_frames, event_rows = [], [], []
serial = 1000
for day, (slug, display, area) in enumerate(PATROL_TYPES + PATROL_TYPES[:3]):
    serial += 1
    patrol_id = fake_id(f"patrol/{serial}")
    start = pd.Timestamp("2026-07-02T06:00:00Z") + pd.Timedelta(days=2 * day % 26)
    n_pts = 120
    end = start + pd.Timedelta(seconds=60 * n_pts)
    ranger = RANGERS[serial % len(RANGERS)]
    team = TEAMS[area][serial % 2]
    title = f"{display} {start:%d %b}"

    patrol_rows.append(
        {
            "id": patrol_id,
            "serial_number": serial,
            "title": title,
            "state": "done",
            "patrol_type": slug,
        }
    )

    lon = RNG.uniform(LON0, LON1)
    lat = RNG.uniform(LAT0, LAT1)
    steps = RNG.normal(0, 0.0012, size=(n_pts, 2)).cumsum(axis=0)
    lons = np.clip(lon + steps[:, 0], LON0, LON1)
    lats = np.clip(lat + steps[:, 1], LAT0, LAT1)
    times = pd.date_range(start, periods=n_pts, freq="60s", tz="UTC")
    obs_frames.append(
        gpd.GeoDataFrame(
            {
                "extra__id": [fake_id(f"obs/{serial}/{i}") for i in range(n_pts)],
                "extra__created_at": times,
                "extra__recorded_at": times,
                "extra__subject_id": fake_id(f"subject/{ranger}"),
                "groupby_col": patrol_id,
                "fixtime": times,
                "junk_status": False,
                "patrol_id": patrol_id,
                "patrol_title": title,
                "patrol_serial_number": serial,
                "patrol_start_time": start,
                "patrol_end_time": end,
                "patrol_type": fake_id(f"patrol-type/{slug}"),
                "patrol_status": "done",
                "patrol_subject": ranger,
                "patrol_type__value": slug,
                "patrol_type__display": display,
            },
            geometry=[Point(x, y) for x, y in zip(lons, lats)],
            crs=4326,
        )
    )

    # 1-3 team members per event; every fifth serial lists the leader among
    # the members too, exercising the roster UNION dedup
    members = [RANGERS[(serial + 1 + i) % len(RANGERS)] for i in range(serial % 3 + 1)]
    if serial % 5 == 0:
        members[0] = ranger

    # two patrols deliberately get NO patrol_information event to exercise
    # the "Unknown" attribute fallback
    if serial % 6 != 0:
        event_rows.append(
            {
                "id": fake_id(f"event/{serial}"),
                "serial_number": 9000 + serial,
                "event_type": "patrol_information",
                "time": (start + pd.Timedelta(minutes=5)).isoformat(),
                "title": "Patrol information",
                "state": "resolved",
                "event_details": json.dumps(
                    {
                        "Team name": team,
                        "Patrol leader": ranger,
                        "Team members": members,
                        "Armed?": bool(serial % 2),
                        "Mandate": MANDATES[slug],
                        "Transport type": TRANSPORTS[serial % 2],
                    }
                ),
                "patrols": [patrol_id],
                "geometry": Point(lons[0], lats[0]),
            }
        )

patrols_df = pd.DataFrame(patrol_rows)
patrols_df.to_parquet(OUT_DIR / "patrols.example-return.parquet")

obs = gpd.GeoDataFrame(pd.concat(obs_frames, ignore_index=True), crs=4326)
obs.to_parquet(OUT_DIR / "patrol-obs.example-return.parquet")

events = gpd.GeoDataFrame(pd.DataFrame(event_rows), geometry="geometry", crs=4326)
events.to_parquet(OUT_DIR / "patrol-info-events.example-return.parquet")

print(f"patrols: {len(patrols_df)}, obs: {len(obs)}, events: {len(events)}")
print(f"wrote fixtures to {OUT_DIR}")
