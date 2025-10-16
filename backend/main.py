"""
Telemetra FastAPI Backend Application.

Main entry point for the Telemetra real-time streaming analytics API.
"""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.db.database import init_db_pool, close_db_pool
from backend.db.redis_client import init_redis_client, close_redis_client
from backend.api.routes import router as api_router
from backend.api.websocket import ws_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Telemetra API", version=settings.app_version)

    try:
        # Initialize database pool
        logger.info("Initializing database connection pool")
        await init_db_pool()

        # Initialize Redis client
        logger.info("Initializing Redis client")
        await init_redis_client()

        logger.info("Telemetra API started successfully")

    except Exception as e:
        logger.error("Failed to start application", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down Telemetra API")

    try:
        # Close database pool
        logger.info("Closing database connection pool")
        await close_db_pool()

        # Close Redis client
        logger.info("Closing Redis client")
        await close_redis_client()

        logger.info("Telemetra API shut down successfully")

    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Real-time streaming analytics API for Telemetra",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
        },
    )


# Include routers
app.include_router(api_router, prefix="/api/v1", tags=["API"])
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


# Direct health endpoint (not versioned)
@app.get("/health", tags=["Health"])
async def health():
    """Simple health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
