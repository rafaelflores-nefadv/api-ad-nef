from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.rate_limit import rate_limit_dependency
from core.security import Role, require_roles
from db.session import get_db
from models.user import (
    UserCreate,
    UserGroupChange,
    UserList,
    UserOut,
    UserPasswordReset,
    UserUpdate,
)
from services import users as user_service
from services.samba import SambaToolError

router = APIRouter()


@router.get("/users", response_model=UserList, summary="Listar usuarios")
def list_users(payload=Depends(require_roles(Role.admin, Role.helpdesk, Role.auditor))):
    try:
        return UserList(users=user_service.list_users())
    except SambaToolError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or str(exc)) from exc


@router.get("/users/{username}", response_model=UserOut, summary="Detalhar usuario")
def get_user(username: str, payload=Depends(require_roles(Role.admin, Role.helpdesk, Role.auditor))):
    try:
        return UserOut(username=username, attributes=user_service.get_user(username))
    except SambaToolError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or str(exc)) from exc


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    summary="Criar usuario",
    dependencies=[Depends(rate_limit_dependency)],
)
def create_user(
    body: UserCreate,
    dry_run: bool = Query(default=False, description="Executa em modo dry-run"),
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin)),
):
    try:
        user_service.create_user(db, payload["sub"], body.model_dump(), dry_run=dry_run)
    except SambaToolError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or str(exc)) from exc
    return {"status": "ok", "dry_run": dry_run}


@router.patch(
    "/users/{username}",
    summary="Atualizar usuario",
    dependencies=[Depends(rate_limit_dependency)],
)
def update_user(
    username: str,
    body: UserUpdate,
    dry_run: bool = Query(default=False, description="Executa em modo dry-run"),
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin, Role.helpdesk)),
):
    try:
        user_service.update_user(db, payload["sub"], username, body.model_dump(exclude_unset=True), dry_run=dry_run)
    except SambaToolError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or str(exc)) from exc
    return {"status": "ok", "dry_run": dry_run}


@router.post(
    "/users/{username}/reset-password",
    summary="Resetar senha",
    dependencies=[Depends(rate_limit_dependency)],
)
def reset_password(
    username: str,
    body: UserPasswordReset,
    dry_run: bool = Query(default=False, description="Executa em modo dry-run"),
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin, Role.helpdesk)),
):
    try:
        user_service.reset_password(
            db, payload["sub"], username, body.new_password, body.must_change_password, dry_run=dry_run
        )
    except SambaToolError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or str(exc)) from exc
    return {"status": "ok", "dry_run": dry_run}


@router.post(
    "/users/{username}/enable",
    summary="Habilitar usuario",
    dependencies=[Depends(rate_limit_dependency)],
)
def enable_user(
    username: str,
    dry_run: bool = Query(default=False, description="Executa em modo dry-run"),
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin, Role.helpdesk)),
):
    try:
        user_service.enable_user(db, payload["sub"], username, dry_run=dry_run)
    except SambaToolError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or str(exc)) from exc
    return {"status": "ok", "dry_run": dry_run}


@router.post(
    "/users/{username}/disable",
    summary="Desabilitar usuario",
    dependencies=[Depends(rate_limit_dependency)],
)
def disable_user(
    username: str,
    dry_run: bool = Query(default=False, description="Executa em modo dry-run"),
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin, Role.helpdesk)),
):
    try:
        user_service.disable_user(db, payload["sub"], username, dry_run=dry_run)
    except SambaToolError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or str(exc)) from exc
    return {"status": "ok", "dry_run": dry_run}


@router.post(
    "/users/{username}/groups",
    summary="Adicionar usuario ao grupo",
    dependencies=[Depends(rate_limit_dependency)],
)
def add_user_to_group(
    username: str,
    body: UserGroupChange,
    dry_run: bool = Query(default=False, description="Executa em modo dry-run"),
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin, Role.helpdesk)),
):
    try:
        user_service.add_user_to_group(db, payload["sub"], username, body.group, dry_run=dry_run)
    except SambaToolError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or str(exc)) from exc
    return {"status": "ok", "dry_run": dry_run}


@router.delete(
    "/users/{username}/groups",
    summary="Remover usuario do grupo",
    dependencies=[Depends(rate_limit_dependency)],
)
def remove_user_from_group(
    username: str,
    body: UserGroupChange,
    dry_run: bool = Query(default=False, description="Executa em modo dry-run"),
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin, Role.helpdesk)),
):
    try:
        user_service.remove_user_from_group(db, payload["sub"], username, body.group, dry_run=dry_run)
    except SambaToolError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or str(exc)) from exc
    return {"status": "ok", "dry_run": dry_run}


@router.post(
    "/sync/users",
    summary="Sincronizar usuarios",
    dependencies=[Depends(rate_limit_dependency)],
)
def sync_users(
    background_tasks: BackgroundTasks,
    payload=Depends(require_roles(Role.admin, Role.auditor)),
):
    actor = payload["sub"]
    background_tasks.add_task(user_service.sync_users_job, actor)
    return {"status": "accepted"}
