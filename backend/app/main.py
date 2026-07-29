from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


async def read_health() -> dict[str, str]:
    """Return a static payload proving the API is reachable."""
    return {"status": "ok"}


def create_app() -> FastAPI:
    """Build the FastAPI application with CORS and routes registered."""
    application = FastAPI(title="SUP Herman Expense Reports", docs_url="/api/docs")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_api_route("/api/health", read_health, methods=["GET"])
    return application


app = create_app()
