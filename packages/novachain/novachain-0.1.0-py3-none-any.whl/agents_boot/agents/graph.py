# src/agents_boot/agents/graph.py
from __future__ import annotations
import os, sqlite3, pathlib, json
from typing import TypedDict, List, Optional, Dict, Any

from langgraph.graph import StateGraph, END
from langgraph.config import get_stream_writer  # emits custom stream data

from agents_boot.config import cfg
from agents_boot.tools.repo_search import has_api_markers
from agents_boot.tools.spec_linter import validate_spec
from agents_boot.evals.gate import run_gate
from agents_boot.agents.gtm_graph import run_release, default_adapters
from agents_boot.channels.base import Product

# ---- Optional persistence (SQLite checkpointer) ----
_checkpointer = None
if cfg.use_checkpointer:
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        pathlib.Path(cfg.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(cfg.sqlite_path, check_same_thread=False)
        _checkpointer = SqliteSaver(_conn)
    except Exception as e:
        # keep going in dev, but surface why persistence is off
        print(f"[agents-boot] WARNING: SQLite checkpointer unavailable: {e}")
        _checkpointer = None


# ---------- State schema ----------
class AppState(TypedDict, total=False):
    intent: str
    spec: str
    pr: str
    eval_gate: bool
    attempts: int
    logs: List[str]
    release: Dict[str, Any]


def _log(s: AppState, *parts: Any) -> None:
    logs = s.get("logs") or []
    logs.append(" ".join(str(p) for p in parts))
    s["logs"] = logs


def _load_product(product_id: Optional[str] = None, catalog_path: str = "products/catalog.json") -> Product:
    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    products = data.get("products") or []
    if not products:
        raise ValueError("No products defined in products/catalog.json")
    if product_id:
        for p in products:
            if p.get("id") == product_id:
                return Product(**p)
    return Product(**products[0])


# ---------- Nodes ----------
def coordinator(s: AppState) -> Dict[str, Any]:
    writer = get_stream_writer()  # NOTE: no keyword args; writer is a callable
    writer({"agent": "Coordinator", "msg": "Setting OKR & routing to ProductArchitect"})
    _log(s, "Coordinator: set OKR + route to ProductArchitect")
    return {}  # pass-through state


def product_architect(s: AppState) -> Dict[str, Any]:
    writer = get_stream_writer()
    # keep your older PRD feel, but compatible with spec linter
    prd = s.get("spec") or (
        "PRD v0.1: API routes, acceptance tests\n\n"
        "This PRD covers /gtm/release, /gtm/post, /auto/ping endpoints.\n\n"
        "Acceptance tests:\n- /health returns ok\n- /gtm/release returns results\n"
        "- post-release creates files in site_content/\n"
    )
    writer({"agent": "ProductArchitect", "msg": "Produced initial PRD"})
    _log(s, "ProductArchitect: produced PRD")
    return {"spec": prd}


def engineer(s: AppState) -> Dict[str, Any]:
    writer = get_stream_writer()
    attempts = int(s.get("attempts") or 0) + 1
    s["attempts"] = attempts

    intent = (s.get("intent") or "").lower().strip()
    writer({"agent": "Engineer", "msg": f"Attempt {attempts}: intent={intent!r}"})
    _log(s, f"Engineer: starting (attempt {attempts})")

    do_release = any(k in intent for k in ("ship", "release", "publish"))
    pr_text: Optional[str] = None
    spec_text: Optional[str] = s.get("spec")

    if do_release:
        cfg_json = os.getenv("CHANNELS_CONFIG_JSON", "{}")
        try:
            ch_cfg = json.loads(cfg_json) if cfg_json else {}
        except Exception as e:
            raise ValueError(f"Invalid CHANNELS_CONFIG_JSON: {e}") from e

        adapters = default_adapters(ch_cfg)
        product_id = os.getenv("DEFAULT_PRODUCT_ID")
        product = _load_product(product_id)

        writer({"agent": "Engineer", "msg": f"Running GTM release for {product.name} {product.version}…"})
        rel = run_release(product, adapters)
        s["release"] = rel
        _log(s, "[Engineer] release results:", json.dumps(rel, indent=2))
        writer({"agent": "Engineer", "msg": "Release completed"})

        channels = ", ".join(adapters.keys())
        # ensure the PRD satisfies the linter (explicit PRD/API/Acceptance tests language)
        spec_text = spec_text or f"""PRD: Release {product.name} {product.version}

We publish the new version across channels: {channels}.

Acceptance tests:
- /health returns ok
- /gtm/release returns results for requested channels
- docs and announcement files are generated in site_content/
"""
        pr_text = f"Release {product.name} {product.version} across {channels}."
    else:
        writer({"agent": "Engineer", "msg": "No release requested — preparing docs/tests maintenance PR"})
        spec_text = spec_text or """PRD: Product iteration

We will update the docs and run smoke tests.

Acceptance tests:
- docs build completes
- pytest suite passes
"""
        pr_text = "Docs and tests maintenance."

    _log(s, f"Engineer: opened PR; intent={'ship' if do_release else 'maint'}.")
    return {"spec": spec_text, "pr": pr_text, "attempts": attempts}


def qa_evals(s: AppState) -> Dict[str, Any]:
    writer = get_stream_writer()
    spec = s.get("spec") or ""
    pr = s.get("pr") or ""
    # run linter just for logging context (gate will run pytest + timing)
    issues = validate_spec(spec) if spec else ["spec.empty"]
    passed, details = run_gate(spec, pr, int(cfg.latency_budget_ms), cfg.report_path)
    writer({
        "agent": "QAEvals",
        "msg": f"Gate={'PASS' if passed else 'FAIL'}; "
               f"linter={'ok' if not issues else issues}; "
               f"latency_ms={details.get('latency_ms')}"
    })
    _log(s, f"QAEvals: gate={'pass' if passed else 'fail'}; latency_ms={details.get('latency_ms')}")
    return {"eval_gate": bool(passed)}


def repo_search_node(s: AppState) -> Dict[str, Any]:
    writer = get_stream_writer()
    hits = has_api_markers(".")
    writer({"agent": "RepoSearch", "msg": f"Found {len(hits)} API-marked docs"})
    _log(s, f"RepoSearch: API markers found in {len(hits)} file(s): {hits[:3]}")
    return {}  # terminal summary step


def backlog_node(s: AppState) -> Dict[str, Any]:
    writer = get_stream_writer()
    tries = int(s.get("attempts") or 0)
    writer({"agent": "Backlog", "msg": f"Gated out after attempts={tries}; handoff to human queue"})
    _log(s, f"Backlog: gated out after attempts={tries}; handoff to human queue")
    return {}


# ---------- Graph wiring (keeps your original shape) ----------
g = StateGraph(AppState)
g.add_node("Coordinator", coordinator)
g.add_node("ProductArchitect", product_architect)
g.add_node("Engineer", engineer)
g.add_node("QAEvals", qa_evals)
g.add_node("RepoSearch", repo_search_node)
g.add_node("Backlog", backlog_node)

g.set_entry_point("Coordinator")
g.add_edge("Coordinator", "ProductArchitect")
g.add_edge("ProductArchitect", "Engineer")
g.add_edge("Engineer", "QAEvals")
g.add_edge("RepoSearch", END)
g.add_edge("Backlog", END)

MAX_ATTEMPTS = cfg.max_attempts

def _route_after_qaevals(state: AppState) -> str:
    # If gate passes, do a final repo scan summary then END; else loop Engineer until max attempts, then Backlog.
    if state.get("eval_gate"):
        return "RepoSearch"
    tries = int(state.get("attempts") or 0)
    return "Engineer" if tries < MAX_ATTEMPTS else "Backlog"

g.add_conditional_edges(
    "QAEvals",
    _route_after_qaevals,
    {"RepoSearch": "RepoSearch", "Engineer": "Engineer", "Backlog": "Backlog"},
)

# Compile with (optional) checkpointer: remember to pass {"configurable":{"thread_id":"..."}}
# when invoking/streaming; required by LangGraph persistence.
app = g.compile(checkpointer=_checkpointer)
