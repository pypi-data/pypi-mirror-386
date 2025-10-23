from __future__ import annotations
import os, json
from typing import Optional
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

# Docs: FastAPI API Key in headers. We use X-API-Key & X-Tenant-Id. :contentReference[oaicite:5]{index=5}
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
TENANT_HEADER = APIKeyHeader(name="X-Tenant-Id", auto_error=False)

def _load_api_key_map() -> dict[str, str]:
    """
    Map API key -> tenant_id
    Format: API_KEYS='{"tenantA":"key123","tenantB":"key456"}'
         or: API_KEYS='tenantA:key123,tenantB:key456'
    """
    raw = os.getenv("API_KEYS", "")
    if not raw:
        return {}
    try:
        obj = json.loads(raw)
        return {v: k for k, v in obj.items()}
    except Exception:
        pairs = [p.strip() for p in raw.split(",") if p.strip()]
        out = {}
        for p in pairs:
            tenant, key = [x.strip() for x in p.split(":", 1)]
            out[key] = tenant
        return out

_API_KEY_TO_TENANT = _load_api_key_map()
_DEFAULT_API_KEY = os.getenv("API_KEY")

def require_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> None:
    if _DEFAULT_API_KEY:
        if api_key != _DEFAULT_API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return
    # Multi-tenant map mode
    if api_key not in _API_KEY_TO_TENANT:
        raise HTTPException(status_code=401, detail="Invalid API key")

def get_tenant(
    api_key: Optional[str] = Security(API_KEY_HEADER),
    tenant_hdr: Optional[str] = Security(TENANT_HEADER)
) -> str:
    # Prefer explicit tenant header if provided and API key validates to same tenant
    if _DEFAULT_API_KEY:
        # Single-tenant mode; require header or fall back to "public"
        return tenant_hdr or "public"

    tenant_from_key = _API_KEY_TO_TENANT.get(api_key or "")
    if not tenant_from_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if tenant_hdr and tenant_hdr != tenant_from_key:
        raise HTTPException(status_code=403, detail="Tenant mismatch")
    return tenant_from_key
