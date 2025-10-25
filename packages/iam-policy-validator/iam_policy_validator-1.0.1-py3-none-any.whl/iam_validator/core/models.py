"""Data models for AWS IAM policy validation.

This module defines Pydantic models for AWS service information,
IAM policies, and validation results.
"""

from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field


# AWS Service Reference Models
class ServiceInfo(BaseModel):
    """Basic information about an AWS service."""

    service: str
    url: str


class ActionDetail(BaseModel):
    """Details about an AWS IAM action."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(alias="Name")
    action_condition_keys: list[str] | None = Field(
        default_factory=list, alias="ActionConditionKeys"
    )
    resources: list[dict[str, Any]] | None = Field(default_factory=list, alias="Resources")
    annotations: dict[str, Any] | None = Field(default=None, alias="Annotations")
    supported_by: dict[str, Any] | None = Field(default=None, alias="SupportedBy")


class ResourceType(BaseModel):
    """Details about an AWS resource type."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(alias="Name")
    arn_pattern: str | None = Field(default=None, alias="ARNPattern")
    condition_keys: list[str] | None = Field(default_factory=list, alias="ConditionKeys")


class ConditionKey(BaseModel):
    """Details about an AWS condition key."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(alias="Name")
    description: str | None = Field(default=None, alias="Description")
    types: list[str] | None = Field(default_factory=list, alias="Types")


class ServiceDetail(BaseModel):
    """Detailed information about an AWS service."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(alias="Name")
    prefix: str | None = None  # Not always present in API response
    actions: dict[str, ActionDetail] = Field(default_factory=dict)
    resources: dict[str, ResourceType] = Field(default_factory=dict)
    condition_keys: dict[str, ConditionKey] = Field(default_factory=dict)
    version: str | None = Field(default=None, alias="Version")

    # Raw API data
    actions_list: list[ActionDetail] = Field(default_factory=list, alias="Actions")
    resources_list: list[ResourceType] = Field(default_factory=list, alias="Resources")
    condition_keys_list: list[ConditionKey] = Field(default_factory=list, alias="ConditionKeys")

    def model_post_init(self, __context: Any) -> None:
        """Convert lists to dictionaries for easier lookup."""
        del __context  # Unused
        # Convert actions list to dict
        self.actions = {action.name: action for action in self.actions_list}
        # Convert resources list to dict
        self.resources = {resource.name: resource for resource in self.resources_list}
        # Convert condition keys list to dict
        self.condition_keys = {ck.name: ck for ck in self.condition_keys_list}


# IAM Policy Models
class Statement(BaseModel):
    """IAM policy statement."""

    model_config = ConfigDict(populate_by_name=True)

    sid: str | None = Field(default=None, alias="Sid")
    effect: str = Field(alias="Effect")
    action: list[str] | str | None = Field(default=None, alias="Action")
    not_action: list[str] | str | None = Field(default=None, alias="NotAction")
    resource: list[str] | str | None = Field(default=None, alias="Resource")
    not_resource: list[str] | str | None = Field(default=None, alias="NotResource")
    condition: dict[str, dict[str, Any]] | None = Field(default=None, alias="Condition")
    principal: dict[str, Any] | str | None = Field(default=None, alias="Principal")
    not_principal: dict[str, Any] | str | None = Field(default=None, alias="NotPrincipal")
    # Line number metadata (populated during parsing)
    line_number: int | None = Field(default=None, exclude=True)

    def get_actions(self) -> list[str]:
        """Get list of actions, handling both string and list formats."""
        if self.action is None:
            return []
        return [self.action] if isinstance(self.action, str) else self.action

    def get_resources(self) -> list[str]:
        """Get list of resources, handling both string and list formats."""
        if self.resource is None:
            return []
        return [self.resource] if isinstance(self.resource, str) else self.resource


class IAMPolicy(BaseModel):
    """IAM policy document."""

    model_config = ConfigDict(populate_by_name=True)

    version: str = Field(alias="Version")
    statement: list[Statement] = Field(alias="Statement")
    id: str | None = Field(default=None, alias="Id")


