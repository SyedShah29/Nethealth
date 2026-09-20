from unittest.mock import AsyncMock

import pytest
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.enums import RoleName
from app.repositories.auth import RoleRepository, UserRepository
from app.security.passwords import PasswordHasher
from app.services.audit import AuditService
from app.services.users import UserService
from tests.factories import make_role, make_user


def make_service(password_hasher: PasswordHasher) -> tuple[UserService, AsyncMock]:
    session = AsyncMock(spec=AsyncSession)
    service = UserService(session, password_hasher)
    service.users = AsyncMock(spec=UserRepository)
    service.roles = AsyncMock(spec=RoleRepository)
    service.audit = AsyncMock(spec=AuditService)
    return service, session


async def test_create_user_hashes_password_and_records_audit(
    password_hasher: PasswordHasher,
) -> None:
    service, session = make_service(password_hasher)
    role = make_role(RoleName.SUPPORT, permissions=())
    service.users.get_by_email.return_value = None
    service.roles.get_by_name.return_value = role
    service.users.add.side_effect = lambda user: user
    actor = make_user()
    password = "a new secure password"

    user = await service.create_user(
        name="Support User",
        email="support@example.test",
        password=SecretStr(password),
        role_name=RoleName.SUPPORT,
        actor=actor,
        request_id="request-5",
    )

    assert user.password_hash != password
    assert password_hasher.verify(password, user.password_hash)
    service.audit.record.assert_awaited_once()
    session.commit.assert_awaited_once()


async def test_final_active_administrator_cannot_be_disabled(
    password_hasher: PasswordHasher,
) -> None:
    service, session = make_service(password_hasher)
    target = make_user()
    actor = make_user()
    service.users.get_by_id.return_value = target
    service.users.count_active_admins.return_value = 1

    with pytest.raises(AppError) as error:
        await service.update_user(
            target.id,
            name=None,
            role_name=None,
            active=False,
            actor=actor,
            request_id="request-6",
        )

    assert error.value.code == "LAST_ADMIN_REQUIRED"
    service.users.lock_active_admins.assert_awaited_once()
    session.commit.assert_not_awaited()
