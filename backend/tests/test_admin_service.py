from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.auth import Permission
from app.models.enums import PermissionCode, RoleName
from app.repositories.audit import AuditLogRepository
from app.repositories.auth import PermissionRepository, RoleRepository
from app.services.admin import AdminService
from app.services.audit import AuditService
from tests.factories import make_role, make_user


def _service() -> tuple[AdminService, AsyncMock]:
    session = AsyncMock(spec=AsyncSession)
    service = AdminService(
        session,
        AsyncMock(spec=RoleRepository),
        AsyncMock(spec=PermissionRepository),
        AsyncMock(spec=AuditLogRepository),
    )
    service.audit = AsyncMock(spec=AuditService)
    return service, session


@pytest.mark.asyncio
async def test_role_management_updates_permissions_and_audits() -> None:
    service, session = _service()
    role = make_role(RoleName.SUPPORT, permissions=())
    permission = Permission(
        code=PermissionCode.SUBSCRIBERS_READ.value,
        description="subscriber read",
    )
    service.roles.get_by_id.return_value = role
    service.permissions.get_by_codes.return_value = [permission]

    updated = await service.update_role(
        role.id,
        description="Support staff",
        permission_codes=[PermissionCode.SUBSCRIBERS_READ.value],
        actor=make_user(),
    )

    assert updated.permissions == [permission]
    service.audit.record.assert_awaited_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_admin_role_must_retain_core_permissions() -> None:
    service, session = _service()
    role = make_role(RoleName.ADMIN, permissions=())
    service.roles.get_by_id.return_value = role
    service.permissions.get_by_codes.return_value = []

    with pytest.raises(AppError) as error:
        await service.update_role(
            role.id,
            description=None,
            permission_codes=[],
            actor=make_user(),
        )

    assert error.value.code == "ADMIN_PERMISSIONS_REQUIRED"
    session.commit.assert_not_awaited()
