# src/agents_boot/agents/gtm_graph.py
from __future__ import annotations
from typing import Any, Dict, List, TypedDict, Optional
from pydantic import BaseModel
from langgraph.graph import StateGraph, END

from agents_boot.channels.base import Product, PublishResult, ChannelAdapter
from agents_boot.channels.website import WebsiteChannel
from agents_boot.channels.aws_marketplace import AWSMarketplaceChannel
from agents_boot.channels.dockerhub import DockerHubChannel
from agents_boot.channels.pypi import PyPIChannel

# If you already have a global checkpointer in agents_boot.agents.graph, we reuse it.
try:
    from agents_boot.agents.graph import _checkpointer as CHECKPOINTER  # type: ignore
except Exception:
    CHECKPOINTER = None

class ReleaseState(TypedDict):
    product: Product
    channel_order: List[str]
    results: List[PublishResult]
    errors: List[str]

def _validate(s: ReleaseState) -> ReleaseState:
    # Adapters validate channel-specific requirements
    return s

def _publish_factory(adapter: ChannelAdapter):
    def _node(s: ReleaseState) -> ReleaseState:
        try:
            adapter.validate(s["product"])
            out = adapter.publish(s["product"])
            return {"results": [*s["results"], out]}
        except Exception as e:
            return {"errors": [*s["errors"], f"{adapter.name}: {e}"]}
    return _node

def build_release_graph(adapters: Dict[str, ChannelAdapter]):
    g = StateGraph(ReleaseState)
    g.add_node("validate", _validate)

    # Add nodes in the order provided by channel_order
    for name, adapter in adapters.items():
        g.add_node(f"publish_{name}", _publish_factory(adapter))

    # Edges
    g.set_entry_point("validate")
    prev = "validate"
    for name in adapters.keys():
        g.add_edge(prev, f"publish_{name}")
        prev = f"publish_{name}"
    g.add_edge(prev, END)

    return g.compile(checkpointer=CHECKPOINTER)

def default_adapters(config: Dict[str, Any]) -> Dict[str, ChannelAdapter]:
    """Create adapters from simple dict config."""
    return {
        "website": WebsiteChannel(config.get("website", {})),
        "aws_marketplace": AWSMarketplaceChannel(config.get("aws_marketplace", {})),
        "dockerhub": DockerHubChannel(config.get("dockerhub", {})),
        "pypi": PyPIChannel(config.get("pypi", {})),
    }

def run_release(product: Product, adapters: Dict[str, ChannelAdapter]) -> Dict[str, Any]:
    graph = build_release_graph(adapters)
    state: ReleaseState = {
        "product": product,
        "channel_order": list(adapters.keys()),
        "results": [],
        "errors": [],
    }
    out = graph.invoke(state)
    return {"results": [r.model_dump() for r in out["results"]], "errors": out["errors"]}
