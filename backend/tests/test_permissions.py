import pytest

from app.api.dependencies.auth import require_permission
from app.core.errors import AppError
from app.models.enums import PermissionCode, RoleName
from tests.factories import make_role, make_user


async def test_permission_dependency_allows_authorized_role() -> None:
    user = make_user()
    dependency = require_permission(PermissionCode.USERS_MANAGE.value)

    assert await dependency(user) is user


async def test_permission_dependency_rejects_unauthorized_role() -> None:
    viewer = make_user(role=make_role(RoleName.VIEWER, permissions=()))
    dependency = require_permission(PermissionCode.USERS_MANAGE.value)

    with pytest.raises(AppError) as error:
        await dependency(viewer)

    assert error.value.code == "PERMISSION_DENIED"
    assert error.value.status_code == 403
