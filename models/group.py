import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

GROUP_RE = re.compile(r"^[A-Za-z0-9._ -]{1,128}$")


class GroupCreate(BaseModel):
    groupname: str = Field(..., description="sAMAccountName do grupo")
    description: Optional[str] = Field(default=None, max_length=256)

    @field_validator("groupname")
    @classmethod
    def validate_groupname(cls, value: str) -> str:
        if not GROUP_RE.match(value):
            raise ValueError("groupname invalido")
        return value


class GroupUpdate(BaseModel):
    description: str = Field(..., max_length=256)


class GroupMemberChange(BaseModel):
    member: str = Field(..., min_length=1, max_length=128)


class GroupOut(BaseModel):
    groupname: str
    attributes: Dict[str, Any]


class GroupList(BaseModel):
    groups: List[str]
