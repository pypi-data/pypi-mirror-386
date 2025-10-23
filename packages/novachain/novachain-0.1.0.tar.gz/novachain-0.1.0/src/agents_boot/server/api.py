from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from agents_boot.server.routes.gtm import router as gtm_router
from agents_boot.server.routes.auto_routes import router as auto_router
from agents_boot.server.routes.console_gtm import router as console_gtm_router
from agents_boot.server.routes.run import router as run_router

# new DB-backed routers
from agents_boot.server.routes import ingest_db as ingest_db_routes
from agents_boot.server.routes import shipments as shipments_routes
from agents_boot.server.routes import eta_db as eta_db_routes
from agents_boot.server.routes import dwell_db as dwell_db_routes

# legacy ETA/Dwell routers (in-memory CSV path)
from agents_boot.server.routes import eta as eta_routes
from agents_boot.server.routes import dwell as dwell_routes

from agents_boot.observability.otel import init_otel
from novachain.db.session import init_db

api = FastAPI(title="NovaChain API", version="0.2.0")

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.get("/health")
def health():
    return {"ok": True, "service": "novachain"}

@api.get("/console")
def console_root():
    return RedirectResponse("/console/gtm", status_code=303)

# Existing surfaces
api.include_router(gtm_router)
api.include_router(auto_router)
api.include_router(console_gtm_router, prefix="/console")
api.include_router(run_router)

# New DB-backed surfaces
api.include_router(ingest_db_routes.router)
api.include_router(shipments_routes.router)
api.include_router(eta_db_routes.router)
api.include_router(dwell_db_routes.router)

# Legacy ETA/Dwell (still available)
api.include_router(eta_routes.router)
api.include_router(dwell_routes.router)

# Init DB and instrumentation
init_db()  # create tables if missing (dev); for prod use Alembic migrations
instrument = init_otel("novachain")
api = instrument(api)

# Back-compat alias
app = api
