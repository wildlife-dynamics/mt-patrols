"""Anonymize patrol relocation data for public use.

Applies:
- GPS coordinate offset (shifts location while preserving spatial relationships)
- Ranger name replacement with fake names
- UUID regeneration with consistent mapping
- Station/team name replacement
- Adds mock foot patrol data
"""

import struct
import uuid

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

INPUT_PATH = "/Users/yunwu/MEP/wt/outputs/mt_patrol_reloc_08aed9f.parquet"
OUTPUT_PATH = "/Users/yunwu/MEP/wt/mt-patrols/resources/mock_patrol_reloc.parquet"

# Coordinate offset: shift ~2 degrees (preserves shape, moves location)
LON_OFFSET = -2.15
LAT_OFFSET = 1.73

FAKE_STATIONS = {
    "Purungat": "Savanna Gate",
    "Oloololo": "River Post",
    "Iseiyia": "Hill Camp",
    "Kilo 2": "Valley Base",
    "Ololaimutia": "Plains Outpost",
}

FAKE_TEAMS = {
    "Purungat": "Savanna Gate",
    "Oloololo": "River Post",
    "Iseiyia": "Hill Camp",
    "Kilo2": "Valley Base",
    "Ololaimutia": "Plains Outpost",
}

FAKE_NAMES = [
    "Alex Mwangi",
    "Bella Otieno",
    "Chris Kamau",
    "Diana Wanjiku",
    "Eric Ochieng",
    "Fatima Hassan",
    "George Njoroge",
    "Hannah Chebet",
    "Isaac Mutua",
    "Jane Kiplagat",
    "Kevin Rotich",
    "Linda Akinyi",
    "Martin Karanja",
    "Nancy Wambui",
    "Oscar Kimani",
    "Patricia Chege",
    "Robert Maina",
    "Sarah Nyambura",
    "Thomas Omondi",
    "Uma Wairimu",
    "Victor Kibet",
    "Wendy Moraa",
    "Xavier Ndirangu",
    "Yolanda Adhiambo",
    "Zack Mureithi",
]


def make_uuid_map(original_uuids: pd.Series) -> dict[str, str]:
    """Create a consistent mapping from original UUIDs to new random UUIDs."""
    rng = np.random.default_rng(42)
    unique = original_uuids.dropna().unique()
    return {
        old: str(uuid.UUID(int=int.from_bytes(rng.bytes(16), "big")))
        for old in unique
    }


def make_wkb_point(lon: float, lat: float) -> bytes:
    """Create a WKB Point from lon/lat."""
    return struct.pack("<bIdd", 1, 1, lon, lat)


