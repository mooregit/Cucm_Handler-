# app/models/tenant.py
from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    # optional: metadata / notes about tenant
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    cucm_servers = relationship(
        "CUCMServer",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )

    unity_connection_servers = relationship(
        "UnityConnectionServer",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )

    expressway_servers = relationship(
        "ExpresswayServer",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )

    ucce_servers = relationship(
        "Ucceserver",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )

    uccx_servers: Mapped[List["UccxServer"]] = relationship(
        "UccxServer",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    imp_servers: Mapped[List["ImpServer"]] = relationship(
        "ImpServer",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    cube_gateways: Mapped[List["CubeGateway"]] = relationship(
        "CubeGateway",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    cer_servers: Mapped[List["CerServer"]] = relationship(
        "CerServer",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    cms_servers: Mapped[List["CmsServer"]] = relationship(
        "CmsServer",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )

    