# Validation Result Models
class ValidationIssue(BaseModel):
    """A single validation issue found in a policy.

    Severity Levels:
    - IAM Validity: "error", "warning", "info"
      (for issues that make the policy invalid according to AWS IAM rules)
    - Security: "critical", "high", "medium", "low"
      (for security best practices and configuration issues)
    """

    severity: str  # "error", "warning", "info" OR "critical", "high", "medium", "low"
    statement_sid: str | None = None
    statement_index: int
    issue_type: str  # "invalid_action", "invalid_condition_key", "invalid_resource", etc.
    message: str
    action: str | None = None
    resource: str | None = None
    condition_key: str | None = None
    suggestion: str | None = None
    line_number: int | None = None  # Line number in the policy file (if available)

    # Severity level constants (ClassVar to avoid Pydantic treating them as fields)
    VALID_SEVERITIES: ClassVar[frozenset[str]] = frozenset(
        [
            "error",
            "warning",
            "info",  # IAM validity severities
            "critical",
            "high",
            "medium",
            "low",  # Security severities
        ]
    )

    # Severity ordering for fail_on_severity (higher value = more severe)
    SEVERITY_RANK: ClassVar[dict[str, int]] = {
        "error": 100,  # IAM validity errors (highest)
        "critical": 90,  # Critical security issues
        "high": 70,  # High security issues
        "warning": 50,  # IAM validity warnings
        "medium": 40,  # Medium security issues
        "low": 20,  # Low security issues
        "info": 10,  # Informational (lowest)
    }

    def get_severity_rank(self) -> int:
        """Get the numeric rank of this issue's severity (higher = more severe)."""
        return self.SEVERITY_RANK.get(self.severity, 0)

    def is_security_severity(self) -> bool:
        """Check if this issue uses security severity levels (critical/high/medium/low)."""
        return self.severity in {"critical", "high", "medium", "low"}

    def is_validity_severity(self) -> bool:
        """Check if this issue uses IAM validity severity levels (error/warning/info)."""
        return self.severity in {"error", "warning", "info"}

    def to_pr_comment(self, include_identifier: bool = True) -> str:
        """Format issue as a PR comment.

        Args:
            include_identifier: Whether to include bot identifier (for cleanup)

        Returns:
            Formatted comment string
        """
        severity_emoji = {
            # IAM validity severities
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
            # Security severities
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🔵",
        }
        emoji = severity_emoji.get(self.severity, "•")

        parts = []

        # Add identifier for bot comment cleanup
        if include_identifier:
            parts.append("🤖 IAM Policy Validator\n")

        # Build statement context for better navigation
        statement_context = f"Statement[{self.statement_index}]"
        if self.statement_sid:
            statement_context = f"`{self.statement_sid}` ({statement_context})"

        # Main issue header with statement context
        parts.append(f"{emoji} **{self.severity.upper()}** in **{statement_context}**")
        parts.append("")
        parts.append(self.message)

        # Add affected fields section if any are present
        if self.action or self.resource or self.condition_key:
            parts.append("")
            parts.append("**Affected Fields:**")
            if self.action:
                parts.append(f"  - Action: `{self.action}`")
            if self.resource:
                parts.append(f"  - Resource: `{self.resource}`")
            if self.condition_key:
                parts.append(f"  - Condition Key: `{self.condition_key}`")

        # Add suggestion if present
        if self.suggestion:
            parts.append("")
            parts.append(f"💡 **Suggestion**: {self.suggestion}")

        return "\n".join(parts)


class PolicyValidationResult(BaseModel):
    """Result of validating a single IAM policy."""

    policy_file: str
    is_valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
    actions_checked: int = 0
    condition_keys_checked: int = 0
    resources_checked: int = 0


class ValidationReport(BaseModel):
    """Complete validation report for all policies."""

    total_policies: int
    valid_policies: int
    invalid_policies: int
    total_issues: int
    results: list[PolicyValidationResult] = Field(default_factory=list)

    def get_summary(self) -> str:
        """Generate a human-readable summary."""
        return (
            f"Validated {self.total_policies} policies: "
            f"{self.valid_policies} valid, {self.invalid_policies} invalid, "
            f"{self.total_issues} total issues found"
        )
