from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from core.rate_limit import rate_limit_dependency
from core.security import Role, actor_from_payload, require_roles
from db.session import get_db
from models.group import GroupCreate, GroupMemberChange, GroupUpdate
from services import groups as group_service
from services.script_runner import ScriptExecutionError

router = APIRouter()


@router.get("/groups", summary="Listar grupos", response_class=PlainTextResponse)
def list_groups(db: Session = Depends(get_db), payload=Depends(require_roles(Role.admin, Role.helpdesk, Role.auditor))):
    actor = actor_from_payload(payload)
    try:
        return group_service.list_groups(db, actor)
    except ScriptExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or exc.stdout or str(exc)
        ) from exc


@router.get("/groups/{groupname}", summary="Detalhar grupo", response_class=PlainTextResponse)
def get_group(
    groupname: str, db: Session = Depends(get_db), payload=Depends(require_roles(Role.admin, Role.helpdesk, Role.auditor))
):
    actor = actor_from_payload(payload)
    try:
        return group_service.get_group(db, actor, groupname)
    except ScriptExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or exc.stdout or str(exc)
        ) from exc


@router.post(
    "/groups",
    status_code=status.HTTP_201_CREATED,
    summary="Criar grupo",
    dependencies=[Depends(rate_limit_dependency)],
    response_class=PlainTextResponse,
)
def create_group(
    body: GroupCreate,
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin)),
):
    actor = actor_from_payload(payload)
    try:
        return group_service.create_group(db, actor, body.groupname, body.description)
    except ScriptExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or exc.stdout or str(exc)
        ) from exc


@router.patch(
    "/groups/{groupname}",
    summary="Editar descricao do grupo",
    dependencies=[Depends(rate_limit_dependency)],
    response_class=PlainTextResponse,
)
def update_group(
    groupname: str,
    body: GroupUpdate,
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin, Role.helpdesk)),
):
    actor = actor_from_payload(payload)
    try:
        return group_service.update_group_description(db, actor, groupname, body.description)
    except ScriptExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or exc.stdout or str(exc)
        ) from exc


@router.post(
    "/groups/{groupname}/members",
    summary="Adicionar membro ao grupo",
    dependencies=[Depends(rate_limit_dependency)],
    response_class=PlainTextResponse,
)
def add_member(
    groupname: str,
    body: GroupMemberChange,
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin, Role.helpdesk)),
):
    actor = actor_from_payload(payload)
    try:
        return group_service.add_member(db, actor, groupname, body.member)
    except ScriptExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or exc.stdout or str(exc)
        ) from exc


@router.delete(
    "/groups/{groupname}/members",
    summary="Remover membro do grupo",
    dependencies=[Depends(rate_limit_dependency)],
    response_class=PlainTextResponse,
)
def remove_member(
    groupname: str,
    body: GroupMemberChange,
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin, Role.helpdesk)),
):
    actor = actor_from_payload(payload)
    try:
        return group_service.remove_member(db, actor, groupname, body.member)
    except ScriptExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or exc.stdout or str(exc)
        ) from exc


@router.post(
    "/groups/{groupname}/disable",
    summary="Desativar grupo",
    dependencies=[Depends(rate_limit_dependency)],
    response_class=PlainTextResponse,
)
def disable_group(
    groupname: str,
    target_ou_dn: str = Query(..., description="DN da OU de destino"),
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin)),
):
    actor = actor_from_payload(payload)
    try:
        return group_service.disable_group(db, actor, groupname, target_ou_dn)
    except ScriptExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or exc.stdout or str(exc)
        ) from exc


@router.post(
    "/sync/groups",
    summary="Sincronizar grupos",
    dependencies=[Depends(rate_limit_dependency)],
    response_class=PlainTextResponse,
)
def sync_groups(db: Session = Depends(get_db), payload=Depends(require_roles(Role.admin, Role.auditor))):
    actor = actor_from_payload(payload)
    try:
        return group_service.sync_groups(db, actor)
    except ScriptExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or exc.stdout or str(exc)
        ) from exc
