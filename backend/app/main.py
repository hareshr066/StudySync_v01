"""StudySync FastAPI Application."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.mongodb import connect_to_mongodb, close_mongodb_connection, get_database, get_client
from app.db.indexes import create_indexes
from app.db.migration import migrate_foreign_keys
from app.api import auth, users, decks, cards, study, sessions, groups, rooms, notifications, ws, documents, notes, notebooks, ai
from app.api import conversations, quizzes, study_plans, search

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    logger.info("Starting StudySync API...")
    connect_to_mongodb()
    db = get_database()
    create_indexes(db)
    migrate_foreign_keys(db)
    logger.info("StudySync API ready")
    yield
    logger.info("Shutting down StudySync API...")
    close_mongodb_connection()


app = FastAPI(
    title="StudySync API",
    description="Collaborative spaced-repetition study platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(decks.router)
app.include_router(cards.router)
app.include_router(study.router)
app.include_router(sessions.router)
app.include_router(rooms.router)
app.include_router(groups.router)
app.include_router(notifications.router)
app.include_router(ws.router)
app.include_router(documents.router)
app.include_router(notes.router)
app.include_router(notebooks.router)
app.include_router(ai.router)
app.include_router(conversations.router)
app.include_router(quizzes.router)
app.include_router(study_plans.router)
app.include_router(search.router)


@app.get("/health")
async def health_check():
    """Health check with real database connectivity test."""
    try:
        client = get_client()
        client.admin.command("ping")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "database": "disconnected", "detail": str(e)})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
