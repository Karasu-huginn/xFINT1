from collections.abc import Callable

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import Role
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import decode_access_token
from app.users.models import User

SESSION_COOKIE_NAME = "session"


def get_current_user(
    request: Request, session: Session = Depends(get_db)
) -> User:
    """Resolve the authenticated user from the session cookie."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is None:
        raise AuthenticationError("Authentication required")

    claims = decode_access_token(token)
    if claims is None:
        raise AuthenticationError("Authentication required")

    user = session.get(User, int(claims["sub"]))
    if user is None:
        raise AuthenticationError("Authentication required")
    return user


class RoleGuard:
    """Dependency admitting only callers holding one of the allowed roles."""

    def __init__(self, allowed_roles: tuple[Role, ...]) -> None:
        """Store the roles this guard admits."""
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """Return the caller when their role is allowed, else refuse."""
        if current_user.role not in self.allowed_roles:
            raise PermissionDeniedError("Your role cannot perform this action")
        return current_user


def require_roles(*allowed_roles: Role) -> Callable:
    """Return a dependency restricting a route to the given roles."""
    return RoleGuard(allowed_roles)
