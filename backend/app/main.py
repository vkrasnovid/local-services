from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Local Services Marketplace API")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Local Services Marketplace",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 routers
from app.api.v1 import auth, masters, slots, bookings, reviews, chat, notifications, admin, categories, upload, payments

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(categories.router, prefix="/api/v1/categories", tags=["categories"])
app.include_router(masters.router, prefix="/api/v1/masters", tags=["masters"])
app.include_router(slots.router, prefix="/api/v1", tags=["slots"])
app.include_router(bookings.router, prefix="/api/v1/bookings", tags=["bookings"])
app.include_router(reviews.router, prefix="/api/v1/reviews", tags=["reviews"])
app.include_router(chat.router, prefix="/api/v1/chats", tags=["chat"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["upload"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])

# WebSocket
from app.ws.chat import chat_websocket
app.add_api_websocket_route("/ws/chat/{room_id}", chat_websocket)

# Static files for uploads
import os
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
