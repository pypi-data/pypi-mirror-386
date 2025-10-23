from __future__ import annotations
import os, json
from novachain.db.session import session_scope
from .checks import run_dq

def main():
    tenant = os.getenv("DQ_TENANT", "public")
    with session_scope() as s:
        res = run_dq(s, tenant)
    print(json.dumps({"tenant": tenant, "results": res}, indent=2))

if __name__ == "__main__":
    main()
