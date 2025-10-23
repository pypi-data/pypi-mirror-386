# src/agents_boot/channels/base.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# --- Canonical product/pricing models ---

class Tier(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    monthly_price: Optional[float] = None
    annual_price: Optional[float] = None
    currency: str = "USD"
    metered: bool = False
    features: List[str] = []

class Product(BaseModel):
    id: str
    name: str
    version: str
    description: str
    slug: str
    docs_url: Optional[str] = None
    repo_url: Optional[str] = None
    # artifacts: names known to adapters, e.g. docker_image, wheel_path
    artifacts: Dict[str, str] = Field(default_factory=dict)
    tiers: List[Tier] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    # channel -> listing_id (e.g., AWS SaaS product entity id, docker repo, etc.)
    channel_ids: Dict[str, str] = Field(default_factory=dict)

class PublishResult(BaseModel):
    channel: str
    status: str = "success"   # success | noop | error
    listing_url: Optional[str] = None
    listing_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)

# --- Channel adapter contract ---

class ChannelAdapter(ABC):
    """Each adapter maps the canonical Product -> channel-specific operations."""
    name: str

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def validate(self, p: Product) -> None:
        """Raise ValueError if required product fields are missing for this channel."""
        return None

    @abstractmethod
    def publish(self, p: Product) -> PublishResult:
        """Create or update listing/content for this product/version."""
        ...

    def update_pricing(self, p: Product) -> PublishResult:
        """Optional channel-specific pricing update."""
        return PublishResult(channel=self.name, status="noop")
