from __future__ import annotations
from typing import Any, Dict, List, Optional, TypedDict
import json, os, pathlib, time
from pydantic import BaseModel
from langgraph.graph import StateGraph, END

from agents_boot.channels.base import Product, PublishResult

# Try to reuse global checkpointer if your app created one already
try:
    from agents_boot.agents.graph import _checkpointer as CHECKPOINTER  # type: ignore
except Exception:
    CHECKPOINTER = None

class PostReleaseState(TypedDict):
    product: Product
    release_results: List[PublishResult]
    config: Dict[str, Any]
    out_files: List[str]

def _root(p: Product, cfg: Dict[str, Any]) -> pathlib.Path:
    return pathlib.Path(cfg.get("content_root", "site_content"))

def _ensure_dirs(root: pathlib.Path) -> None:
    (root / "announcements").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)

def _write(path: pathlib.Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return str(path)

def _announce_md(s: PostReleaseState) -> str:
    p = s["product"]; cfg = s["config"]; root = _root(p, cfg)
    _ensure_dirs(root)
    md = f"""---
title: "{p.name} {p.version} released"
slug: "{p.slug}-{p.version}"
date: "{time.strftime('%Y-%m-%d')}"
---

## What’s new in {p.name} {p.version}

- Automated release across channels: {", ".join([r.channel for r in s["release_results"]])}
- See the docs at {p.docs_url or "docs/"}.

### Quick start
```bash
# Example install (if package published)
pip install {p.slug.replace('-', '_')}=={p.version}
```
"""
    path = root / "announcements" / f"{p.slug}-{p.version}.md"
    return _write(path, md)

def _docs_index_md(s: PostReleaseState) -> str:
    p = s["product"]; cfg = s["config"]; root = _root(p, cfg)
    _ensure_dirs(root)
    md = f"""# {p.name} {p.version}

Welcome to the {p.name} docs.

- Repo: {p.repo_url or "-"}
- Latest: {p.version}
"""
    path = root / "docs" / "index.md"
    return _write(path, md)

def _node_announce(s: PostReleaseState) -> Dict[str, Any]:
    path = _announce_md(s)
    return {"out_files": [*s["out_files"], path]}

def _node_docs_index(s: PostReleaseState) -> Dict[str, Any]:
    path = _docs_index_md(s)
    return {"out_files": [*s["out_files"], path]}

def build_post_release_graph():
    g = StateGraph(PostReleaseState)
    g.add_node("announce", _node_announce)
    g.add_node("docs_index", _node_docs_index)
    g.set_entry_point("announce")
    g.add_edge("announce", "docs_index")
    g.add_edge("docs_index", END)
    return g.compile(checkpointer=CHECKPOINTER)

def run_post_release(product: Product, release_results: List[PublishResult], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    graph = build_post_release_graph()
    state: PostReleaseState = {
        "product": product,
        "release_results": release_results,
        "config": config or {"content_root": "site_content"},
        "out_files": [],
    }
    # supply a thread id for the checkpointer
    thread_id = f"post-{product.slug}-{product.version}"
    out = graph.invoke(state, config={"configurable": {"thread_id": thread_id}})
    return {"out_files": out["out_files"]}
