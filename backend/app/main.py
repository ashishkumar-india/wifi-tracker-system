"""
WiFi Tracker System - FastAPI Main Application
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import init_db, check_db_connection
from app.utils.logger import setup_logging, get_logger
from app.services.notification import notification_service

from app.routers import (
    auth_router,
    devices_router,
    scans_router,
    alerts_router,
    dashboard_router
)

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting WiFi Tracker System...")
    
    if check_db_connection():
        logger.info("Database connection successful")
        init_db()
    else:
        logger.error("Database connection failed!")
    
    yield
    
    logger.info("Shutting down WiFi Tracker System...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-based WiFi device tracking and monitoring system",
    lifespan=lifespan
)

# CORS configuration - allow all origins for development (file:// has null origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins including file:// (null origin)
    allow_credentials=False,  # Must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


app.include_router(auth_router, prefix="/api")
app.include_router(devices_router, prefix="/api")
app.include_router(scans_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_status = check_db_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected"
    }


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    
    notification_service.register_websocket(websocket)
    logger.info("WebSocket client connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        notification_service.unregister_websocket(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        notification_service.unregister_websocket(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
