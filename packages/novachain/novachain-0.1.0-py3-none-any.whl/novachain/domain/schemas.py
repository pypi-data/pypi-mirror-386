from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Literal

StopType = Literal["PICKUP", "DELIVERY", "WAYPOINT", "UNKNOWN"]

class Shipment(BaseModel):
    shipment_id: str
    origin: str
    destination: str
    mode: Literal["TL","LTL","OCEAN","AIR","RAIL","INTERMODAL"] = "TL"
    carrier: Optional[str] = None

class ShipmentEvent(BaseModel):
    shipment_id: str
    event_time: datetime
    city: Optional[str] = None
    state: Optional[str] = None
    facility_id: Optional[str] = None
    stop_type: StopType = "UNKNOWN"  # map from EDI-214/315 statuses
    status: Optional[str] = None     # raw status text
    lat: Optional[float] = None
    lon: Optional[float] = None

class DwellObservation(BaseModel):
    facility_id: str
    arrival_time: datetime
    departure_time: datetime

    @property
    def dwell_hours(self) -> float:
        return (self.departure_time - self.arrival_time).total_seconds() / 3600

class ETARequest(BaseModel):
    shipment_id: str
    as_of: Optional[datetime] = None

class ETAResponse(BaseModel):
    shipment_id: str
    predicted_arrival: datetime
    method: str = Field(default="lane_avg")
    confidence: float = Field(ge=0, le=1, default=0.5)
