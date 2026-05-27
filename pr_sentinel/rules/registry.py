from pr_sentinel.core.models import Finding
from pr_sentinel.rules.base import BaseRule, RuleContext


class RuleRegistry:
    def __init__(self) -> None:
        self._rules: list[BaseRule] = []

    def register(self, rule: BaseRule) -> None:
        existing_ids = {registered_rule.metadata.rule_id for registered_rule in self._rules}

        if rule.metadata.rule_id in existing_ids:
            raise ValueError(f"Duplicate rule id registered: {rule.metadata.rule_id}")

        self._rules.append(rule)

    def register_many(self, rules: list[BaseRule]) -> None:
        for rule in rules:
            self.register(rule)

    def all_rules(self) -> list[BaseRule]:
        return list(self._rules)

    def evaluate_all(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []

        for rule in self._rules:
            findings.extend(rule.evaluate(context))

        return findings