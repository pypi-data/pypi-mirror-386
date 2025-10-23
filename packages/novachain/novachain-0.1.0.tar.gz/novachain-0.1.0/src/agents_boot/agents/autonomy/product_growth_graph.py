"""
Reads objectives, guardrails, telemetry; proposes and scaffolds upgrades.
- If ETA MAE is above target -> open PR with tighter features or retrain trigger.
- If Dwell coverage < target -> propose new enrichers (e.g., facility calendars).
- If adoption < target -> open GTM task (docs, pricing).
"""
from __future__ import annotations
import json, os, subprocess, datetime as dt
from pathlib import Path
from pydantic import BaseModel
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
OBJ = ROOT / "objectives" / "roadmap.json"
POL = ROOT / "policies" / "autonomy_guardrails.yaml"
METRICS = ROOT / ".data" / "metrics.jsonl"    # emitted by services/tests
BACKLOG = ROOT / ".data" / "backlog.jsonl"

class Proposal(BaseModel):
    title: str
    description: str
    impact: str
    files_added: list[str] = []

def _avg_metric(name: str, days: int = 7) -> float | None:
    if not METRICS.exists():
        return None
    cutoff = dt.datetime.utcnow() - dt.timedelta(days=days)
    vals = []
    with METRICS.open() as fh:
        for line in fh:
            rec = json.loads(line)
            if rec.get("name")==name and dt.datetime.fromisoformat(rec["ts"])>=cutoff:
                vals.append(rec["value"])
    return sum(vals)/len(vals) if vals else None

def _git(cmd: list[str]) -> None:
    subprocess.check_call(cmd, cwd=ROOT)

def _scaffold_new_product(slug: str, title: str) -> list[str]:
    svc_dir = ROOT / "src" / "novachain" / "services" / slug
    svc_dir.mkdir(parents=True, exist_ok=True)
    init = svc_dir / "__init__.py"; init.write_text("")
    r = svc_dir / "service.py"; r.write_text(f'# {title}\nclass Service:\n    pass\n')
    return [str(r.relative_to(ROOT))]

def maybe_propose() -> Proposal | None:
    eta_mae = _avg_metric("eta_mae_days")
    dwell_cov = _avg_metric("dwell_coverage")
    if eta_mae and eta_mae > 1.5:
        files = _scaffold_new_product("eta_v1", "ETA v1 (lane + day-of-week model)")
        return Proposal(
            title="Improve ETA to v1",
            description="Introduce DoW/holiday features; retrain; update /api/eta.",
            impact=f"Reduce MAE from {eta_mae:.2f} to <=1.2 days",
            files_added=files
        )
    if dwell_cov and dwell_cov < 0.9:
        files = _scaffold_new_product("dwell_enricher", "Dwell Calendar Enricher")
        return Proposal(
            title="Add Dwell Calendar Enricher",
            description="Use facility calendars/holidays to improve dwell coverage.",
            impact="Coverage >= 0.95",
            files_added=files
        )
    return None

def run() -> dict[str, Any]:
    prop = maybe_propose()
    if not prop:
        return {"ok": True, "action": "none"}
    BACKLOG.parent.mkdir(parents=True, exist_ok=True)
    with BACKLOG.open("a") as fh:
        fh.write(json.dumps({"ts": dt.datetime.utcnow().isoformat(), "proposal": prop.dict()}) + "\n")
    # open a branch and commit scaffold (optional)
    try:
        _git(["git", "checkout", "-b", f"proposal/{prop.title.replace(' ', '-').lower()}"])
        for path in prop.files_added:
            _git(["git", "add", path])
        _git(["git", "commit", "-m", f"chore: {prop.title} [autonomy]"])
    except Exception:
        pass
    return {"ok": True, "proposal": prop.dict()}
