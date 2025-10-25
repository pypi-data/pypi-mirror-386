"""Condition key validation check - validates condition keys against AWS definitions."""

from iam_validator.core.aws_fetcher import AWSServiceFetcher
from iam_validator.core.check_registry import CheckConfig, PolicyCheck
from iam_validator.core.models import Statement, ValidationIssue


class ConditionKeyValidationCheck(PolicyCheck):
    """Validates condition keys against AWS service definitions and global keys."""

    @property
    def check_id(self) -> str:
        return "condition_key_validation"

    @property
    def description(self) -> str:
        return "Validates condition keys against AWS service definitions"

    @property
    def default_severity(self) -> str:
        return "error"  # Invalid condition keys are IAM policy errors

    async def execute(
        self,
        statement: Statement,
        statement_idx: int,
        fetcher: AWSServiceFetcher,
        config: CheckConfig,
    ) -> list[ValidationIssue]:
        """Execute condition key validation on a statement."""
        issues = []

        # Get conditions from statement
        if not statement.condition:
            return issues

        statement_sid = statement.sid
        line_number = statement.line_number
        actions = statement.get_actions()

        # Extract all condition keys from all condition operators
        for operator, conditions in statement.condition.items():
            for condition_key in conditions.keys():
                # Validate this condition key against each action in the statement
                for action in actions:
                    # Skip wildcard actions
                    if action == "*":
                        continue

                    is_valid, error_msg = await fetcher.validate_condition_key(
                        action, condition_key
                    )

                    if not is_valid:
                        issues.append(
                            ValidationIssue(
                                severity=self.get_severity(config),
                                statement_sid=statement_sid,
                                statement_index=statement_idx,
                                issue_type="invalid_condition_key",
                                message=error_msg or f"Invalid condition key: {condition_key}",
                                action=action,
                                condition_key=condition_key,
                                line_number=line_number,
                            )
                        )
                        # Only report once per condition key (not per action)
                        break

        return issues
