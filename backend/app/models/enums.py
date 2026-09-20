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
    ROLES_MANAGE = "roles:manage"
    AUDIT_READ = "audit:read"
    INVENTORY_READ = "inventory:read"
    SITES_MANAGE = "sites:manage"
    DEVICES_MANAGE = "devices:manage"
    INTERFACES_MANAGE = "interfaces:manage"
    COLLECTOR_ASSIGNMENTS_MANAGE = "collector_assignments:manage"
    THRESHOLDS_MANAGE = "thresholds:manage"
    COLLECTORS_MANAGE = "collectors:manage"
    RULES_MANAGE = "rules:manage"
    NOTIFICATIONS_MANAGE = "notifications:manage"
    OPERATIONAL_READ = "operational:read"
    TOPOLOGY_READ = "topology:read"
    METRICS_READ = "metrics:read"
    SUBSCRIBERS_READ = "subscribers:read"
    INCIDENTS_MANAGE = "incidents:manage"
    INCIDENTS_READ = "incidents:read"
    INCIDENTS_ACKNOWLEDGE = "incidents:acknowledge"
    DIAGNOSTICS_READ = "diagnostics:read"
    JOBS_READ = "jobs:read"
    JOBS_UPDATE = "jobs:update"
    FIELD_NOTES_CREATE = "field_notes:create"
    FIELD_PHOTOS_UPLOAD = "field_photos:upload"
    DASHBOARDS_READ = "dashboards:read"


class AuditEventType(StrEnum):
    LOGIN_SUCCEEDED = "auth.login_succeeded"
    LOGIN_FAILED = "auth.login_failed"
    LOGOUT = "auth.logout"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DISABLED = "user.disabled"
    USER_ROLE_CHANGED = "user.role_changed"
    CONFIGURATION_CHANGED = "configuration.changed"
    THRESHOLD_CHANGED = "threshold.changed"
    INCIDENT_ACTION = "incident.action"


class DeviceType(StrEnum):
    CORE_ROUTER = "CORE_ROUTER"
    EDGE_ROUTER = "EDGE_ROUTER"
    BNG = "BNG"
    BRAS = "BRAS"
    AGGREGATION_SWITCH = "AGGREGATION_SWITCH"
    ACCESS_SWITCH = "ACCESS_SWITCH"
    OLT = "OLT"
    OTHER = "OTHER"
