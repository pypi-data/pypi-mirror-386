from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass
class AppConfig:
    # LangGraph persistence
    use_checkpointer: bool = os.getenv("USE_CHECKPOINTER", "1") == "1"
    sqlite_path: str = os.getenv("CHECKPOINT_DB", ".data/novachain-checkpoints.sqlite")
    # Graph execution
    recursion_limit: int = int(os.getenv("RECURSION_LIMIT", "25"))
    max_attempts: int = int(os.getenv("MAX_ATTEMPTS", "3"))
    latency_budget_ms: float = float(os.getenv("LATENCY_BUDGET_MS", "500"))
    # Reports
    report_path: str = os.getenv("REPORT_PATH", "docs/eval_report.md")

cfg = AppConfig()
