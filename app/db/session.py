# app/db/session.py

"""
Compatibility shim so existing imports like:

    from app.db.session import get_db

still work, even though the actual objects live in app.db.__init__.
"""

from . import Base, engine, SessionLocal, get_db  # type: ignore[assignment]

__all__ = ["Base", "engine", "SessionLocal", "get_db"]
