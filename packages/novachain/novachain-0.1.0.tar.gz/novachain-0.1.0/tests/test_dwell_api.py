from fastapi.testclient import TestClient
from agents_boot.server.api import app
from pathlib import Path

client = TestClient(app)

def test_dwell(tmp_path: Path):
    dwell = tmp_path/"dwell.csv"
    dwell.write_text(
        "facility_id,arrival_time,departure_time\n"
        "F1,2025-01-01T08:00:00Z,2025-01-01T20:00:00Z\n"
        "F1,2025-01-03T08:00:00Z,2025-01-03T18:00:00Z\n"
    )
    r = client.post("/api/dwell/ingest", params={"dwell_csv": str(dwell)})
    assert r.json()["ok"]
    r2 = client.get("/api/dwell/facility", params={"facility_id": "F1"})
    assert 11.0 <= r2.json()["mean_dwell_hours"] <= 13.0
