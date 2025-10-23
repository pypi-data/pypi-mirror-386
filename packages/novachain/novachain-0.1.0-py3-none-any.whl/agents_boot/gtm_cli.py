# src/agents_boot/gtm_cli.py
from __future__ import annotations
import argparse, json, os, sys
from agents_boot.channels.base import Product
from agents_boot.agents.gtm_graph import run_release, default_adapters

def main():
    ap = argparse.ArgumentParser("gtm")
    ap.add_argument("product_id")
    ap.add_argument("--channels", default="", help="comma-separated subset (website,aws_marketplace,dockerhub,pypi)")
    ap.add_argument("--config-json", default=os.environ.get("CHANNELS_CONFIG_JSON","{}"))
    ap.add_argument("--catalog", default=os.environ.get("PRODUCT_CATALOG_PATH","products/catalog.json"))
    args = ap.parse_args()

    catalog = json.load(open(args.catalog, "r", encoding="utf-8"))
    prod = None
    for p in catalog.get("products", []):
        if p.get("id") == args.product_id:
            prod = Product(**p); break
    if not prod:
        print(f"product_id={args.product_id!r} not found in {args.catalog}", file=sys.stderr)
        sys.exit(2)
    cfg = json.loads(args.config_json or "{}")
    adapters = default_adapters(cfg)
    if args.channels:
        # filter subset
        keep = [c.strip() for c in args.channels.split(",") if c.strip()]
        adapters = {k:v for k,v in adapters.items() if k in keep}

    out = run_release(prod, adapters)
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
