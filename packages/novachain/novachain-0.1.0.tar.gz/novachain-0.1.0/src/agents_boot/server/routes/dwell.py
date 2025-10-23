from __future__ import annotations
from fastapi import APIRouter
from novachain.domain.schemas import DwellObservation
from novachain.data.ingest.csv_ingestor import load_dwell
from novachain.services.dwell.service import DwellService

router = APIRouter(prefix="/api/dwell", tags=["dwell"])
_state = {"dwell": [], "svc": DwellService()}

@router.post("/ingest")
def ingest(dwell_csv: str) -> dict:
    _state["dwell"] = load_dwell(dwell_csv)
    _state["svc"].retrain(_state["dwell"])
    return {"ok": True, "facilities": len({d.facility_id for d in _state["dwell"]})}

@router.get("/facility")
def facility(facility_id: str) -> dict:
    return {"facility_id": facility_id, "mean_dwell_hours": _state["svc"].get_dwell(facility_id)}
