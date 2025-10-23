# tests/test_auto_routes.py
import json
import pathlib
import pytest
from starlette.testclient import TestClient

# Import the FastAPI app
from agents_boot.server.api import api

client = TestClient(api)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "service": "novachain"}


def test_spec_file_exists():
    spec_path = pathlib.Path("contracts/auto_routes.json")
    assert spec_path.exists(), "contracts/auto_routes.json is missing"
    # also validate it parses as JSON
    json.loads(spec_path.read_text(encoding="utf-8"))


def test_auto_ping():
    """Covers the default example route we ship in auto_routes.json."""
    r = client.get("/auto/ping")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "route": "auto/ping"}


# ----- Dynamic tests generated from contracts/auto_routes.json -----

def _load_spec():
    p = pathlib.Path("contracts/auto_routes.json")
    if not p.exists():
        return {"routes": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"routes": []}


_SPEC = _load_spec()
_PARAM_ROUTES = [
    (r.get("method", "GET"), r.get("path", "/"), r.get("status", 200), r.get("response"))
    for r in _SPEC.get("routes", [])
]

@pytest.mark.parametrize("method,path,expected_status,expected_json", _PARAM_ROUTES)
def test_routes_from_spec(method, path, expected_status, expected_json):
    """
    For every route in contracts/auto_routes.json, issue the request and
    assert on status + optional response body.
    """
    method = (method or "GET").upper()
    resp = client.request(method, path)
    assert resp.status_code == expected_status

    if expected_json is not None:
        # Starlette TestClient .json() returns Python dicts with True/False.
        assert resp.json() == expected_json
