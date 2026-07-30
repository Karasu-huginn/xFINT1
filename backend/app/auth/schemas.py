from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Credentials submitted to the login endpoint."""

    email: EmailStr
    password: str
