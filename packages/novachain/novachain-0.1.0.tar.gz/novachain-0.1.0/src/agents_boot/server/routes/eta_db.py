from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from novachain.db.session import get_session
from novachain.db.models import Shipment, ShipmentEvent
from novachain.domain.schemas import ETARequest
from novachain.data.ingest.csv_ingestor import build_lane_stats
from novachain.services.eta.service import ETABaseline
from agents_boot.server.deps.auth import require_api_key, get_tenant

router = APIRouter(prefix="/api/eta/db", tags=["eta-db"])
_model_cache: dict[str, ETABaseline] = {}

def _model_for_tenant(tenant_id: str, session: Session) -> ETABaseline:
    key = tenant_id
    if key in _model_cache:
        return _model_cache[key]
    # build on the fly from DB
    shipments = session.query(Shipment).filter(Shipment.tenant_id == tenant_id).all()
    events = session.query(ShipmentEvent).filter(ShipmentEvent.tenant_id == tenant_id).all()
    # adapt to Pydantic models expected by build_lane_stats/ETABaseline
    from novachain.domain.schemas import Shipment as PShip, ShipmentEvent as PEvent
    pships = [PShip(shipment_id=s.shipment_id, origin=s.origin, destination=s.destination, mode=s.mode, carrier=s.carrier) for s in shipments]
    pevents = [PEvent(shipment_id=e.shipment_id, event_time=e.event_time, city=e.city, state=e.state,
                      facility_id=e.facility_id, stop_type=e.stop_type, status=e.status, lat=e.lat, lon=e.lon) for e in events]
    stats = build_lane_stats(pevents, pships)
    m = ETABaseline(); m.retrain(stats)
    _model_cache[key] = m
    return m

@router.post("/predict")
def predict(
    req: ETARequest,
    session: Session = Depends(get_session),
    _: None = Depends(require_api_key),
    tenant_id: str = Depends(get_tenant),
):
    sh = session.query(Shipment).filter(Shipment.tenant_id==tenant_id, Shipment.shipment_id==req.shipment_id).first()
    if not sh:
        raise HTTPException(404, f"Unknown shipment_id {req.shipment_id}")
    events = session.query(ShipmentEvent).filter(ShipmentEvent.tenant_id==tenant_id).all()
    from novachain.domain.schemas import ShipmentEvent as PEvent
    pevents = [PEvent(shipment_id=e.shipment_id, event_time=e.event_time, city=e.city, state=e.state,
                      facility_id=e.facility_id, stop_type=e.stop_type, status=e.status, lat=e.lat, lon=e.lon) for e in events]
    model = _model_for_tenant(tenant_id, session)
    resp = model.predict(req, pevents, sh.origin, sh.destination)
    return resp.model_dump()
