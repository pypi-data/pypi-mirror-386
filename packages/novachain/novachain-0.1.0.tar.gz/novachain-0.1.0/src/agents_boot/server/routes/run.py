from __future__ import annotations
import json
from typing import Optional, Dict, Any, List, Tuple
from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import PlainTextResponse, StreamingResponse
from agents_boot.config import cfg
from agents_boot.agents.graph import app

router = APIRouter()

def _thread_cfg(thread_id: Optional[str]) -> Dict[str, Any]:
    # Required when a checkpointer is compiled into the graph
    return {"configurable": {"thread_id": thread_id or "default"}}

@router.post("/run")
def run_graph(
    intent: str = Body("ship v0"),
    recursion_limit: Optional[int] = Body(None),
    thread_id: Optional[str] = Body(None),
) -> Dict[str, Any]:
    try:
        return app.invoke({"intent": intent}, config=_thread_cfg(thread_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report", response_class=PlainTextResponse)
def get_report() -> str:
    try:
        with open(cfg.report_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "# No report yet\n"

@router.post("/stream/run")
def stream_run(
    intent: str = Body("ship v0"),
    recursion_limit: Optional[int] = Body(None),
    thread_id: Optional[str] = Body(None),
    # ask for both by default; UI can send "values" if it only wants step state
    stream_mode: Any = Body(["values", "custom"]),
) -> StreamingResponse:
    def gen():
        # When streaming multiple modes, LangGraph yields (mode, chunk) tuples
        for item in app.stream({"intent": intent}, config=_thread_cfg(thread_id), stream_mode=stream_mode):
            if isinstance(item, tuple) and len(item) == 2:
                mode, chunk = item  # e.g., ("values", {...}) or ("custom", {...})
            else:
                mode, chunk = "values", item

            if mode in ("values", "updates"):
                yield f"data: {json.dumps({'tick': chunk})}\n\n"
            elif mode == "custom":
                yield f"data: {json.dumps({'custom': chunk})}\n\n"
            else:
                # ignore other modes (messages/debug) unless you plan to surface them
                continue

        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
