# src/agents_boot/tools/repo_search.py
from __future__ import annotations
from pathlib import Path
from typing import List

def has_api_markers(root: str = ".") -> List[str]:
    """Return a list of markdown files that look like they mention API routes."""
    hits: List[str] = []
    for p in Path(root).rglob("*.md"):
        try:
            s = p.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            continue
        if "api" in s and ("route" in s or "endpoint" in s):
            hits.append(str(p))
    return hits
