# app/models/unity_connection_server.py
from sqlalchemy import String, Integer, Boolean, UniqueConstraint, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .uc_base import UcServerBase


class UnityConnectionServer(UcServerBase, Base):
    __tablename__ = "unity_connection_servers"

    # Unity-specific fields
    cluster_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Admin/REST API
    rest_port: Mapped[int] = mapped_column(Integer, nullable=False, default=443)
    rest_use_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rest_base_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    admin_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    admin_credential_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    tenant = relationship("Tenant", back_populates="unity_connection_servers")

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "name", name="uq_unity_servers_tenant_name"
        ),
        UniqueConstraint(
            "tenant_id", "fqdn", name="uq_unity_servers_tenant_fqdn"
        ),
        Index(
            "ix_unity_servers_tenant_env",
            "tenant_id",
            "environment",
        ),
    )