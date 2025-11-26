# app/models/imp_server.py
from typing import Optional

from sqlalchemy import String, Integer, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .uc_base import UcServerBase


class ImpServer(UcServerBase, Base):
    __tablename__ = "imp_servers"

    # IMP-specific
    cluster_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    node_role: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # e.g. "presence", "xmpp"

    product_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Admin / XCP REST APIs
    api_port: Mapped[int] = mapped_column(Integer, nullable=False, default=443)
    api_use_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    api_base_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    api_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    api_credential_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    tenant = relationship("Tenant", back_populates="imp_servers")

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "name", name="uq_imp_servers_tenant_name"
        ),
        UniqueConstraint(
            "tenant_id", "fqdn", name="uq_imp_servers_tenant_fqdn"
        ),
        Index(
            "ix_imp_servers_tenant_env",
            "tenant_id",
            "environment",
        ),
    )