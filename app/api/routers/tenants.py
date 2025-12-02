# app/api/routers/tenants.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.cucm_server import CUCMServer

router = APIRouter(prefix="/tenants", tags=["tenants"])

@router.get("/")
def list_tenants(db: Session = Depends(get_db)):
    tenants = (
        db.query(Tenant)
        .filter(Tenant.deleted_at.is_(None))   # if SoftDeleteMixin uses deleted_at
        .all()
    )
    return [
        {
            "id": str(t.id),       # UUID -> string
            "name": t.name,
            "slug": t.slug,
        }
        for t in tenants
    ]

@router.get("/{tenant_id}/cucm-servers")
def list_cucm_servers(tenant_id: str, db: Session = Depends(get_db)):
    servers = (
        db.query(CUCMServer)
        .filter(
            CUCMServer.tenant_id == tenant_id,
            CUCMServer.deleted_at.is_(None),
        )
        .all()
    )
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "hostname": s.hostname,
            "version": s.version,
        }
        for s in servers
    ]
