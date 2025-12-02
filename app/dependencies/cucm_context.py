# app/dependencies/cucm_context.py
from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.cucm_server import CUCMServer
from app.services.axl_service import AxlService  # your existing wrapper

class CucmContext:
    def __init__(self, server: CUCMServer, axl: AxlService):
        self.server = server
        self.axl = axl

def get_cucm_context(
    tenant_id: str = Query(..., description="Tenant UUID"),
    server_id: str = Query(..., description="CUCM server UUID"),
    db: Session = Depends(get_db),
) -> CucmContext:
    server = (
        db.query(CUCMServer)
        .filter(
            CUCMServer.id == server_id,
            CUCMServer.tenant_id == tenant_id,
            CUCMServer.deleted_at.is_(None),
        )
        .first()
    )
    if not server:
        raise HTTPException(status_code=404, detail="CUCM server not found")

    # Build AXL client from DB row (pseudo-code)
    # password = decrypt(server.password_encrypted)
    # axl_client = AxlClient(
    #     hostname=server.hostname,
    #     username=server.username,
    #     password=password,
    #     port=server.port,
    #     use_tls=server.use_tls,
    #     wsdl_path=server.wsdl_path,
    # )
    axl_service = AxlService.from_server(server)  # convenient factory

    return CucmContext(server=server, axl=axl_service)
