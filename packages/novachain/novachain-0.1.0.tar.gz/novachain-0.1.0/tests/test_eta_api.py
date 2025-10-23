import json
from fastapi.testclient import TestClient
from agents_boot.server.api import app

client = TestClient(app)

def test_eta_roundtrip(tmp_path):
    shipments = tmp_path/"shipments.csv"
    events = tmp_path/"events.csv"
    shipments.write_text("shipment_id,origin,destination\nS1,CHI,NYC\n")
    events.write_text(
        "shipment_id,event_time,stop_type\n"
        "S1,2025-01-01T08:00:00Z,PICKUP\n"
        "S1,2025-01-03T16:00:00Z,DELIVERY\n"
    )
    r = client.post("/api/eta/ingest", params={"shipments_csv": str(shipments), "events_csv": str(events)})
    assert r.json()["ok"]
    pred = client.post("/api/eta/predict", json={"shipment_id": "S1"}).json()
    assert pred["shipment_id"] == "S1"
    assert "predicted_arrival" in pred
