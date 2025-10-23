from __future__ import annotations
import pandas as pd
from pathlib import Path
from typing import Tuple
from pydantic import TypeAdapter
from novachain.domain.schemas import Shipment, ShipmentEvent, DwellObservation

def load_shipments(path: str | Path) -> list[Shipment]:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    required = {"shipment_id","origin","destination"}
    if not required.issubset(set(df.columns)):
        missing = required - set(df.columns)
        raise ValueError(f"Missing columns: {missing}")
    records = df.to_dict(orient="records")
    return TypeAdapter(list[Shipment]).validate_python(records)

def load_events(path: str | Path) -> list[ShipmentEvent]:
    df = pd.read_csv(path, parse_dates=["event_time"])
    df.columns = [c.strip().lower() for c in df.columns]
    records = df.to_dict(orient="records")
    return TypeAdapter(list[ShipmentEvent]).validate_python(records)

def load_dwell(path: str | Path) -> list[DwellObservation]:
    df = pd.read_csv(path, parse_dates=["arrival_time","departure_time"])
    df.columns = [c.strip().lower() for c in df.columns]
    records = df.to_dict(orient="records")
    return TypeAdapter(list[DwellObservation]).validate_python(records)

def to_lane_key(origin: str, destination: str) -> str:
    return f"{origin.strip().upper()}::{destination.strip().upper()}"

def build_lane_stats(events: list[ShipmentEvent], shipments: list[Shipment]) -> pd.DataFrame:
    """Compute lane transit times from first PICKUP to last DELIVERY per shipment."""
    import numpy as np
    ev = pd.DataFrame([e.model_dump() for e in events])  # ← was e.dict()
    if ev.empty:
        return pd.DataFrame(columns=["lane","mean_hours","count"])
    first_pickup = ev[ev["stop_type"]=="PICKUP"].sort_values("event_time").groupby("shipment_id").first()
    last_delivery = ev[ev["stop_type"]=="DELIVERY"].sort_values("event_time").groupby("shipment_id").last()
    transit = first_pickup[["event_time"]].join(last_delivery[["event_time"]], lsuffix="_start", rsuffix="_end", how="inner")
    transit["hours"] = (transit["event_time_end"] - transit["event_time_start"]).dt.total_seconds()/3600
    sh = pd.DataFrame([s.model_dump() for s in shipments]).set_index("shipment_id")  # ← was s.dict()
    joined = transit.join(sh[["origin","destination"]], how="inner")
    joined["lane"] = joined.apply(lambda r: to_lane_key(r["origin"], r["destination"]), axis=1)
    lane_stats = joined.groupby("lane")["hours"].agg(["mean","count"]).reset_index()
    lane_stats.columns = ["lane","mean_hours","count"]
    lane_stats.replace([np.inf, -np.inf], pd.NA, inplace=True)
    return lane_stats
