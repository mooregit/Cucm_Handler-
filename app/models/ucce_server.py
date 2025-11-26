# app/models/ucce_server.py
from sqlalchemy import String, Integer, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .uc_base import UcServerBase


class Ucceserver(UcServerBase, Base):
    __tablename__ = "ucce_servers"

    # UCCE-specific fields
    instance_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    component_role: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # e.g. "ROGGER", "PG", "AW", "HDS"

    product_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    api_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    api_use_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    api_base_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    api_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    api_credential_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    tenant = relationship("Tenant", back_populates="ucce_servers")

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "name", name="uq_ucce_servers_tenant_name"
        ),
        UniqueConstraint(
            "tenant_id", "fqdn", name="uq_ucce_servers_tenant_fqdn"
        ),
        Index(
            "ix_ucce_servers_tenant_env",
            "tenant_id",
            "environment",
        ),
    )