from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.expenses.router import attachments_router, reports_router
from app.users.router import router as users_router


async def read_health() -> dict[str, str]:
    """Return a static payload proving the API is reachable."""
    return {"status": "ok"}


def create_app() -> FastAPI:
    """Build the FastAPI application with CORS, handlers and routes registered."""
    # Every documentation URL lives under /api because the dev server proxies that
    # prefix and nothing else; a schema served from the root would 404 through it.
    application = FastAPI(
        title="SUP Herman Expense Reports",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
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
    application.include_router(users_router)
    application.include_router(reports_router)
    application.include_router(attachments_router)
    return application


app = create_app()
