# app/models/uc_base.py
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, SoftDeleteMixin


class UcServerBase(TimestampMixin, SoftDeleteMixin):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Generic identity
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    fqdn: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)

    environment: Mapped[str] = mapped_column(
        String(50), nullable=False, default="production"
    )
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Health snapshot
    last_health_check_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_health_status: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # "up", "down", "degraded"
    last_health_message: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)