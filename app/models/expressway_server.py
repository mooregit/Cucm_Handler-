# app/models/expressway_server.py
from sqlalchemy import String, Integer, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .uc_base import UcServerBase


class ExpresswayServer(UcServerBase, Base):
    __tablename__ = "expressway_servers"

    # Expressway-specific fields
    cluster_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    node_role: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # "C" or "E"

    product_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    api_port: Mapped[int] = mapped_column(Integer, nullable=False, default=443)
    api_use_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    api_base_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    api_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    api_credential_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    tenant = relationship("Tenant", back_populates="expressway_servers")

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "name", name="uq_expressway_servers_tenant_name"
        ),
        UniqueConstraint(
            "tenant_id", "fqdn", name="uq_expressway_servers_tenant_fqdn"
        ),
        Index(
            "ix_expressway_servers_tenant_env",
            "tenant_id",
            "environment",
        ),
    )