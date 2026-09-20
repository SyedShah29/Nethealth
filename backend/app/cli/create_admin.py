import argparse
import asyncio
import sys
from getpass import getpass

from pydantic import SecretStr, ValidationError

from app.core.errors import AppError
from app.db.session import async_session_factory
from app.models.enums import RoleName
from app.schemas.auth import UserCreateRequest
from app.security.passwords import get_password_hasher
from app.services.users import UserService


async def create_admin(name: str, email: str, password: SecretStr) -> None:
    payload = UserCreateRequest(name=name, email=email, password=password, role=RoleName.ADMIN)
    async with async_session_factory() as session:
        service = UserService(session, get_password_hasher())
        await service.create_user(
            name=payload.name,
            email=payload.email,
            password=payload.password,
            role_name=payload.role,
            actor=None,
            request_id=None,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the first NetHealth administrator.")
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    password = getpass("Password (minimum 12 characters): ")
    confirmation = getpass("Confirm password: ")
    if password != confirmation:
        parser.error("Passwords do not match.")
    try:
        asyncio.run(create_admin(args.name, args.email, SecretStr(password)))
    except ValidationError as exc:
        parser.error(str(exc))
    except AppError as exc:
        parser.error(exc.message)
    sys.stdout.write("Administrator created successfully.\n")


if __name__ == "__main__":
    main()
