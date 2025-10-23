from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from novachain.db.session import get_session
from novachain.db.models import Shipment, ShipmentEvent
from agents_boot.server.deps.auth import require_api_key, get_tenant

router = APIRouter(prefix="/api", tags=["shipments"])

@router.get("/shipments")
def list_shipments(
    limit: int = 50, offset: int = 0,
    session: Session = Depends(get_session),
    _: None = Depends(require_api_key),
    tenant_id: str = Depends(get_tenant),
):
    q = session.query(Shipment).filter(Shipment.tenant_id == tenant_id).order_by(Shipment.id).offset(offset).limit(limit)
    items = [dict(
        shipment_id=s.shipment_id, origin=s.origin, destination=s.destination,
        mode=s.mode, carrier=s.carrier
    ) for s in q.all()]
    return {"items": items, "limit": limit, "offset": offset}

@router.get("/shipments/{shipment_id}/events")
def shipment_events(
    shipment_id: str,
    session: Session = Depends(get_session),
    _: None = Depends(require_api_key),
    tenant_id: str = Depends(get_tenant),
):
    q = session.query(ShipmentEvent).filter(
        ShipmentEvent.tenant_id == tenant_id,
        ShipmentEvent.shipment_id == shipment_id
    ).order_by(ShipmentEvent.event_time)
    return {"shipment_id": shipment_id, "events": [dict(
        event_time=e.event_time.isoformat(),
        stop_type=e.stop_type, status=e.status,
        city=e.city, state=e.state, facility_id=e.facility_id,
        lat=e.lat, lon=e.lon
    ) for e in q.all()]}
