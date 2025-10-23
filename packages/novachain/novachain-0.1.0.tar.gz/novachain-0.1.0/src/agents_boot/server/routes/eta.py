from __future__ import annotations
from fastapi import APIRouter, HTTPException
from typing import List
from novachain.domain.schemas import Shipment, ShipmentEvent, ETARequest, ETAResponse
from novachain.data.ingest.csv_ingestor import load_shipments, load_events, build_lane_stats
from novachain.services.eta.service import ETABaseline

router = APIRouter(prefix="/api/eta", tags=["eta"])
_state = {"shipments": [], "events": [], "model": ETABaseline()}

@router.post("/ingest")
def ingest(shipments_csv: str, events_csv: str) -> dict:
    _state["shipments"] = load_shipments(shipments_csv)
    _state["events"] = load_events(events_csv)
    stats = build_lane_stats(_state["events"], _state["shipments"])
    _state["model"].retrain(stats)
    return {"ok": True, "lanes": len(stats)}

@router.post("/predict", response_model=ETAResponse)
def predict(req: ETARequest):
    sh = next((s for s in _state["shipments"] if s.shipment_id == req.shipment_id), None)
    if not sh:
        raise HTTPException(404, f"Unknown shipment_id {req.shipment_id}")
    return _state["model"].predict(req, _state["events"], sh.origin, sh.destination)
