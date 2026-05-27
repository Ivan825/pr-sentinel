from pr_sentinel.core.enums import FindingCategory, Severity

SEVERITY_WEIGHTS: dict[Severity, int] = {
    Severity.INFO: 1,
    Severity.LOW: 4,
    Severity.MEDIUM: 8,
    Severity.HIGH: 16,
    Severity.CRITICAL: 28,
}


CATEGORY_MULTIPLIERS: dict[FindingCategory, float] = {
    FindingCategory.SECURITY: 1.35,
    FindingCategory.AUTH: 1.3,
    FindingCategory.API: 1.15,
    FindingCategory.DATABASE: 1.2,
    FindingCategory.CONFIG: 1.05,
    FindingCategory.DEPENDENCY: 1.0,
    FindingCategory.TEST: 1.15,
    FindingCategory.INFRA: 1.1,
    FindingCategory.GENERAL: 1.0,
}


HIGH_RISK_RULE_BONUSES: dict[str, int] = {
    "SEC_001_HARDCODED_SECRET": 12,
    "AUTH_001_PERMISSION_CHECK_REMOVED": 10,
    "SEC_002_RAW_SQL_CONCATENATION": 8,
    "CFG_001_CORS_WILDCARD_ENABLED": 6,
    "TEST_001_RISKY_SOURCE_WITHOUT_MATCHING_TEST": 5,
}


MAX_CATEGORY_CONTRIBUTION: dict[str, int] = {
    "SECURITY": 45,
    "AUTH": 40,
    "API": 30,
    "DATABASE": 30,
    "CONFIG": 25,
    "DEPENDENCY": 25,
    "TEST": 25,
    "INFRA": 25,
    "GENERAL": 20,
}