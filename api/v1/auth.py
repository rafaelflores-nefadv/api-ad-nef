from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from core.security import authenticate_and_issue_token

router = APIRouter()


@router.post("/auth/token", summary="Obter token JWT")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return authenticate_and_issue_token(form_data)
