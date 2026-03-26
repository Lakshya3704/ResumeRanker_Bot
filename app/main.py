"""
main.py – FastAPI application entry point.

Configures:
  • CORS middleware
  • Logging
  • Router registration
  • Static file serving for the web frontend
  • Health-check endpoint
"""

from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes.analyze import router as analyze_router
from app.routes.auth import router as auth_router
from app.models.schemas import HealthResponse
from app.services.database import close_database
from app.utils.helpers import setup_logging, get_env

logger = setup_logging("drcode.api")

# Path to web frontend
WEB_DIR = Path(__file__).resolve().parent.parent / "web"


# ──────────────────────────────────────────────
#  Lifespan events
# ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    logger.info("🚀 DRCode API starting up …")
    yield
    await close_database()
    logger.info("🛑 DRCode API shutting down.")


# ──────────────────────────────────────────────
#  Create app
# ──────────────────────────────────────────────

app = FastAPI(
    title="DRCode – AI Resume Analyzer",
    description=(
        "Analyze a resume against a job description, get a score out of 10, "
        "actionable suggestions, and optionally generate an improved resume."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ──
app.include_router(analyze_router, tags=["Analysis"])
app.include_router(auth_router)


# ── Health check ──
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Simple liveness probe."""
    return HealthResponse()


# ── Telegram bot username endpoint ──
@app.get("/api/config")
async def get_config():
    """Return public config for the frontend."""
    return {
        "telegram_bot_username": get_env("TELEGRAM_BOT_USERNAME", "DRCode_resume_bot"),
    }


# ── Serve static web frontend (MUST be last – catches all unmatched routes) ──
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
    logger.info("Serving web frontend from %s", WEB_DIR)
