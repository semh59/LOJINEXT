from typing import List
from app.database.unit_of_work import UnitOfWork
from app.database.models import Kullanici
from app.infrastructure.security import jwt_handler
from fastapi import HTTPException


class UserService:
    """Service for managing administrative user operations."""

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[Kullanici]:
        """List users with pagination."""
        async with UnitOfWork() as uow:
            return await uow.kullanici_repo.get_all(
                offset=skip, limit=limit, load_relations=["rol"]
            )

    async def get_user(self, user_id: int) -> Kullanici:
        """Get user by ID."""
        async with UnitOfWork() as uow:
            user = await uow.kullanici_repo.get(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
            return user

    async def create_user(self, data: dict, created_by_id: int) -> Kullanici:
        """Create a new user with hashed password."""
        async with UnitOfWork() as uow:
            # 1. Email check
            existing = await uow.kullanici_repo.get_by_email(data["email"])
            if existing:
                raise HTTPException(
                    status_code=400, detail="Bu e-posta adresi zaten kullanımda"
                )

            # 2. Setup user
            user = Kullanici(
                email=data["email"],
                ad_soyad=data["ad_soyad"],
                rol_id=data["rol_id"],
                aktif=data.get("aktif", True),
                sofor_id=data.get("sofor_id"),
                sifre_hash=jwt_handler.get_password_hash(data["sifre"]),
                olusturan_id=created_by_id,
            )

            await uow.kullanici_repo.add(user)
            await uow.commit()
            return user

    async def update_user(self, user_id: int, data: dict) -> Kullanici:
        """Update user details and password if provided."""
        async with UnitOfWork() as uow:
            user = await uow.kullanici_repo.get(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")

            if "sifre" in data and data["sifre"]:
                data["sifre_hash"] = jwt_handler.get_password_hash(data.pop("sifre"))

            # Use repository update
            success = await uow.kullanici_repo.update(user_id, **data)
            if not success:
                raise HTTPException(status_code=500, detail="Güncelleme başarısız")

            await uow.commit()
            return await uow.kullanici_repo.get(user_id)

    async def delete_user(self, user_id: int) -> bool:
        """Soft delete or hard delete user based on implementation."""
        async with UnitOfWork() as uow:
            # For now, we'll do an actual delete, but usually soft-delete is preferred
            success = await uow.kullanici_repo.delete(user_id)
            if success:
                await uow.commit()
            return success
