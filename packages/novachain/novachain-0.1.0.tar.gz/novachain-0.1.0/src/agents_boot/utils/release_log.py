from __future__ import annotations
import json, pathlib, time
from typing import Any, Dict, List, Optional

DEFAULT_PATH = "site_content/releases/index.json"

def _load(path: str = DEFAULT_PATH) -> Dict[str, Any]:
    p = pathlib.Path(path)
    if not p.exists():
        return {"history": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"history": []}

def append(product_id: str, product_slug: str, version: str, results: List[Dict[str, Any]], errors: List[str], path: str = DEFAULT_PATH) -> None:
    p = pathlib.Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    doc = _load(path)
    entry = {"ts": int(time.time()), "product_id": product_id, "product_slug": product_slug, "version": version, "results": results, "errors": errors}
    doc["history"].append(entry)
    p.write_text(json.dumps(doc, indent=2), encoding="utf-8")

def latest(product_id: str, path: str = DEFAULT_PATH) -> Optional[Dict[str, Any]]:
    doc = _load(path)
    items = [e for e in doc.get("history", []) if e.get("product_id") == product_id]
    return items[-1] if items else None

def list_history(product_id: Optional[str] = None, limit: int = 50, path: str = DEFAULT_PATH) -> List[Dict[str, Any]]:
    doc = _load(path)
    items = doc.get("history", [])
    if product_id:
        items = [e for e in items if e.get("product_id") == product_id]
    return items[-limit:]
