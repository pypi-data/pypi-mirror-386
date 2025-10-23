from __future__ import annotations
from fastapi import APIRouter, Depends, Query, Form, Body, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from novachain.db.session import get_session
from novachain.db.models import Shipment, ShipmentEvent, DwellObservation
from novachain.data.ingest.csv_ingestor import load_shipments, load_events, load_dwell
from agents_boot.server.deps.auth import require_api_key, get_tenant
from novachain.billing.stripe_meter import record_usage

router = APIRouter(prefix="/api/ingest/db", tags=["ingest-db"])

class CSVBody(BaseModel):
    shipments_csv: str | None = None
    events_csv: str | None = None
    dwell_csv: str | None = None

def _pick_path(q: str | None, f: str | None, b: str | None, name: str) -> str:
    path = q or f or b
    if not path:
        raise HTTPException(422, f"{name} is required (query ?{name}=..., or form {name}=..., or JSON body)")
    return path

@router.post("/shipments")
def ingest_shipments(
    shipments_csv_q: str | None = Query(default=None, alias="shipments_csv"),
    shipments_csv_f: str | None = Form(default=None, alias="shipments_csv"),
    body: CSVBody | None = Body(default=None),
    session: Session = Depends(get_session),
    _: None = Depends(require_api_key),
    tenant_id: str = Depends(get_tenant),
) -> dict:
    shipments_csv = _pick_path(shipments_csv_q, shipments_csv_f, (body.shipments_csv if body else None), "shipments_csv")
    rows = load_shipments(shipments_csv)
    inserted, skipped = 0, 0
    for r in rows:
        try:
            session.add(Shipment(
                tenant_id=tenant_id, shipment_id=r.shipment_id,
                origin=r.origin, destination=r.destination,
                mode=r.mode, carrier=r.carrier
            ))
            session.flush()
            inserted += 1
        except IntegrityError:
            session.rollback()
            skipped += 1
    session.commit()
    record_usage(tenant_id, "shipments_ingested", inserted)
    return {"ok": True, "ingested": inserted, "skipped_duplicates": skipped}

@router.post("/events")
def ingest_events(
    events_csv_q: str | None = Query(default=None, alias="events_csv"),
    events_csv_f: str | None = Form(default=None, alias="events_csv"),
    body: CSVBody | None = Body(default=None),
    session: Session = Depends(get_session),
    _: None = Depends(require_api_key),
    tenant_id: str = Depends(get_tenant),
) -> dict:
    events_csv = _pick_path(events_csv_q, events_csv_f, (body.events_csv if body else None), "events_csv")
    rows = load_events(events_csv)
    inserted, skipped = 0, 0
    for e in rows:
        try:
            session.add(ShipmentEvent(
                tenant_id=tenant_id, shipment_id=e.shipment_id,
                event_time=e.event_time, city=e.city, state=e.state,
                facility_id=e.facility_id, stop_type=e.stop_type, status=e.status,
                lat=e.lat, lon=e.lon
            ))
            session.flush()
            inserted += 1
        except IntegrityError:
            session.rollback()
            skipped += 1
    session.commit()
    record_usage(tenant_id, "events_ingested", inserted)
    return {"ok": True, "ingested": inserted, "skipped_duplicates": skipped}

@router.post("/dwell")
def ingest_dwell(
    dwell_csv_q: str | None = Query(default=None, alias="dwell_csv"),
    dwell_csv_f: str | None = Form(default=None, alias="dwell_csv"),
    body: CSVBody | None = Body(default=None),
    session: Session = Depends(get_session),
    _: None = Depends(require_api_key),
    tenant_id: str = Depends(get_tenant),
) -> dict:
    dwell_csv = _pick_path(dwell_csv_q, dwell_csv_f, (body.dwell_csv if body else None), "dwell_csv")
    rows = load_dwell(dwell_csv)
    inserted, skipped = 0, 0
    for d in rows:
        try:
            session.add(DwellObservation(
                tenant_id=tenant_id, facility_id=d.facility_id,
                arrival_time=d.arrival_time, departure_time=d.departure_time
            ))
            session.flush()
            inserted += 1
        except IntegrityError:
            session.rollback()
            skipped += 1
    session.commit()
    record_usage(tenant_id, "dwell_obs_ingested", inserted)
    return {"ok": True, "ingested": inserted, "skipped_duplicates": skipped}
