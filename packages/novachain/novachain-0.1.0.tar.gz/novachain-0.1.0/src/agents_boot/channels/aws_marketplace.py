# src/agents_boot/channels/aws_marketplace.py
from __future__ import annotations
import json, time
from typing import Dict, Any, Optional
from .base import ChannelAdapter, Product, PublishResult

class AWSMarketplaceChannel(ChannelAdapter):
    """
    Config keys:
      - region_name: Optional[str]
      - entity_id: str  # SaaS product entity id, e.g. "prod-xxxx"
      - release_notes_template: Optional[str]  # Jinja-ish template or static string
      - poll_seconds: int (default 5)
      - dry_run: bool (default False)  # if True, do not call AWS
    """
    name = "aws_marketplace"

    def validate(self, p: Product) -> None:
        if not self.config.get("entity_id"):
            raise ValueError("AWS Marketplace entity_id missing in config")
        if "aws_marketplace" in p.channel_ids and not p.channel_ids["aws_marketplace"]:
            raise ValueError("Product.channel_ids['aws_marketplace'] must be the product entity id")

    def _release_notes(self, p: Product) -> str:
        tpl = self.config.get("release_notes_template") or "Release {{version}} for {{name}}"
        # tiny, safe templating
        return tpl.replace("{{version}}", p.version).replace("{{name}}", p.name)

    def publish(self, p: Product) -> PublishResult:
        if self.config.get("dry_run"):
            return PublishResult(channel=self.name, status="noop", details={"dry_run": True})

        import boto3  # lazy import
        client = boto3.client("marketplace-catalog", region_name=self.config.get("region_name"))

        entity_id = p.channel_ids.get("aws_marketplace") or self.config["entity_id"]

        details = {
            "ProductTitle": p.name,
            "ShortDescription": (p.description or "")[:255],
            "LongDescription": p.description,
            "LatestVersion": {
                "VersionTitle": p.version,
                "ReleaseNotes": self._release_notes(p),
            },
        }

        change = {
            "ChangeType": "UpdateEntity",
            "Entity": {"Identifier": entity_id, "Type": "SaaSProduct"},
            "DetailsDocument": details,
        }

        resp = client.start_change_set(
            Catalog="AWSMarketplace",
            ChangeSetName=f"{p.slug}-{p.version}",
            ChangeSet=[change],
        )
        change_set_arn = resp["ChangeSetArn"]

        poll = int(self.config.get("poll_seconds", 5))
        status: Optional[str] = None
        while True:
            out = client.describe_change_set(Catalog="AWSMarketplace", ChangeSetArn=change_set_arn)
            status = out.get("Status")
            if status in ("APPLY_SUCCESSFUL", "APPLY_FAILED", "CANCELLED"):
                break
            time.sleep(poll)

        if status != "APPLY_SUCCESSFUL":
            return PublishResult(channel=self.name, status="error", details={"change_set_status": status})

        listing_url = self.config.get("listing_url")  # optional static link for now
        return PublishResult(channel=self.name, listing_url=listing_url, listing_id=entity_id)

    def update_pricing(self, p: Product) -> PublishResult:
        # Pricing via AWS Marketplace offers/terms is also change-set driven.
        # This function would assemble the offer/terms JSON and submit a change set.
        # For safety we leave it as a noop unless explicitly implemented by you.
        return PublishResult(channel=self.name, status="noop", details={"note": "Implement offer/terms changes when ready."})
