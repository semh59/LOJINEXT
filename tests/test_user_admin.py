import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.services.user_service import UserService


@pytest.mark.asyncio
async def test_user_service_list_users():
    service = UserService()
    with patch("app.core.services.user_service.UnitOfWork") as mock_uow_cls:
        mock_uow = MagicMock()
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow_cls.return_value = mock_uow

        mock_uow.kullanici_repo.get_all = AsyncMock(
            return_value=[MagicMock(id=1, email="test@test.com")]
        )

        users = await service.list_users()
        assert len(users) == 1
        assert users[0].email == "test@test.com"


@pytest.mark.asyncio
async def test_user_service_create_user_email_exists():
    service = UserService()
    with patch("app.core.services.user_service.UnitOfWork") as mock_uow_cls:
        mock_uow = MagicMock()
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow_cls.return_value = mock_uow

        mock_uow.kullanici_repo.get_by_email = AsyncMock(return_value=MagicMock(id=1))

        with pytest.raises(Exception) as exc:
            await service.create_user({"email": "exists@test.com"}, created_by_id=1)
        assert "zaten kullanımda" in str(exc.value)


@pytest.mark.asyncio
async def test_user_service_delete_user():
    service = UserService()
    with patch("app.core.services.user_service.UnitOfWork") as mock_uow_cls:
        mock_uow = MagicMock()
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow_cls.return_value = mock_uow

        mock_uow.commit = AsyncMock()
        mock_uow.kullanici_repo.delete = AsyncMock(return_value=True)

        success = await service.delete_user(1)
        assert success is True
        mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_user_service_get_user():
    """Verify retrieval of a single user."""
    service = UserService()
    with patch("app.core.services.user_service.UnitOfWork") as mock_uow_cls:
        mock_uow = MagicMock()
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow_cls.return_value = mock_uow

        mock_user = MagicMock(id=1, email="get@test.com")
        mock_uow.kullanici_repo.get = AsyncMock(return_value=mock_user)

        user = await service.get_user(1)
        assert user.id == 1
        assert user.email == "get@test.com"


@pytest.mark.asyncio
async def test_user_service_update_user():
    """Verify partial updates for a user."""
    service = UserService()
    with patch("app.core.services.user_service.UnitOfWork") as mock_uow_cls:
        mock_uow = MagicMock()
        mock_uow.__aenter__.return_value = mock_uow
        mock_uow_cls.return_value = mock_uow

        mock_uow.kullanici_repo.get = AsyncMock(
            side_effect=[
                MagicMock(id=1, ad_soyad="Old Name"),
                MagicMock(id=1, ad_soyad="New Name"),
            ]
        )
        mock_uow.kullanici_repo.update = AsyncMock(return_value=True)
        mock_uow.commit = AsyncMock()

        updated_user = await service.update_user(1, {"ad_soyad": "New Name"})
        assert updated_user.ad_soyad == "New Name"
        mock_uow.kullanici_repo.update.assert_called_with(1, ad_soyad="New Name")
        mock_uow.commit.assert_called_once()
