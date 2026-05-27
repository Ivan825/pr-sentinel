from pr_sentinel.rules.auth_rules import PermissionCheckRemovedRule
from pr_sentinel.rules.config_rules import CorsWildcardRule, DebugModeEnabledRule
from pr_sentinel.rules.dependency_rules import DependencyFileChangedRule
from pr_sentinel.rules.registry import RuleRegistry
from pr_sentinel.rules.security_rules import HardcodedSecretRule, RawSqlConcatenationRule


def build_default_rule_registry() -> RuleRegistry:
    registry = RuleRegistry()

    registry.register_many(
        [
            HardcodedSecretRule(),
            RawSqlConcatenationRule(),
            CorsWildcardRule(),
            DebugModeEnabledRule(),
            DependencyFileChangedRule(),
            PermissionCheckRemovedRule(),
        ]
    )

    return registry