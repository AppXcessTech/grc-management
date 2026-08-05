from pydantic import BaseModel, EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    token: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str
    password: str
