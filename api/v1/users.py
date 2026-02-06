from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from core.rate_limit import rate_limit_dependency
from core.security import Role, actor_from_payload, require_roles
from db.session import get_db
from models.user import UserCreate, UserGroupChange, UserPasswordReset, UserUpdate
from services import users as user_service
from services.script_runner import ScriptExecutionError

router = APIRouter()


@router.get("/users", summary="Listar usuarios", response_class=PlainTextResponse)
def list_users(db: Session = Depends(get_db), payload=Depends(require_roles(Role.admin, Role.helpdesk, Role.auditor))):
    actor = actor_from_payload(payload)
    try:
        return user_service.list_users(db, actor)
    except ScriptExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or exc.stdout or str(exc)
        ) from exc


@router.get("/users/{username}", summary="Detalhar usuario", response_class=PlainTextResponse)
def get_user(
    username: str, db: Session = Depends(get_db), payload=Depends(require_roles(Role.admin, Role.helpdesk, Role.auditor))
):
    actor = actor_from_payload(payload)
    try:
        return user_service.get_user(db, actor, username)
    except ScriptExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or exc.stdout or str(exc)
        ) from exc


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    summary="Criar usuario",
    dependencies=[Depends(rate_limit_dependency)],
    response_class=PlainTextResponse,
)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin)),
):
    actor = actor_from_payload(payload)
    try:
        return user_service.create_user(db, actor, body.model_dump())
    except ScriptExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or exc.stdout or str(exc)
        ) from exc


@router.patch(
    "/users/{username}",
    summary="Atualizar usuario",
    dependencies=[Depends(rate_limit_dependency)],
    response_class=PlainTextResponse,
)
def update_user(
    username: str,
    body: UserUpdate,
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin, Role.helpdesk)),
):
    actor = actor_from_payload(payload)
    try:
        return user_service.update_user(db, actor, username, body.model_dump(exclude_unset=True))
    except ScriptExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or exc.stdout or str(exc)
        ) from exc


@router.post(
    "/users/{username}/reset-password",
    summary="Resetar senha",
    dependencies=[Depends(rate_limit_dependency)],
    response_class=PlainTextResponse,
)
def reset_password(
    username: str,
    body: UserPasswordReset,
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin, Role.helpdesk)),
):
    actor = actor_from_payload(payload)
    try:
        return user_service.reset_password(db, actor, username, body.new_password, body.must_change_password)
    except ScriptExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or exc.stdout or str(exc)
        ) from exc


@router.post(
    "/users/{username}/enable",
    summary="Habilitar usuario",
    dependencies=[Depends(rate_limit_dependency)],
    response_class=PlainTextResponse,
)
def enable_user(
    username: str,
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin, Role.helpdesk)),
):
    actor = actor_from_payload(payload)
    try:
        return user_service.enable_user(db, actor, username)
    except ScriptExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or exc.stdout or str(exc)
        ) from exc


@router.post(
    "/users/{username}/disable",
    summary="Desabilitar usuario",
    dependencies=[Depends(rate_limit_dependency)],
    response_class=PlainTextResponse,
)
def disable_user(
    username: str,
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin, Role.helpdesk)),
):
    actor = actor_from_payload(payload)
    try:
        return user_service.disable_user(db, actor, username)
    except ScriptExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or exc.stdout or str(exc)
        ) from exc


@router.delete(
    "/users/{username}",
    summary="Remover usuario",
    dependencies=[Depends(rate_limit_dependency)],
    response_class=PlainTextResponse,
)
def delete_user(
    username: str,
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin)),
):
    actor = actor_from_payload(payload)
    try:
        return user_service.delete_user(db, actor, username)
    except ScriptExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or exc.stdout or str(exc)
        ) from exc


@router.post(
    "/users/{username}/groups",
    summary="Adicionar usuario ao grupo",
    dependencies=[Depends(rate_limit_dependency)],
    response_class=PlainTextResponse,
)
def add_user_to_group(
    username: str,
    body: UserGroupChange,
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin, Role.helpdesk)),
):
    actor = actor_from_payload(payload)
    try:
        return user_service.add_user_to_group(db, actor, username, body.group)
    except ScriptExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or exc.stdout or str(exc)
        ) from exc


@router.delete(
    "/users/{username}/groups",
    summary="Remover usuario do grupo",
    dependencies=[Depends(rate_limit_dependency)],
    response_class=PlainTextResponse,
)
def remove_user_from_group(
    username: str,
    body: UserGroupChange,
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin, Role.helpdesk)),
):
    actor = actor_from_payload(payload)
    try:
        return user_service.remove_user_from_group(db, actor, username, body.group)
    except ScriptExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or exc.stdout or str(exc)
        ) from exc


@router.post(
    "/sync/users",
    summary="Sincronizar usuarios",
    dependencies=[Depends(rate_limit_dependency)],
    response_class=PlainTextResponse,
)
def sync_users(db: Session = Depends(get_db), payload=Depends(require_roles(Role.admin, Role.auditor))):
    actor = actor_from_payload(payload)
    try:
        return user_service.sync_users(db, actor)
    except ScriptExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or exc.stdout or str(exc)
        ) from exc
