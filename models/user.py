import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


class UserCreate(BaseModel):
    username: str = Field(..., description="sAMAccountName")
    password: str = Field(..., min_length=8, max_length=128)
    given_name: Optional[str] = Field(default=None, max_length=64)
    surname: Optional[str] = Field(default=None, max_length=64)
    display_name: Optional[str] = Field(default=None, max_length=128)
    mail: Optional[str] = Field(default=None, max_length=128)
    must_change_password: bool = Field(default=True)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if not USERNAME_RE.match(value):
            raise ValueError("username invalido")
        return value


class UserUpdate(BaseModel):
    given_name: Optional[str] = Field(default=None, max_length=64)
    surname: Optional[str] = Field(default=None, max_length=64)
    display_name: Optional[str] = Field(default=None, max_length=128)
    mail: Optional[str] = Field(default=None, max_length=128)
    upn: Optional[str] = Field(default=None, max_length=128)


class UserPasswordReset(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=128)
    must_change_password: bool = Field(default=False)


class UserGroupChange(BaseModel):
    group: str = Field(..., min_length=1, max_length=128)


class UserOut(BaseModel):
    username: str
    attributes: Dict[str, Any]


class UserList(BaseModel):
    users: List[str]
