import os
import sys
import time
import json
import pathlib
from datetime import datetime
from subprocess import run, PIPE
from agents_boot.config import cfg
from agents_boot.tools.spec_linter import validate_spec


def _repo_root() -> pathlib.Path:
    p = pathlib.Path(__file__).resolve()
    for parent in [p, *p.parents]:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return p.parents[3]


def _run_pytest_quiet() -> tuple[bool, str, str, str]:
    """Run pytest as a subprocess in repo root: python -m pytest -q tests"""
    cmd = [sys.executable, "-m", "pytest", "-q", "tests"]
    proc = run(cmd, cwd=_repo_root(), stdout=PIPE, stderr=PIPE, text=True)
    note = f"pytest_rc={proc.returncode}"
    return (proc.returncode == 0), note, (proc.stdout or ""), (proc.stderr or "")


def run_gate(
    spec: str,
    pr: str | None,
    default_budget_ms: int = 500,
    report_path: str = "docs/eval_report.md",
) -> tuple[bool, dict]:
    t0 = time.perf_counter()

    linter_issues = validate_spec(spec)
    lint_ok = len(linter_issues) == 0

    pytest_ok, pytest_note, py_out, py_err = _run_pytest_quiet()

    pr_ok = bool(pr)

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    budget_ms = float(os.getenv("LATENCY_BUDGET_MS", default_budget_ms))
    latency_ok = elapsed_ms <= budget_ms

    passed = lint_ok and pytest_ok and pr_ok and latency_ok
    details = {
        "lint_ok": lint_ok,
        "linter_issues": linter_issues,
        "pytest_ok": pytest_ok,
        "pytest_note": pytest_note,
        "pr_present": pr_ok,
        "latency_ms": round(elapsed_ms, 2),
        "latency_budget_ms": budget_ms,
    }

    path = (_repo_root() / (report_path or cfg.report_path))
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().isoformat(timespec="seconds")

    report = f"""# Eval Report — {ts}

**Gate result:** {'PASS' if passed else 'FAIL'}

- Lint OK: {lint_ok}{' (issues: ' + ', '.join(linter_issues) + ')' if not lint_ok else ''}
- Pytest OK: {pytest_ok} ({pytest_note})
- PR present: {pr_ok}
- Latency: {details['latency_ms']} ms (budget {details['latency_budget_ms']} ms)

### Pytest STDOUT
~~~text
{py_out.strip()}
~~~

### Pytest STDERR
~~~text
{py_err.strip()}
~~~

### Raw JSON
~~~json
{json.dumps(details, indent=2)}
~~~
"""
    path.write_text(report, encoding="utf-8")
    return passed, details
