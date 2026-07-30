from pydantic import BaseModel, ConfigDict, EmailStr

from app.core.enums import Role


class UserCreateRequest(BaseModel):
    """Payload a manager submits to provision a new account."""

    email: EmailStr
    role: Role


class UserResponse(BaseModel):
    """Public representation of a user account."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: Role


class UserInvitedResponse(UserResponse):
    """Creation response carrying the one-time activation token."""

    activation_token: str
