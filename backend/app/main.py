from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers


async def read_health() -> dict[str, str]:
    """Return a static payload proving the API is reachable."""
    return {"status": "ok"}


def create_app() -> FastAPI:
    """Build the FastAPI application with CORS, handlers and routes registered."""
    application = FastAPI(title="SUP Herman Expense Reports", docs_url="/api/docs")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(application)
    application.add_api_route("/api/health", read_health, methods=["GET"])
    application.include_router(auth_router)
    return application


app = create_app()
