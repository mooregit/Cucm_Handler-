# app/models/cucm_server.py
from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, SoftDeleteMixin


class CUCMServer(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "cucm_servers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Multi-tenant FK
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    fqdn: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)

    # CUCM details / role
    cluster_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    server_role: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # e.g. "publisher", "subscriber", "imp", "unity"

    # Versioning
    cucm_version: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # e.g. "12.5(1)SU8"
    axl_api_version: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # e.g. "12.5", "14.0"

    # Connectivity config
    axl_port: Mapped[int] = mapped_column(Integer, nullable=False, default=8443)
    use_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    verify_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Credentials:
    # Store references to an external secrets system rather than raw passwords.
    axl_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    axl_credential_ref: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # e.g. key/id in Vault/KMS/SecretsManager

    # Environment info
    environment: Mapped[str] = mapped_column(
        String(50), nullable=False, default="production"
    )  # "production", "staging", etc.
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)  # DC/name

    # Health / status snapshot fields (updated by health check jobs)
    last_health_check_at: Mapped[datetime | None] = mapped_column(
        nullable=True
    )
    last_health_status: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # "up", "down", "degraded"
    last_health_message: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="cucm_servers")

    __table_args__ = (
        # Names and FQDNs must be unique per tenant
        UniqueConstraint(
            "tenant_id",
            "name",
            name="uq_cucm_servers_tenant_name",
        ),
        UniqueConstraint(
            "tenant_id",
            "fqdn",
            name="uq_cucm_servers_tenant_fqdn",
        ),
        # Helpful indexes for lookups
        Index("ix_cucm_servers_tenant_cluster", "tenant_id", "cluster_name"),
        Index("ix_cucm_servers_tenant_env", "tenant_id", "environment"),
    )