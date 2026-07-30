from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Credentials submitted to the login endpoint."""

    email: EmailStr
    password: str


class ActivationRequest(BaseModel):
    """Payload submitted to set a password from an invitation."""

    token: str
    password: str


class ActivationProbeResponse(BaseModel):
    """Reveals which address an activation token belongs to."""

    email: str
