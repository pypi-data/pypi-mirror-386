from __future__ import annotations
import json, os, pathlib, threading, time
from typing import Any, Dict, List, Optional

class ReleaseLog:
    def __init__(self, path: str | None = None):
        self.path = pathlib.Path(path or os.getenv("RELEASE_LOG_PATH", ".data/release_history.jsonl"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def append(self, product_id: str, slug: str, version: str, results: List[Dict[str, Any]], errors: List[str]) -> Dict[str, Any]:
        rec = {"ts": time.time(), "product_id": product_id, "slug": slug, "version": version, "results": results, "errors": errors}
        with self._lock:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
        return rec

    def _read_all(self) -> List[Dict[str, Any]]:
        if not self.path.exists(): return []
        out = []
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try: out.append(json.loads(line))
                    except Exception: pass
        return out

    def list_history(self, product_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        items = self._read_all()
        if product_id:
            items = [r for r in items if r.get("product_id") == product_id]
        items.sort(key=lambda r: r.get("ts", 0), reverse=True)
        return items[:limit]

    def latest(self, product_id: str) -> Optional[Dict[str, Any]]:
        items = self.list_history(product_id=product_id, limit=1)
        return items[0] if items else None

release_log = ReleaseLog()
