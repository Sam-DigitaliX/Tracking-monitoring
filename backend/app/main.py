import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import alerts, clients, dashboard, ingest, monitoring, probes, sites
from app.api.ingest import start_flush_loop
from app.config import settings
from app.probes.scheduler import load_all_probes, start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("probr")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Probr starting up...")
    start_scheduler()
    await load_all_probes()
    flush_task = asyncio.create_task(start_flush_loop())
    logger.info("Probr ready")
    yield
    # Shutdown
    logger.info("Probr shutting down...")
    flush_task.cancel()
    try:
        await flush_task
    except asyncio.CancelledError:
        pass
    stop_scheduler()


app = FastAPI(
    title="Probr",
    description="Monitoring & alerting for client tracking infrastructure",
    version="0.1.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.allowed_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(clients.router, prefix="/api")
app.include_router(sites.router, prefix="/api")
app.include_router(probes.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(monitoring.router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "probr"}
