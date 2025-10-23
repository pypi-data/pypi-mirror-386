from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from novachain.db.session import get_session
from novachain.db.models import DwellObservation
from novachain.services.dwell.service import DwellService
from novachain.domain.schemas import DwellObservation as PDwell
from agents_boot.server.deps.auth import require_api_key, get_tenant

router = APIRouter(prefix="/api/dwell/db", tags=["dwell-db"])
_cache: dict[str, DwellService] = {}

def _svc_for_tenant(tenant_id: str, session: Session) -> DwellService:
    if tenant_id in _cache:
        return _cache[tenant_id]
    rows = session.query(DwellObservation).filter(DwellObservation.tenant_id == tenant_id).all()
    svc = DwellService()
    svc.retrain([PDwell(facility_id=r.facility_id, arrival_time=r.arrival_time, departure_time=r.departure_time) for r in rows])
    _cache[tenant_id] = svc
    return svc

@router.get("/facility")
def facility(
    facility_id: str,
    session: Session = Depends(get_session),
    _: None = Depends(require_api_key),
    tenant_id: str = Depends(get_tenant),
):
    svc = _svc_for_tenant(tenant_id, session)
    return {"facility_id": facility_id, "mean_dwell_hours": svc.get_dwell(facility_id)}
