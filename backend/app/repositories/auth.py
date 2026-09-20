from __future__ import annotations

import builtins
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.auth import AuthSession, Permission, Role, User
from app.models.enums import RoleName


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User)
            .where(User.email == email)
            .options(selectinload(User.role).selectinload(Role.permissions))
        )
        return result.scalar_one_or_none()

    async def get_by_email_for_update(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User)
            .where(User.email == email)
            .with_for_update()
            .options(selectinload(User.role).selectinload(Role.permissions))
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.role).selectinload(Role.permissions))
        )
        return result.scalar_one_or_none()

    async def list(self) -> list[User]:
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.role).selectinload(Role.permissions))
            .order_by(User.name, User.email)
        )
        return list(result.scalars().unique())

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user

    async def count_active_admins(self) -> int:
        result = await self.session.execute(
            select(func.count(User.id))
            .join(Role, User.role_id == Role.id)
            .where(User.active.is_(True), Role.name == RoleName.ADMIN.value)
        )
        return int(result.scalar_one())

    async def lock_active_admins(self) -> None:
        await self.session.execute(
            select(User.id)
            .join(Role, User.role_id == Role.id)
            .where(User.active.is_(True), Role.name == RoleName.ADMIN.value)
            .with_for_update()
        )


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, role_id: UUID) -> Role | None:
        result = await self.session.execute(
            select(Role)
            .where(Role.id == role_id)
            .options(selectinload(Role.permissions))
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Role | None:
        result = await self.session.execute(
            select(Role)
            .where(Role.name == name)
            .options(selectinload(Role.permissions))
        )
        return result.scalar_one_or_none()

    async def list(self) -> list[Role]:
        result = await self.session.execute(
            select(Role).options(selectinload(Role.permissions)).order_by(Role.name)
        )
        return list(result.scalars().unique())


class PermissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self) -> list[Permission]:
        result = await self.session.execute(select(Permission).order_by(Permission.code))
        return list(result.scalars())

    async def get_by_codes(self, codes: set[str]) -> builtins.list[Permission]:
        result = await self.session.execute(select(Permission).where(Permission.code.in_(codes)))
        return list(result.scalars())


class AuthSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, auth_session: AuthSession) -> AuthSession:
        self.session.add(auth_session)
        await self.session.flush()
        return auth_session

    async def get_by_token_hash(self, token_hash: str) -> AuthSession | None:
        result = await self.session.execute(
            select(AuthSession)
            .where(AuthSession.token_hash == token_hash)
            .options(
                selectinload(AuthSession.user)
                .selectinload(User.role)
                .selectinload(Role.permissions)
            )
        )
        return result.scalar_one_or_none()

    async def revoke(self, auth_session: AuthSession, revoked_at: datetime) -> None:
        auth_session.revoked_at = revoked_at
        await self.session.flush()
