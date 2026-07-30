from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.auth.schemas import LoginRequest
from app.auth.service import authenticate_user
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import SESSION_COOKIE_NAME, get_current_user
from app.core.security import create_access_token
from app.users.models import User
from app.users.schemas import UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


def set_session_cookie(response: Response, user: User) -> None:
    """Attach a signed session cookie identifying the given user."""
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_access_token(user.id, user.role),
        httponly=True,
        samesite="lax",
        secure=settings.is_cookie_secure,
        max_age=settings.access_token_expire_hours * 3600,
        path="/",
    )


@router.post("/login", status_code=status.HTTP_204_NO_CONTENT)
def log_in(
    payload: LoginRequest,
    response: Response,
    session: Session = Depends(get_db),
) -> None:
    """Authenticate the caller and issue a session cookie."""
    user = authenticate_user(session, payload.email, payload.password)
    set_session_cookie(response, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def log_out(response: Response) -> None:
    """Clear the session cookie."""
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    """Return the authenticated caller's account."""
    return current_user
