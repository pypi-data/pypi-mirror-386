from __future__ import annotations
import json, os
from typing import Any, Dict, List
from fastapi import APIRouter
from fastapi.responses import JSONResponse

SPEC_PATH = os.getenv("AUTO_ROUTES_PATH", "contracts/auto_routes.json")

def _load_spec(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_router(spec_path: str = SPEC_PATH) -> APIRouter:
    router = APIRouter(prefix="", tags=["auto-routes"])
    spec = _load_spec(spec_path)
    for r in spec.get("routes", []):
        method = (r.get("method", "GET") or "GET").upper()
        path = r["path"]
        status = int(r.get("status", 200))
        response = r.get("response", {})

        async def handler(resp=response, sc=status):
            return JSONResponse(content=resp, status_code=sc)

        router.add_api_route(path, handler, methods=[method])
    return router

router = build_router(SPEC_PATH)
