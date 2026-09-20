from app import models  # noqa: F401
from app.db.base import Base


def test_authentication_metadata_contains_all_phase_one_tables() -> None:
    assert {
        "roles",
        "permissions",
        "role_permissions",
        "users",
        "auth_sessions",
        "audit_logs",
    }.issubset(Base.metadata.tables)
