from __future__ import annotations
import pandas as pd
from novachain.domain.schemas import DwellObservation

class DwellService:
    """Facility dwell time using rolling mean in hours."""
    def __init__(self):
        self._means = {}  # facility_id -> hours

    def retrain(self, dwell_obs: list[DwellObservation]) -> None:
        df = pd.DataFrame([{"facility_id": d.facility_id, "hours": d.dwell_hours} for d in dwell_obs])
        if df.empty:
            self._means = {}
            return
        self._means = df.groupby("facility_id")["hours"].mean().to_dict()

    def get_dwell(self, facility_id: str) -> float:
        return float(self._means.get(facility_id, 12.0))  # default 12h
