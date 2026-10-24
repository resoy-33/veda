"""System routes: cache rebuild."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import require_roles
from app.rebuild import rebuild_cache

router = APIRouter(prefix="/system", tags=["system"])


@router.post("/rebuild")
def rebuild(user: dict = Depends(require_roles("admin"))) -> dict:
    return rebuild_cache()
