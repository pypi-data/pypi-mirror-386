from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Float, UniqueConstraint

class Base(DeclarativeBase):
    pass

class Shipment(Base):
    __tablename__ = "shipments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "shipment_id", name="uq_shipment_tenant_id_shipment_id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    shipment_id: Mapped[str] = mapped_column(String(64), index=True)
    origin: Mapped[str] = mapped_column(String(64))
    destination: Mapped[str] = mapped_column(String(64))
    mode: Mapped[str] = mapped_column(String(16), default="TL")
    carrier: Mapped[Optional[str]] = mapped_column(String(64), default=None)

class ShipmentEvent(Base):
    __tablename__ = "shipment_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "shipment_id", "event_time", "stop_type",
                         name="uq_event_tenant_sid_time_type"),
    )
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    shipment_id: Mapped[str] = mapped_column(String(64), index=True)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    city: Mapped[Optional[str]] = mapped_column(String(64), default=None)
    state: Mapped[Optional[str]] = mapped_column(String(64), default=None)
    facility_id: Mapped[Optional[str]] = mapped_column(String(64), default=None)
    stop_type: Mapped[str] = mapped_column(String(16), default="UNKNOWN")
    status: Mapped[Optional[str]] = mapped_column(String(128), default=None)
    lat: Mapped[Optional[float]] = mapped_column(default=None)
    lon: Mapped[Optional[float]] = mapped_column(default=None)

class DwellObservation(Base):
    __tablename__ = "dwell_obs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "facility_id", "arrival_time", "departure_time",
                         name="uq_dwell_tenant_facility_arrive_depart"),
    )
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    facility_id: Mapped[str] = mapped_column(String(64), index=True)
    arrival_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    departure_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
