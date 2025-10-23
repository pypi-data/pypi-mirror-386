from __future__ import annotations
import json, os, pathlib
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from agents_boot.channels.base import Product, PublishResult
from agents_boot.agents.gtm_graph import run_release, default_adapters
from agents_boot.agents.post_release_graph import run_post_release
from agents_boot.utils import release_log

router = APIRouter(prefix="/gtm", tags=["gtm"])

CATALOG_PATH = os.environ.get("PRODUCT_CATALOG_PATH", "products/catalog.json")
CFG_ENV = "CHANNELS_CONFIG_JSON"

class ReleaseRequest(BaseModel):
    product_id: str
    channels: Optional[List[str]] = None
    config: Dict[str, Any] = {}

class PostRequest(BaseModel):
    product_id: str
    config: Dict[str, Any] = {}

def _load_catalog() -> Dict[str, Any]:
    p = pathlib.Path(CATALOG_PATH)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"catalog not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))

def _load_product(product_id: str) -> Product:
    cat = _load_catalog()
    for item in cat.get("products", []):
        if item.get("id") == product_id:
            return Product(**item)
    raise HTTPException(status_code=404, detail=f"product not in catalog: {product_id}")

def _cfg() -> Dict[str, Any]:
    raw = os.environ.get(CFG_ENV)
    return json.loads(raw) if raw else {}

@router.get("/catalog")
def get_catalog():
    return _load_catalog()

@router.get("/channels")
def get_channels():
    return {"ok": True, "channels": list(default_adapters(_cfg()).keys())}

@router.get("/history")
def get_history(product_id: str = Query(...), limit: int = Query(20, ge=1, le=200)):
    items = release_log.list_history(product_id=product_id, limit=limit)
    latest = items[-1] if items else None
    return {"ok": True, "latest": latest, "items": items}

@router.post("/release")
def post_release(req: ReleaseRequest):
    product = _load_product(req.product_id)
    cfg = _cfg()
    # per-request overrides
    for k, v in (req.config or {}).items():
        cfg[k] = {**cfg.get(k, {}), **v}
    adapters = default_adapters(cfg)
    if req.channels:
        adapters = {k: adapters[k] for k in req.channels if k in adapters}
        if not adapters:
            raise HTTPException(status_code=400, detail="no valid channels selected")

    out = run_release(product, adapters)
    release_log.append(product.id, product.slug, product.version, out["results"], out["errors"])
    return {"ok": True, **out}

@router.post("/post")
def post_post(req: PostRequest):
    product = _load_product(req.product_id)
    latest = release_log.latest(product.id)
    release_results: List[PublishResult] = []
    if latest:
        release_results = [PublishResult(**r) for r in latest.get("results", [])]
    cfg = _cfg()
    out = run_post_release(product, release_results, cfg.get("post", {"content_root": "site_content"}))
    return {"ok": True, **out}

@router.post("/release_full")
def post_release_full(req: ReleaseRequest):
    rel = post_release(req)  # type: ignore
    product = _load_product(req.product_id)
    post = run_post_release(
        product,
        [PublishResult(**r) for r in rel["results"]],
        _cfg().get("post", {"content_root": "site_content"})
    )
    return {"ok": True, "release": rel, "post": post}
