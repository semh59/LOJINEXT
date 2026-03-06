from enum import IntFlag, auto
from typing import Any, Dict, Union

from fastapi import HTTPException, status

from app.database.models import Kullanici


class Permission(IntFlag):
    NONE = 0
    READ = auto()
    WRITE = auto()
    DELETE = auto()
    ADMIN = auto()
    SUPERADMIN = auto()


class SecurityService:
    """
    Sovereign Security Service for Zero-Defect RBAC and Isolation.
    """

    ROLE_PERMISSIONS: Dict[str, Permission] = {
        "user": Permission.READ,
        "driver": Permission.READ,
        "admin": Permission.READ
        | Permission.WRITE
        | Permission.DELETE
        | Permission.ADMIN,
        "super_admin": Permission.READ
        | Permission.WRITE
        | Permission.DELETE
        | Permission.ADMIN
        | Permission.SUPERADMIN,
    }

    @classmethod
    def has_permission(
        cls, user: Kullanici, required_permission: Union[Permission, str]
    ) -> bool:
        """
        Check if user has required permission.
        Supports both legacy bitwise flags and new granular string keys.
        """
        if not user or not user.aktif:
            return False

        # Super Admin bypass
        user_role_name = getattr(user.rol, "ad", None) if user.rol else None
        if user_role_name == "super_admin":
            return True

        # New Granular Permission Check (String or List[String])
        if isinstance(required_permission, (str, list)):
            if not user.rol or not user.rol.yetkiler:
                return False

            # Admin/SuperAdmin bypass for granular checks is already handled above
            # specifically for role names, but here we check permissions.
            perms_to_check = (
                [required_permission]
                if isinstance(required_permission, str)
                else required_permission
            )

            # Wildcard match
            if user.rol.yetkiler.get("*"):
                return True

            # Match at least one
            for perm in perms_to_check:
                if user.rol.yetkiler.get(perm):
                    return True
            return False

        # Legacy Bitwise Check (Permission enum)
        role_name = user.rol.ad if user.rol else "user"
        user_permission = cls.ROLE_PERMISSIONS.get(role_name, Permission.NONE)
        return bool(user_permission & required_permission)

    @classmethod
    def verify_permission(
        cls, user: Kullanici, required_permission: Union[Permission, str]
    ):
        """Raise HTTPException if permission is missing."""
        if not cls.has_permission(user, required_permission):
            perm_name = (
                required_permission.name
                if isinstance(required_permission, Permission)
                else required_permission
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Erişim Reddedildi: {perm_name} yetkisi gerekli.",
            )

    @classmethod
    def verify_ownership(
        cls, user: Kullanici, owner_id: int, field_name: str = "sofor_id"
    ):
        """Verify data ownership for isolation."""
        if cls.has_permission(user, Permission.ADMIN):
            return  # Admin can access everything

        user_owner_id = getattr(user, field_name, None)
        if user_owner_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Erişim Reddedildi: Bu veri size ait değil.",
            )

    @classmethod
    def apply_isolation(
        cls, user: Kullanici, filters: Dict[str, Any], field_name: str = "sofor_id"
    ) -> Dict[str, Any]:
        """Apply isolation filters based on user role."""
        if cls.has_permission(user, Permission.ADMIN):
            return filters  # No isolation for admins

        user_owner_id = getattr(user, field_name, None)
        if user_owner_id:
            filters[field_name] = user_owner_id
        else:
            # If no ownership ID and not admin, restrict all data (Secure Default)
            filters[field_name] = -1  # Invalid ID to ensure empty result

        return filters
