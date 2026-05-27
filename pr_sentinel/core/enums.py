from enum import StrEnum


class Severity(StrEnum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskBand(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FindingCategory(StrEnum):
    AUTH = "AUTH"
    SECURITY = "SECURITY"
    API = "API"
    DATABASE = "DATABASE"
    CONFIG = "CONFIG"
    DEPENDENCY = "DEPENDENCY"
    TEST = "TEST"
    INFRA = "INFRA"
    GENERAL = "GENERAL"


class FileChangeStatus(StrEnum):
    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"
    RENAMED = "renamed"


class FileCategory(StrEnum):
    AUTH = "AUTH"
    SECURITY = "SECURITY"
    API = "API"
    DATABASE = "DATABASE"
    CONFIG = "CONFIG"
    DEPENDENCY = "DEPENDENCY"
    TEST = "TEST"
    INFRA = "INFRA"
    FRONTEND = "FRONTEND"
    BACKEND = "BACKEND"
    DOCUMENTATION = "DOCUMENTATION"
    UNKNOWN = "UNKNOWN"