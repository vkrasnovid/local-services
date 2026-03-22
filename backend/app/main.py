from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(
    title="Local Services Marketplace",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Router placeholders — uncomment as modules are implemented
# from app.api.v1 import auth, catalog, booking, payment, chat, review, admin, notification, upload
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
# app.include_router(catalog.router, prefix="/api/v1/catalog", tags=["catalog"])
# app.include_router(booking.router, prefix="/api/v1/bookings", tags=["bookings"])
# app.include_router(payment.router, prefix="/api/v1/payments", tags=["payments"])
# app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
# app.include_router(review.router, prefix="/api/v1/reviews", tags=["reviews"])
# app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
# app.include_router(notification.router, prefix="/api/v1/notifications", tags=["notifications"])
# app.include_router(upload.router, prefix="/api/v1/upload", tags=["upload"])
