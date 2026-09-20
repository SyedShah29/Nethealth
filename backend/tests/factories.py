from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.models.auth import Permission, Role, User
from app.models.enums import PermissionCode, RoleName


def make_role(
    name: RoleName = RoleName.ADMIN,
    permissions: tuple[PermissionCode, ...] = (
        PermissionCode.USERS_MANAGE,
        PermissionCode.ROLES_READ,
        PermissionCode.AUDIT_READ,
    ),
) -> Role:
    return Role(
        id=uuid4(),
        name=name.value,
        description=f"{name.value} role",
        permissions=[
            Permission(id=uuid4(), code=code.value, description=code.value)
            for code in permissions
        ],
    )


def make_user(
    *,
    role: Role | None = None,
    user_id: UUID | None = None,
    password_hash: str = "not-used",
    active: bool = True,
) -> User:
    selected_role = role or make_role()
    now = datetime.now(UTC)
    return User(
        id=user_id or uuid4(),
        name="Test User",
        email="user@example.test",
        password_hash=password_hash,
        role_id=selected_role.id,
        role=selected_role,
        active=active,
        failed_login_count=0,
        created_at=now,
        updated_at=now,
    )
