from enum import StrEnum


class RoleName(StrEnum):
    ADMIN = "ADMIN"
    NOC_ENGINEER = "NOC_ENGINEER"
    SUPPORT = "SUPPORT"
    FIELD_TECHNICIAN = "FIELD_TECHNICIAN"
    VIEWER = "VIEWER"


class PermissionCode(StrEnum):
    USERS_MANAGE = "users:manage"
    ROLES_READ = "roles:read"
    AUDIT_READ = "audit:read"
    INVENTORY_READ = "inventory:read"
    SITES_MANAGE = "sites:manage"
    DEVICES_MANAGE = "devices:manage"
    INTERFACES_MANAGE = "interfaces:manage"
    COLLECTOR_ASSIGNMENTS_MANAGE = "collector_assignments:manage"


class AuditEventType(StrEnum):
    LOGIN_SUCCEEDED = "auth.login_succeeded"
    LOGIN_FAILED = "auth.login_failed"
    LOGOUT = "auth.logout"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DISABLED = "user.disabled"
    USER_ROLE_CHANGED = "user.role_changed"
