# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from app.api.routers.axl_raw import router as axl_raw_router
from app.api.routers.devices import router as devices_router
from app.api.routers.health import router as health_router
from app.api.routers.perfmon_raw import router as perfmon_router
from app.api.routers.ris_raw import router as ris_router


def create_app() -> FastAPI:
    """
    Application factory for the CUCM Handler / UC Monitoring Tool API.
    """
    app = FastAPI(
        title="CUCM Handler API",
        description="Unified Communications Monitoring and CUCM handler service.",
        version="0.1.0",
    )

    # CORS configuration (adjust as needed for your environment)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # replace with specific origins in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router)
    app.include_router(axl_raw_router)
    app.include_router(devices_router)
    app.include_router(ris_router)
    app.include_router(perfmon_router)

    # Simple root endpoint
    @app.get("/", tags=["Meta"])
    async def root():
        return {
            "status": "ok",
            "service": "CUCM Handler API",
            "version": app.version,
        }

    return app


# FastAPI entrypoint for ASGI servers (uvicorn, gunicorn, etc.)
app = create_app()
