from __future__ import annotations
from typing import Any, Dict, List, Union
import json

Issue = str

# Public API expected by tests:
# validate_spec(input) -> List[Issue]
def validate_spec(spec: Union[str, Dict[str, Any]]) -> List[Issue]:
    """
    Accepts either:
      - dict (auto-routes JSON spec)
      - str  (either JSON text or free-text PRD)
    Returns a list of issue codes (empty list == OK).
    """
    # Normalize input
    data: Dict[str, Any] | None = None
    if isinstance(spec, dict):
        data = spec
    elif isinstance(spec, str):
        # Try parse JSON string. If it fails, treat as free-text PRD.
        try:
            data = json.loads(spec)
        except Exception:
            data = None
            text = spec
            return _lint_free_text_prd(text)

    # If we have a dict, validate as auto-routes spec
    if isinstance(data, dict):
        return _lint_auto_routes_spec(data)

    # Fallback (shouldn't happen), flag generic
    return ["spec.unrecognized"]

def _lint_auto_routes_spec(data: Dict[str, Any]) -> List[Issue]:
    issues: List[Issue] = []
    routes = data.get("routes")
    if not isinstance(routes, list) or not routes:
        issues.append("spec.routes.missing")
        return issues

    for i, r in enumerate(routes):
        if not isinstance(r, dict):
            issues.append(f"spec.routes[{i}].not_object")
            continue
        if not r.get("path"):
            issues.append(f"spec.routes[{i}].path.missing")
        if not r.get("method"):
            issues.append(f"spec.routes[{i}].method.missing")
        if "status" not in r:
            issues.append(f"spec.routes[{i}].status.missing")
        if "response" not in r:
            issues.append(f"spec.routes[{i}].response.missing")
    return issues

def _lint_free_text_prd(text: str) -> List[Issue]:
    t = text.lower()
    issues: List[Issue] = []

    if "prd" not in t:
        issues.append("spec.missing_prd_keyword")
    if not any(k in t for k in ("api", "endpoint", "route")):
        issues.append("spec.missing_api_section")
    if not any(k in t for k in ("acceptance test", "acceptance tests", "test cases")):
        issues.append("spec.missing_acceptance_tests")

    return issues
