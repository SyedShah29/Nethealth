from datetime import UTC, datetime
from uuid import UUID

from pydantic import SecretStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.auth import User
from app.models.enums import AuditEventType, RoleName
from app.repositories.audit import AuditLogRepository
from app.repositories.auth import RoleRepository, UserRepository
from app.security.passwords import PasswordHasher
from app.services.audit import AuditService


class UserService:
    def __init__(self, session: AsyncSession, password_hasher: PasswordHasher) -> None:
        self.session = session
        self.password_hasher = password_hasher
        self.users = UserRepository(session)
        self.roles = RoleRepository(session)
        self.audit = AuditService(AuditLogRepository(session))

    async def list_users(self) -> list[User]:
        return await self.users.list()

    async def create_user(
        self,
        *,
        name: str,
        email: str,
        password: SecretStr,
        role_name: RoleName,
        actor: User | None,
        request_id: str | None,
    ) -> User:
        if (
            actor is None
            and role_name is RoleName.ADMIN
            and await self.users.count_active_admins() > 0
        ):
            raise AppError(
                "ADMIN_ALREADY_BOOTSTRAPPED",
                "An administrator already exists; use the authenticated user API.",
                409,
            )
        if await self.users.get_by_email(email) is not None:
            raise AppError("EMAIL_ALREADY_EXISTS", "A user with this email already exists.", 409)
        role = await self.roles.get_by_name(role_name.value)
        if role is None:
            raise AppError("ROLE_NOT_FOUND", "The requested role does not exist.", 400)
        user = User(
            name=name,
            email=email,
            password_hash=self.password_hasher.hash(password.get_secret_value()),
            role_id=role.id,
            role=role,
            active=True,
        )
        try:
            await self.users.add(user)
            await self.audit.record(
                AuditEventType.USER_CREATED,
                success=True,
                actor_user_id=actor.id if actor else None,
                target_user_id=user.id,
                request_id=request_id,
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise AppError(
                "EMAIL_ALREADY_EXISTS", "A user with this email already exists.", 409
            ) from exc
        return user

    async def update_user(
        self,
        user_id: UUID,
        *,
        name: str | None,
        role_name: RoleName | None,
        active: bool | None,
        actor: User,
        request_id: str | None,
    ) -> User:
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise AppError("USER_NOT_FOUND", "The requested user does not exist.", 404)
        if user.id == actor.id and active is False:
            raise AppError("SELF_DISABLE_FORBIDDEN", "You cannot disable your own account.", 400)

        removes_active_admin = (
            user.active
            and user.role.name == RoleName.ADMIN.value
            and (active is False or (role_name is not None and role_name != RoleName.ADMIN))
        )
        if removes_active_admin:
            await self.users.lock_active_admins()
            if await self.users.count_active_admins() <= 1:
                raise AppError(
                    "LAST_ADMIN_REQUIRED",
                    "At least one active administrator is required.",
                    409,
                )

        if name is not None:
            user.name = name
        if role_name is not None and role_name.value != user.role.name:
            role = await self.roles.get_by_name(role_name.value)
            if role is None:
                raise AppError("ROLE_NOT_FOUND", "The requested role does not exist.", 400)
            user.role = role
            user.role_id = role.id
            await self.audit.record(
                AuditEventType.USER_ROLE_CHANGED,
                success=True,
                actor_user_id=actor.id,
                target_user_id=user.id,
                request_id=request_id,
                event_metadata={"role": role.name},
            )
        if active is not None and active != user.active:
            user.active = active
            if not active:
                await self.audit.record(
                    AuditEventType.USER_DISABLED,
                    success=True,
                    actor_user_id=actor.id,
                    target_user_id=user.id,
                    request_id=request_id,
                )
        user.updated_at = datetime.now(UTC)
        await self.audit.record(
            AuditEventType.USER_UPDATED,
            success=True,
            actor_user_id=actor.id,
            target_user_id=user.id,
            request_id=request_id,
        )
        await self.session.commit()
        return user
