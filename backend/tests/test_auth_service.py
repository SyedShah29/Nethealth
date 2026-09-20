from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import AppError
from app.models.auth import AuthSession
from app.repositories.auth import AuthSessionRepository, UserRepository
from app.security.passwords import PasswordHasher
from app.services.audit import AuditService
from app.services.auth import AuthService
from tests.factories import make_user


def make_service(password_hasher: PasswordHasher) -> tuple[AuthService, AsyncMock]:
    session = AsyncMock(spec=AsyncSession)
    settings = Settings(auth_max_failed_attempts=2, auth_lockout_minutes=10)
    service = AuthService(session, settings, password_hasher)
    service.users = AsyncMock(spec=UserRepository)
    service.sessions = AsyncMock(spec=AuthSessionRepository)
    service.audit = AsyncMock(spec=AuditService)
    return service, session


async def test_login_creates_hashed_expiring_session_and_audit(
    password_hasher: PasswordHasher,
) -> None:
    service, session = make_service(password_hasher)
    password = "a secure test password"
    user = make_user(password_hash=password_hasher.hash(password))
    service.users.get_by_email_for_update.return_value = user

    result = await service.login(
        user.email,
        SecretStr(password),
        request_id="request-1",
    )

    assert result.token
    created_session = service.sessions.add.await_args.args[0]
    assert isinstance(created_session, AuthSession)
    assert created_session.token_hash == service.hash_token(result.token)
    assert result.token not in created_session.token_hash
    assert result.expires_at > datetime.now(UTC)
    service.audit.record.assert_awaited_once()
    session.commit.assert_awaited_once()


async def test_failed_login_locks_account_without_returning_sensitive_reason(
    password_hasher: PasswordHasher,
) -> None:
    service, session = make_service(password_hasher)
    user = make_user(password_hash=password_hasher.hash("valid password value"))
    user.failed_login_count = 1
    service.users.get_by_email_for_update.return_value = user

    with pytest.raises(AppError) as error:
        await service.login(
            user.email,
            SecretStr("invalid password value"),
            request_id="request-2",
        )

    assert error.value.code == "INVALID_CREDENTIALS"
    assert error.value.status_code == 401
    assert "locked" not in error.value.message.lower()
    assert user.failed_login_count == 2
    assert user.locked_until is not None
    service.audit.record.assert_awaited_once()
    session.commit.assert_awaited_once()


async def test_unknown_user_gets_same_generic_login_failure(
    password_hasher: PasswordHasher,
) -> None:
    service, session = make_service(password_hasher)
    service.users.get_by_email_for_update.return_value = None

    with pytest.raises(AppError) as error:
        await service.login(
            "missing@example.test",
            SecretStr("invalid password value"),
            request_id="request-3",
        )

    assert error.value.code == "INVALID_CREDENTIALS"
    service.audit.record.assert_awaited_once()
    session.commit.assert_awaited_once()


async def test_expired_session_is_rejected(password_hasher: PasswordHasher) -> None:
    service, _session = make_service(password_hasher)
    user = make_user()
    service.sessions.get_by_token_hash.return_value = AuthSession(
        user_id=user.id,
        token_hash=service.hash_token("expired-token"),
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
        user=user,
    )

    with pytest.raises(AppError) as error:
        await service.authenticate_session("expired-token")

    assert error.value.code == "AUTHENTICATION_REQUIRED"
    assert error.value.status_code == 401


async def test_logout_revokes_session_and_creates_audit(
    password_hasher: PasswordHasher,
) -> None:
    service, session = make_service(password_hasher)
    user = make_user()
    auth_session = AuthSession(
        user_id=user.id,
        token_hash=service.hash_token("active-token"),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        user=user,
    )
    service.sessions.get_by_token_hash.return_value = auth_session

    await service.logout("active-token", request_id="request-4")

    service.sessions.revoke.assert_awaited_once()
    service.audit.record.assert_awaited_once()
    session.commit.assert_awaited_once()
