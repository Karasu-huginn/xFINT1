from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.enums import Role
from app.users.models import User
from app.users.schemas import UserCreateRequest, UserInvitedResponse
from app.users.service import create_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post(
    "",
    response_model=UserInvitedResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_account(
    payload: UserCreateRequest,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.MANAGER)),
) -> UserInvitedResponse:
    """Provision an account and return its one-time activation token."""
    user, raw_token = create_user(session, payload.email, payload.role)
    session.commit()
    return UserInvitedResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        activation_token=raw_token,
    )
