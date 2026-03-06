from typing import Union

from fastapi import Depends

from app.api.deps import get_current_user
from app.core.services.security_service import Permission, SecurityService
from app.database.models import Kullanici


class PermissionChecker:
    """
    Dependency factory for granular RBAC.
    """

    def __init__(self, required_permission: Union[Permission, str]):
        self.required_permission = required_permission

    def __call__(
        self, current_user: Kullanici = Depends(get_current_user)
    ) -> Kullanici:
        SecurityService.verify_permission(current_user, self.required_permission)
        return current_user


def require_yetki(permission: Union[Permission, str]):
    """
    Shortcut for PermissionChecker.
    Usage: Depends(require_yetki("kullanici_ekle"))
    """
    return PermissionChecker(permission)
