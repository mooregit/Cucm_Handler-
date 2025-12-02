# app/models/uc_server.py

"""
Compatibility shim.

Older/other parts of the code expect a generic `UcServer` model in
`app.models.uc_server`. In your current project you only have a
CUCM-specific `CucmServer` model in `app.models.cucm_server`.

This module simply aliases `CucmServer` -> `UcServer` so imports like:

    from app.models.uc_server import UcServer

continue to work.
"""

from __future__ import annotations

from app.models.cucm_server import CUCMServer

# Simple alias
UcServer = CUCMServer

__all__ = ["UcServer"]
