# app/models/cube_gateway.py
from typing import Optional

from sqlalchemy import String, Integer, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .uc_base import UcServerBase


class CubeGateway(UcServerBase, Base):
    __tablename__ = "cube_gateways"

    # Hardware / platform
    platform_model: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # e.g. "ISR4431", "CSR1000v"
    ios_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Management & automation options
    ssh_port: Mapped[int] = mapped_column(Integer, nullable=False, default=22)

    restconf_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    restconf_port: Mapped[int | None] = mapped_column(Integer, nullable=True)

    netconf_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    netconf_port: Mapped[int | None] = mapped_column(Integer, nullable=True)

    mgmt_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mgmt_credential_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    tenant = relationship("Tenant", back_populates="cube_gateways")

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "name", name="uq_cube_gateways_tenant_name"
        ),
        UniqueConstraint(
            "tenant_id", "fqdn", name="uq_cube_gateways_tenant_fqdn"
        ),
        Index(
            "ix_cube_gateways_tenant_env",
            "tenant_id",
            "environment",
        ),
    )