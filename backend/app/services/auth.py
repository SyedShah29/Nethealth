from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe

from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import AppError
from app.models.auth import AuthSession, User
from app.models.enums import AuditEventType
from app.repositories.audit import AuditLogRepository
from app.repositories.auth import AuthSessionRepository, UserRepository
from app.security.passwords import PasswordHasher
from app.services.audit import AuditService


@dataclass(frozen=True, slots=True)
class LoginResult:
    user: User
    token: str
    expires_at: datetime


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        password_hasher: PasswordHasher,
    ) -> None:
        self.session = session
        self.settings = settings
        self.password_hasher = password_hasher
        self.users = UserRepository(session)
        self.sessions = AuthSessionRepository(session)
        self.audit = AuditService(AuditLogRepository(session))

    @staticmethod
    def hash_token(token: str) -> str:
        return sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def fingerprint(subject: str) -> str:
        return sha256(subject.strip().lower().encode("utf-8")).hexdigest()

    @staticmethod
    def _invalid_credentials() -> AppError:
        return AppError(
            code="INVALID_CREDENTIALS",
            message="The email or password is incorrect.",
            status_code=401,
            headers={"WWW-Authenticate": "Session"},
        )

    async def login(
        self,
        email: str,
        password: SecretStr,
        *,
        request_id: str | None,
    ) -> LoginResult:
        now = datetime.now(UTC)
        supplied_password = password.get_secret_value()
        user = await self.users.get_by_email_for_update(email)

        if user is None:
            self.password_hasher.verify(supplied_password, self.password_hasher.dummy_hash)
            await self.audit.record(
                AuditEventType.LOGIN_FAILED,
                success=False,
                request_id=request_id,
                subject_fingerprint=self.fingerprint(email),
                event_metadata={"reason": "invalid_credentials"},
            )
            await self.session.commit()
            raise self._invalid_credentials()

        if user.locked_until is not None and user.locked_until > now:
            self.password_hasher.verify(supplied_password, user.password_hash)
            await self._record_failed_login(user, request_id, reason="locked")
            raise self._invalid_credentials()

        if not user.active:
            self.password_hasher.verify(supplied_password, user.password_hash)
            await self._record_failed_login(user, request_id, reason="inactive")
            raise self._invalid_credentials()

        if not self.password_hasher.verify(supplied_password, user.password_hash):
            user.failed_login_count += 1
            if user.failed_login_count >= self.settings.auth_max_failed_attempts:
                user.locked_until = now + timedelta(minutes=self.settings.auth_lockout_minutes)
            await self._record_failed_login(user, request_id, reason="invalid_credentials")
            raise self._invalid_credentials()

        if self.password_hasher.needs_rehash(user.password_hash):
            user.password_hash = self.password_hasher.hash(supplied_password)
        user.failed_login_count = 0
        user.locked_until = None
        user.last_login = now

        token = token_urlsafe(48)
        expires_at = now + timedelta(hours=self.settings.auth_session_hours)
        await self.sessions.add(
            AuthSession(
                user_id=user.id,
                token_hash=self.hash_token(token),
                expires_at=expires_at,
            )
        )
        await self.audit.record(
            AuditEventType.LOGIN_SUCCEEDED,
            success=True,
            actor_user_id=user.id,
            target_user_id=user.id,
            request_id=request_id,
        )
        await self.session.commit()
        return LoginResult(user=user, token=token, expires_at=expires_at)

    async def _record_failed_login(
        self,
        user: User,
        request_id: str | None,
        *,
        reason: str,
    ) -> None:
        await self.audit.record(
            AuditEventType.LOGIN_FAILED,
            success=False,
            target_user_id=user.id,
            request_id=request_id,
            subject_fingerprint=self.fingerprint(user.email),
            event_metadata={"reason": reason},
        )
        await self.session.commit()

    async def authenticate_session(self, token: str | None) -> User:
        if not token:
            raise self._authentication_required()
        auth_session = await self.sessions.get_by_token_hash(self.hash_token(token))
        now = datetime.now(UTC)
        if (
            auth_session is None
            or auth_session.revoked_at is not None
            or auth_session.expires_at <= now
            or not auth_session.user.active
        ):
            raise self._authentication_required()
        return auth_session.user

    async def logout(self, token: str | None, *, request_id: str | None) -> None:
        if not token:
            return
        auth_session = await self.sessions.get_by_token_hash(self.hash_token(token))
        if auth_session is None or auth_session.revoked_at is not None:
            return
        now = datetime.now(UTC)
        await self.sessions.revoke(auth_session, now)
        await self.audit.record(
            AuditEventType.LOGOUT,
            success=True,
            actor_user_id=auth_session.user_id,
            target_user_id=auth_session.user_id,
            request_id=request_id,
        )
        await self.session.commit()

    @staticmethod
    def _authentication_required() -> AppError:
        return AppError(
            code="AUTHENTICATION_REQUIRED",
            message="Authentication is required.",
            status_code=401,
            headers={"WWW-Authenticate": "Session"},
        )
