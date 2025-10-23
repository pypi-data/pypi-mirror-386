import json, subprocess, sys, os, time
from pathlib import Path

# Keeping your golden set at its current path for now:
GOLDEN = Path("src/evals/golden.jsonl")
MIN_PASS = float(os.getenv("EVAL_MIN_PASS", "1.0"))

def run_case(intent: str) -> tuple[str, float]:
    t0 = time.perf_counter()
    out = subprocess.check_output([sys.executable, "-m", "agents_boot.agents.graph"]).decode()
    dt = (time.perf_counter() - t0) * 1000.0
    return out, dt

ok = 0; total = 0
for line in Path(GOLDEN).read_text().splitlines():
    case = json.loads(line); total += 1
    out, ms = run_case(case["intent"])
    if case["expect_contains"] in out:
        ok += 1

rate = ok / total if total else 0.0
print(f"eval_pass_rate={rate:.2f}")
if rate < MIN_PASS:
    sys.exit(1)