def generate_foot_patrol_data(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Generate mock foot patrol data based on existing vehicle patrol patterns."""
    # Pick a subset of existing patrols as templates
    template_patrols = df.groupby("patrol_id").first().sample(n=3, random_state=42)

    foot_rows = []
    for i, (_, template) in enumerate(template_patrols.iterrows()):
        patrol_id = str(uuid.UUID(int=int.from_bytes(rng.bytes(16), "big")))
        leader_uuid = str(uuid.UUID(int=int.from_bytes(rng.bytes(16), "big")))
        leg_uuid = str(uuid.UUID(int=int.from_bytes(rng.bytes(16), "big")))
        day_uuid = str(uuid.UUID(int=int.from_bytes(rng.bytes(16), "big")))

        leader_name = FAKE_NAMES[-(i + 1)]  # pick from the end of the list
        station = list(FAKE_STATIONS.values())[i % len(FAKE_STATIONS)]
        team = list(FAKE_TEAMS.values())[i % len(FAKE_TEAMS)]

        # Generate a foot patrol path: shorter distances, slower speeds
        base_lon = template["longitude"] + rng.uniform(-0.01, 0.01)
        base_lat = template["latitude"] + rng.uniform(-0.01, 0.01)
        n_points = rng.integers(80, 200)

        # Random walk for foot patrol (smaller steps than vehicle)
        lon_steps = rng.normal(0, 0.0003, n_points).cumsum() + base_lon
        lat_steps = rng.normal(0, 0.0003, n_points).cumsum() + base_lat

        start_time = pd.Timestamp(template["fixtime"]) + pd.Timedelta(hours=rng.integers(0, 3))
        times = [start_time + pd.Timedelta(minutes=int(m)) for m in range(n_points)]

        patrol_start = times[0].strftime("%Y-%m-%dT%H:%M:%S")
        patrol_end = times[-1].strftime("%Y-%m-%dT%H:%M:%S")
        day_str = times[0].strftime("%Y-%m-%d")

        for j in range(n_points):
            foot_rows.append(
                {
                    "longitude": lon_steps[j],
                    "latitude": lat_steps[j],
                    "fixtime": times[j],
                    "patrol_id": patrol_id,
                    "groupby_col": patrol_id,
                    "patrol_leg_uuid": leg_uuid,
                    "patrol_leg_id": "1",
                    "patrol_leg_day_day": day_str,
                    "patrol_leg_day_uuid": day_uuid,
                    "patrol_mandate": "Anti-Poaching",
                    "patrol_transport": "Foot",
                    "station": station,
                    "team": team,
                    "objective": None,
                    "patrol_type": "GROUND",
                    "patrol_start_time": patrol_start,
                    "patrol_end_time": patrol_end,
                    "patrol_leader_uuid": leader_uuid,
                    "patrol_leader_name": leader_name,
                    "distance": rng.uniform(10, 40),
                    "duration(s)": 60.0,
                    "duration(h)": 1 / 60,
                    "track": None,
                    "patrol_type__display": None,
                    "junk_status": False,
                    "patrol_type__value": None,
                    "patrol_serial_number": None,
                    "patrol_status": None,
                    "patrol_subject": None,
                    "geometry": None,
                }
            )

    foot_df = pd.DataFrame(foot_rows)
    # Match dtypes
    foot_df["fixtime"] = pd.to_datetime(foot_df["fixtime"], utc=True)
    for col in foot_df.columns:
        if col in df.columns and df[col].dtype != foot_df[col].dtype:
            try:
                foot_df[col] = foot_df[col].astype(df[col].dtype)
            except (ValueError, TypeError):
                pass
    return foot_df


def main():
    df = pd.read_parquet(INPUT_PATH)
    rng = np.random.default_rng(42)

    # 1. Offset coordinates
    df["longitude"] = df["longitude"] + LON_OFFSET
    df["latitude"] = df["latitude"] + LAT_OFFSET

    # 2. Replace station/team names
    df["station"] = df["station"].map(FAKE_STATIONS)
    df["team"] = df["team"].map(FAKE_TEAMS)

    # 3. Replace ranger names
    original_names = df["patrol_leader_name"].dropna().unique()
    name_map = {old: FAKE_NAMES[i % len(FAKE_NAMES)] for i, old in enumerate(original_names)}
    df["patrol_leader_name"] = df["patrol_leader_name"].map(name_map)

    # 4. Regenerate UUIDs
    for col in ["patrol_id", "patrol_leg_uuid", "patrol_leg_day_uuid", "patrol_leader_uuid"]:
        uuid_map = make_uuid_map(df[col])
        df[col] = df[col].map(uuid_map)

    # Also remap groupby_col (same as patrol_id originally)
    if "groupby_col" in df.columns:
        groupby_map = make_uuid_map(df["groupby_col"])
        df["groupby_col"] = df["groupby_col"].map(groupby_map)

    # 5. Clear serial numbers, subjects, status
    df["patrol_serial_number"] = None
    df["patrol_subject"] = None
    df["patrol_status"] = None
    df["track"] = None
    df["patrol_type__display"] = None
    df["patrol_type__value"] = None

    # 6. Add foot patrol data
    foot_df = generate_foot_patrol_data(df, rng)
    df = pd.concat([df, foot_df], ignore_index=True)

    # Cast string columns
    string_cols = [
        "patrol_id", "groupby_col", "patrol_leg_uuid", "patrol_leg_id",
        "patrol_leg_day_day", "patrol_leg_day_uuid", "patrol_mandate",
        "patrol_transport", "station", "team", "objective", "patrol_type",
        "patrol_start_time", "patrol_end_time", "patrol_leader_uuid",
        "patrol_leader_name", "track", "patrol_type__display",
        "patrol_type__value", "patrol_serial_number", "patrol_status",
        "patrol_subject",
    ]
    for col in string_cols:
        df[col] = df[col].astype("string[python]")

    # Convert to GeoDataFrame with proper geometry for GeoParquet output
    df = df.drop(columns=["geometry"])
    df["geometry"] = [Point(lon, lat) for lon, lat in zip(df["longitude"], df["latitude"])]
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    # Write as GeoParquet (preserves geo metadata for downstream geopandas reads)
    # Then re-read as plain pandas and convert geometry back to WKB bytes
    # to match the original file format (raw WKB in a bytes column)
    gdf.to_parquet(OUTPUT_PATH, index=False)
    print(f"Written {len(df)} rows to {OUTPUT_PATH}")
    print(f"  Vehicle patrols: {(df['patrol_transport'] == 'Vehicle').sum()}")
    print(f"  Foot patrols: {(df['patrol_transport'] == 'Foot').sum()}")
    print(f"  Stations: {df['station'].unique().tolist()}")


if __name__ == "__main__":
    main()
