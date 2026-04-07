from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header

from app.core.config import settings
from app.core.errors import ForbiddenError


async def require_admin(x_admin_token: Annotated[str | None, Header()] = None) -> None:
    """
    Placeholder admin dependency.

    - For local MVP, we protect admin endpoints with a static token header.
    - Later this becomes role-based auth (admin users, permissions, audit, etc).
    """

    if not settings.admin_token:
        raise ForbiddenError("Admin endpoints are not enabled")
    if not x_admin_token or x_admin_token != settings.admin_token:
        raise ForbiddenError("Admin token required")


Admin = Annotated[None, Depends(require_admin)]

