from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from novachain.db.models import Shipment, ShipmentEvent
from pathlib import Path
import json

def _emit_metric(name: str, value: float, tenant_id: str) -> None:
    Path(".data").mkdir(exist_ok=True)
    rec = {"ts": datetime.now(timezone.utc).isoformat(), "tenant": tenant_id, "name": name, "value": float(value)}
    with open(".data/metrics.jsonl", "a") as fh:
        fh.write(json.dumps(rec) + "\n")

def _as_aware_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def run_dq(session: Session, tenant_id: str) -> dict:
    latest = session.query(ShipmentEvent)\
        .filter(ShipmentEvent.tenant_id==tenant_id)\
        .order_by(ShipmentEvent.event_time.desc())\
        .first()
    if latest and latest.event_time:
        now = datetime.now(timezone.utc)
        ev = _as_aware_utc(latest.event_time)
        age_hours = (now - ev).total_seconds() / 3600.0
        freshness = 1.0 if age_hours <= 48 else 0.0
    else:
        freshness = 0.0

    shipments = session.query(Shipment).filter(Shipment.tenant_id==tenant_id).all()
    total = len(shipments)
    complete = 0
    for s in shipments:
        evs = session.query(ShipmentEvent)\
            .filter(ShipmentEvent.tenant_id==tenant_id,
                    ShipmentEvent.shipment_id==s.shipment_id)\
            .all()
        has_pu = any((e.stop_type or "").upper()=="PICKUP" for e in evs)
        has_dl = any((e.stop_type or "").upper()=="DELIVERY" for e in evs)
        if has_pu and has_dl: complete += 1
    completeness = (complete/total) if total else 0.0

    from sqlalchemy import func
    dup_groups = session.query(
        ShipmentEvent.shipment_id, ShipmentEvent.event_time, ShipmentEvent.stop_type, func.count()
    ).filter(ShipmentEvent.tenant_id==tenant_id)\
     .group_by(ShipmentEvent.shipment_id, ShipmentEvent.event_time, ShipmentEvent.stop_type)\
     .having(func.count() > 1).all()

    # Count only the redundant rows: sum(count-1) per dup group
    dup_overage = sum((c - 1) for *_k, c in dup_groups)
    total_events = session.query(ShipmentEvent).filter(ShipmentEvent.tenant_id==tenant_id).count()
    dup_rate = (dup_overage / total_events) if total_events else 0.0

    results = {"dq_freshness": freshness, "dq_completeness": completeness, "dq_dup_rate": dup_rate}
    for k, v in results.items():
        _emit_metric(k, v, tenant_id)
    return results
