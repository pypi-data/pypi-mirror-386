from __future__ import annotations
from datetime import datetime, timedelta
import pandas as pd
from typing import Optional
from novachain.domain.schemas import ETARequest, ETAResponse, ShipmentEvent
from novachain.data.ingest.csv_ingestor import to_lane_key

class ETABaseline:
    """Lane-average ETA baseline (fast, explainable)."""
    def __init__(self):
        self._lane_hours = {}  # lane -> mean transit hours

    def retrain(self, lane_stats: pd.DataFrame) -> None:
        self._lane_hours = {row["lane"]: float(row["mean_hours"]) for _, row in lane_stats.iterrows()}

    def predict(self, req: ETARequest, events: list[ShipmentEvent], origin: str, destination: str) -> ETAResponse:
        lane = to_lane_key(origin, destination)
        mean_hours = self._lane_hours.get(lane)
        if not mean_hours:
            # fallback: global mean 48h
            mean_hours = 48.0
        # pick most recent event for this shipment
        evs = [e for e in events if e.shipment_id == req.shipment_id]
        as_of = req.as_of or (max(e.event_time for e in evs) if evs else datetime.utcnow())
        predicted_arrival = as_of + timedelta(hours=mean_hours)
        conf = 0.5 if lane not in self._lane_hours else min(0.9, 0.6 + 0.3*(self._lane_hours[lane]>0))
        return ETAResponse(shipment_id=req.shipment_id, predicted_arrival=predicted_arrival, method="lane_avg", confidence=conf)
