import re

from pydantic import BaseModel, Field, field_validator

APP_NAME_RE = re.compile(r"^[A-Za-z0-9._-]{2,64}$")


class AppTokenRequest(BaseModel):
    app_name: str = Field(..., description="Nome da aplicacao")

    @field_validator("app_name")
    @classmethod
    def validate_app_name(cls, value: str) -> str:
        if not APP_NAME_RE.match(value):
            raise ValueError("app_name invalido")
        return value


class AppLoginRequest(BaseModel):
    app_name: str = Field(..., description="Nome da aplicacao")
    app_secret: str = Field(..., min_length=16)

    @field_validator("app_name")
    @classmethod
    def validate_app_name(cls, value: str) -> str:
        if not APP_NAME_RE.match(value):
            raise ValueError("app_name invalido")
        return value


class AppTokenResponse(BaseModel):
    app_name: str
    app_secret: str | None = None
    access_token: str
    token_type: str = "bearer"
