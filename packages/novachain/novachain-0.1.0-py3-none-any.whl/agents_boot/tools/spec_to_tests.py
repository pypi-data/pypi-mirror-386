from __future__ import annotations
import json, os
from typing import Any, Dict

_DEFAULT_SPEC = os.getenv("AUTO_ROUTES_PATH", "contracts/auto_routes.json")

_TEMPLATE = """# Auto-generated; do not edit by hand
import pytest
from fastapi.testclient import TestClient
from agents_boot.server.api import api

@pytest.fixture(scope="module")
def client():
    with TestClient(api) as c:
        yield c
{cases}
"""

_CASE = """

def test_{name}(client):
    r = client.{method}({path_literal})
    assert r.status_code == {status}
    assert r.json() == {response_literal}
"""

def _canon_name(method: str, path: str) -> str:
    p = path.strip('/').replace('/', '_').replace('-', '_') or 'root'
    return f"{method.lower()}_{p}"

def generate_tests(spec_path: str | None = None, out_file: str = "tests/test_auto_routes.py") -> int:
    spec_path = spec_path or _DEFAULT_SPEC
    with open(spec_path, 'r', encoding='utf-8') as f:
        spec: Dict[str, Any] = json.load(f)

    routes = spec.get('routes', [])
    parts: list[str] = []
    count = 0
    for r in routes:
        method = (r.get('method', 'GET') or 'GET').lower()
        path = r.get('path', '/')
        name = _canon_name(method, path)
        path_literal = repr(path)          # Python literal
        response_literal = repr(r.get('response', {}))  # Python literal
        case = _CASE.format(
            name=name, method=method, path_literal=path_literal,
            status=int(r.get('status', 200)), response_literal=response_literal
        )
        parts.append(case); count += 1

    if not parts: return 0
    os.makedirs(os.path.dirname(out_file) or ".", exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(_TEMPLATE.format(cases="".join(parts)))
    return count
