from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from core.security import authenticate_and_issue_token
from db.session import get_db
from models.auth import AppLoginRequest, AppTokenRequest, AppTokenResponse
from services import app_tokens

router = APIRouter()


@router.post("/auth/token", summary="Obter token JWT")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return authenticate_and_issue_token(form_data)


@router.post("/auth/app-token", response_model=AppTokenResponse, summary="Gerar token por aplicacao")
def create_app_token(body: AppTokenRequest, db=Depends(get_db)):
    app_name, app_secret = app_tokens.create_app_credentials(db, body.app_name)
    access_token = app_tokens.issue_app_token(app_name)
    return AppTokenResponse(app_name=app_name, app_secret=app_secret, access_token=access_token)


@router.post("/auth/app-login", response_model=AppTokenResponse, summary="Login por aplicacao")
def app_login(body: AppLoginRequest, db=Depends(get_db)):
    if not app_tokens.verify_app_secret(db, body.app_name, body.app_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais invalidas")
    access_token = app_tokens.issue_app_token(body.app_name)
    return AppTokenResponse(app_name=body.app_name, access_token=access_token)
