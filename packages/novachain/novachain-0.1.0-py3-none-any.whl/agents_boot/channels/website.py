# src/agents_boot/channels/website.py
from __future__ import annotations
import json, os, pathlib, subprocess, shlex
from typing import Dict, Any
from .base import ChannelAdapter, Product, PublishResult

class WebsiteChannel(ChannelAdapter):
    """
    Writes canonical product + pricing JSON for your website.
    If config['deploy_cmd'] is set, it will execute it (e.g. "npm run deploy" or "make deploy").
    Config keys:
      - content_root: str (default "site_content")
      - deploy_cmd: Optional[str]
    """
    name = "website"

    def _root(self) -> pathlib.Path:
        root = pathlib.Path(self.config.get("content_root", "site_content"))
        (root / "products").mkdir(parents=True, exist_ok=True)
        return root

    def publish(self, p: Product) -> PublishResult:
        root = self._root()
        # products/<slug>.json
        product_path = root / "products" / f"{p.slug}.json"
        product_doc: Dict[str, Any] = json.loads(p.model_dump_json())
        product_path.write_text(json.dumps(product_doc, indent=2), encoding="utf-8")

        # pricing.json (aggregate of tiers across all products if desired)
        pricing_path = root / "pricing.json"
        pricing = {}
        if pricing_path.exists():
            try:
                pricing = json.loads(pricing_path.read_text(encoding="utf-8"))
            except Exception:
                pricing = {}
        pricing[p.slug] = [t.model_dump() for t in p.tiers]
        pricing_path.write_text(json.dumps(pricing, indent=2), encoding="utf-8")

        # optional deploy
        deploy_cmd = self.config.get("deploy_cmd")
        if deploy_cmd:
            subprocess.run(shlex.split(deploy_cmd), check=True)

        url = self.config.get("public_base_url")
        return PublishResult(channel=self.name, listing_url=f"{url}/{p.slug}" if url else None)
