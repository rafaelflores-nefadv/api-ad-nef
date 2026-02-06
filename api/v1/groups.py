from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.rate_limit import rate_limit_dependency
from core.security import Role, require_roles
from db.session import get_db
from models.group import GroupCreate, GroupList, GroupMemberChange, GroupOut, GroupUpdate
from services import groups as group_service
from services.samba import SambaToolError

router = APIRouter()


@router.get("/groups", response_model=GroupList, summary="Listar grupos")
def list_groups(payload=Depends(require_roles(Role.admin, Role.helpdesk, Role.auditor))):
    return GroupList(groups=group_service.list_groups())


@router.get("/groups/{groupname}", response_model=GroupOut, summary="Detalhar grupo")
def get_group(groupname: str, payload=Depends(require_roles(Role.admin, Role.helpdesk, Role.auditor))):
    return GroupOut(groupname=groupname, attributes=group_service.get_group(groupname))


@router.post(
    "/groups",
    status_code=status.HTTP_201_CREATED,
    summary="Criar grupo",
    dependencies=[Depends(rate_limit_dependency)],
)
def create_group(
    body: GroupCreate,
    dry_run: bool = Query(default=False, description="Executa em modo dry-run"),
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin)),
):
    try:
        group_service.create_group(db, payload["sub"], body.groupname, body.description, dry_run=dry_run)
    except SambaToolError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or str(exc)) from exc
    return {"status": "ok", "dry_run": dry_run}


@router.patch(
    "/groups/{groupname}",
    summary="Editar descricao do grupo",
    dependencies=[Depends(rate_limit_dependency)],
)
def update_group(
    groupname: str,
    body: GroupUpdate,
    dry_run: bool = Query(default=False, description="Executa em modo dry-run"),
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin, Role.helpdesk)),
):
    try:
        group_service.update_group_description(db, payload["sub"], groupname, body.description, dry_run=dry_run)
    except SambaToolError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or str(exc)) from exc
    return {"status": "ok", "dry_run": dry_run}


@router.post(
    "/groups/{groupname}/members",
    summary="Adicionar membro ao grupo",
    dependencies=[Depends(rate_limit_dependency)],
)
def add_member(
    groupname: str,
    body: GroupMemberChange,
    dry_run: bool = Query(default=False, description="Executa em modo dry-run"),
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin, Role.helpdesk)),
):
    try:
        group_service.add_member(db, payload["sub"], groupname, body.member, dry_run=dry_run)
    except SambaToolError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or str(exc)) from exc
    return {"status": "ok", "dry_run": dry_run}


@router.delete(
    "/groups/{groupname}/members",
    summary="Remover membro do grupo",
    dependencies=[Depends(rate_limit_dependency)],
)
def remove_member(
    groupname: str,
    body: GroupMemberChange,
    dry_run: bool = Query(default=False, description="Executa em modo dry-run"),
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin, Role.helpdesk)),
):
    try:
        group_service.remove_member(db, payload["sub"], groupname, body.member, dry_run=dry_run)
    except SambaToolError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or str(exc)) from exc
    return {"status": "ok", "dry_run": dry_run}


@router.post(
    "/groups/{groupname}/disable",
    summary="Desativar grupo",
    dependencies=[Depends(rate_limit_dependency)],
)
def disable_group(
    groupname: str,
    target_ou_dn: str = Query(..., description="DN da OU de destino"),
    dry_run: bool = Query(default=False, description="Executa em modo dry-run"),
    db: Session = Depends(get_db),
    payload=Depends(require_roles(Role.admin)),
):
    try:
        group_service.disable_group(db, payload["sub"], groupname, target_ou_dn, dry_run=dry_run)
    except SambaToolError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.stderr or str(exc)) from exc
    return {"status": "ok", "dry_run": dry_run}


@router.post(
    "/sync/groups",
    summary="Sincronizar grupos",
    dependencies=[Depends(rate_limit_dependency)],
)
def sync_groups(
    background_tasks: BackgroundTasks,
    payload=Depends(require_roles(Role.admin, Role.auditor)),
):
    actor = payload["sub"]
    background_tasks.add_task(group_service.sync_groups_job, actor)
    return {"status": "accepted"}
