"""Unit tests for action_condition_enforcement check."""

import pytest

from iam_validator.checks.action_condition_enforcement import (
    ActionConditionEnforcementCheck,
)
from iam_validator.core.check_registry import CheckConfig
from iam_validator.core.models import Statement


class TestActionConditionEnforcement:
    """Test the ActionConditionEnforcementCheck class."""

    @pytest.fixture
    def check(self):
        """Create a check instance."""
        return ActionConditionEnforcementCheck()

    @pytest.fixture
    def mock_fetcher(self):
        """Create a mock AWS service fetcher."""
        return None  # Not needed for these tests

    def test_check_id(self, check):
        """Test that check has correct ID."""
        assert check.check_id == "action_condition_enforcement"

    def test_description(self, check):
        """Test that check has a description."""
        assert len(check.description) > 0
        assert "condition" in check.description.lower()

    @pytest.mark.asyncio
    async def test_none_of_actions_forbidden(self, check, mock_fetcher):
        """Test that forbidden actions are detected."""
        # Config with forbidden actions
        config = CheckConfig(
            check_id="action_condition_enforcement",
            enabled=True,
            severity="error",
            config={
                "action_condition_requirements": [
                    {
                        "actions": {"none_of": ["iam:DeleteUser", "s3:DeleteBucket"]},
                        "description": "These actions are forbidden",
                    }
                ]
            },
        )

        # Statement with forbidden action
        statement = Statement(
            sid="TestStatement",
            effect="Allow",
            action=["iam:DeleteUser", "s3:GetObject"],
            resource="*",
        )

        issues = await check.execute(statement, 0, mock_fetcher, config)

        assert len(issues) == 1
        assert issues[0].issue_type == "forbidden_action_present"
        assert "iam:DeleteUser" in issues[0].message
        assert "FORBIDDEN" in issues[0].message

    @pytest.mark.asyncio
    async def test_none_of_actions_allowed(self, check, mock_fetcher):
        """Test that allowed actions don't trigger none_of."""
        config = CheckConfig(
            check_id="action_condition_enforcement",
            enabled=True,
            severity="error",
            config={
                "action_condition_requirements": [
                    {
                        "actions": {"none_of": ["iam:DeleteUser", "s3:DeleteBucket"]},
                        "description": "These actions are forbidden",
                    }
                ]
            },
        )

        # Statement without forbidden actions
        statement = Statement(
            sid="TestStatement",
            effect="Allow",
            action=["s3:GetObject", "s3:PutObject"],
            resource="*",
        )

        issues = await check.execute(statement, 0, mock_fetcher, config)

        assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_none_of_conditions_forbidden(self, check, mock_fetcher):
        """Test that forbidden conditions are detected."""
        config = CheckConfig(
            check_id="action_condition_enforcement",
            enabled=True,
            severity="error",
            config={
                "action_condition_requirements": [
                    {
                        "actions": ["s3:GetObject"],
                        "required_conditions": {
                            "none_of": [
                                {
                                    "condition_key": "aws:SecureTransport",
                                    "expected_value": False,
                                    "description": "Never allow insecure transport",
                                }
                            ]
                        },
                    }
                ]
            },
        )

        # Statement with forbidden condition
        statement = Statement(
            sid="TestStatement",
            effect="Allow",
            action=["s3:GetObject"],
            resource="*",
            condition={"Bool": {"aws:SecureTransport": False}},
        )

        issues = await check.execute(statement, 0, mock_fetcher, config)

        assert len(issues) == 1
        assert issues[0].issue_type == "forbidden_condition_present"
        assert "aws:SecureTransport" in issues[0].message
        assert "FORBIDDEN" in issues[0].message

    @pytest.mark.asyncio
    async def test_none_of_conditions_allowed(self, check, mock_fetcher):
        """Test that allowed conditions don't trigger none_of."""
        config = CheckConfig(
            check_id="action_condition_enforcement",
            enabled=True,
            severity="error",
            config={
                "action_condition_requirements": [
                    {
                        "actions": ["s3:GetObject"],
                        "required_conditions": {
                            "none_of": [
                                {
                                    "condition_key": "aws:SecureTransport",
                                    "expected_value": False,
                                }
                            ]
                        },
                    }
                ]
            },
        )

        # Statement with allowed condition (SecureTransport: true)
        statement = Statement(
            sid="TestStatement",
            effect="Allow",
            action=["s3:GetObject"],
            resource="*",
            condition={"Bool": {"aws:SecureTransport": True}},
        )

        issues = await check.execute(statement, 0, mock_fetcher, config)

        assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_all_of_conditions_missing(self, check, mock_fetcher):
        """Test that missing required conditions (all_of) are detected."""
        config = CheckConfig(
            check_id="action_condition_enforcement",
            enabled=True,
            severity="error",
            config={
                "action_condition_requirements": [
                    {
                        "actions": ["ec2:RunInstances"],
                        "required_conditions": {
                            "all_of": [
                                {"condition_key": "aws:RequestTag/Owner"},
                                {"condition_key": "aws:RequestTag/CostCenter"},
                            ]
                        },
                    }
                ]
            },
        )

        # Statement missing both conditions
        statement = Statement(
            sid="TestStatement",
            effect="Allow",
            action=["ec2:RunInstances"],
            resource="*",
        )

        issues = await check.execute(statement, 0, mock_fetcher, config)

        assert len(issues) == 2  # One for each missing condition
        assert all(issue.issue_type == "missing_required_condition" for issue in issues)

    @pytest.mark.asyncio
    async def test_all_of_conditions_present(self, check, mock_fetcher):
        """Test that all_of passes when all conditions present."""
        config = CheckConfig(
            check_id="action_condition_enforcement",
            enabled=True,
            severity="error",
            config={
                "action_condition_requirements": [
                    {
                        "actions": ["ec2:RunInstances"],
                        "required_conditions": {
                            "all_of": [
                                {"condition_key": "aws:RequestTag/Owner"},
                                {"condition_key": "aws:RequestTag/CostCenter"},
                            ]
                        },
                    }
                ]
            },
        )

        # Statement with all required conditions
        statement = Statement(
            sid="TestStatement",
            effect="Allow",
            action=["ec2:RunInstances"],
            resource="*",
            condition={
                "StringEquals": {
                    "aws:RequestTag/Owner": "team-a",
                    "aws:RequestTag/CostCenter": "engineering",
                }
            },
        )

        issues = await check.execute(statement, 0, mock_fetcher, config)

        assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_any_of_conditions_missing_all(self, check, mock_fetcher):
        """Test that any_of fails when no conditions present."""
        config = CheckConfig(
            check_id="action_condition_enforcement",
            enabled=True,
            severity="error",
            config={
                "action_condition_requirements": [
                    {
                        "actions": ["cloudformation:CreateStack"],
                        "required_conditions": {
                            "any_of": [
                                {"condition_key": "aws:SourceIp"},
                                {"condition_key": "aws:SourceVpce"},
                            ]
                        },
                    }
                ]
            },
        )

        # Statement with no conditions
        statement = Statement(
            sid="TestStatement",
            effect="Allow",
            action=["cloudformation:CreateStack"],
            resource="*",
        )

        issues = await check.execute(statement, 0, mock_fetcher, config)

        assert len(issues) == 1
        assert issues[0].issue_type == "missing_required_condition_any_of"
        assert "at least ONE" in issues[0].message

    @pytest.mark.asyncio
    async def test_any_of_conditions_one_present(self, check, mock_fetcher):
        """Test that any_of passes when at least one condition present."""
        config = CheckConfig(
            check_id="action_condition_enforcement",
            enabled=True,
            severity="error",
            config={
                "action_condition_requirements": [
                    {
                        "actions": ["cloudformation:CreateStack"],
                        "required_conditions": {
                            "any_of": [
                                {"condition_key": "aws:SourceIp"},
                                {"condition_key": "aws:SourceVpce"},
                            ]
                        },
                    }
                ]
            },
        )

        # Statement with one of the required conditions
        statement = Statement(
            sid="TestStatement",
            effect="Allow",
            action=["cloudformation:CreateStack"],
            resource="*",
            condition={"IpAddress": {"aws:SourceIp": "10.0.0.0/8"}},
        )

        issues = await check.execute(statement, 0, mock_fetcher, config)

        assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_deny_statements_ignored(self, check, mock_fetcher):
        """Test that Deny statements are not checked."""
        config = CheckConfig(
            check_id="action_condition_enforcement",
            enabled=True,
            severity="error",
            config={
                "action_condition_requirements": [
                    {
                        "actions": {"none_of": ["iam:DeleteUser"]},
                    }
                ]
            },
        )

        # Deny statement with forbidden action (should be ignored)
        statement = Statement(
            sid="TestStatement",
            effect="Deny",
            action=["iam:DeleteUser"],
            resource="*",
        )

        issues = await check.execute(statement, 0, mock_fetcher, config)

        assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_simple_required_condition(self, check, mock_fetcher):
        """Test that simple required conditions work correctly."""
        config = CheckConfig(
            check_id="action_condition_enforcement",
            enabled=True,
            severity="error",
            config={
                "action_condition_requirements": [
                    {
                        "actions": ["iam:CreateUser"],
                        "required_conditions": [
                            {
                                "condition_key": "aws:MultiFactorAuthPresent",
                                "expected_value": True,
                            }
                        ],
                    }
                ]
            },
        )

        # Statement missing MFA condition
        statement = Statement(
            sid="TestStatement",
            effect="Allow",
            action=["iam:CreateUser"],
            resource="*",
        )

        issues = await check.execute(statement, 0, mock_fetcher, config)

        assert len(issues) == 1
        assert "aws:MultiFactorAuthPresent" in issues[0].message

    @pytest.mark.asyncio
    async def test_combined_all_of_and_none_of(self, check, mock_fetcher):
        """Test combining all_of and none_of in same requirement."""
        config = CheckConfig(
            check_id="action_condition_enforcement",
            enabled=True,
            severity="error",
            config={
                "action_condition_requirements": [
                    {
                        "actions": ["iam:CreateUser"],
                        "required_conditions": {
                            "all_of": [
                                {
                                    "condition_key": "aws:MultiFactorAuthPresent",
                                    "expected_value": True,
                                }
                            ],
                            "none_of": [
                                {
                                    "condition_key": "aws:SourceIp",
                                    "expected_value": "0.0.0.0/0",
                                }
                            ],
                        },
                    }
                ]
            },
        )

        # Statement with MFA but wildcard IP (should fail on none_of)
        statement = Statement(
            sid="TestStatement",
            effect="Allow",
            action=["iam:CreateUser"],
            resource="*",
            condition={
                "Bool": {"aws:MultiFactorAuthPresent": True},
                "IpAddress": {"aws:SourceIp": "0.0.0.0/0"},
            },
        )

        issues = await check.execute(statement, 0, mock_fetcher, config)

        assert len(issues) == 1
        assert issues[0].issue_type == "forbidden_condition_present"
        assert "0.0.0.0/0" in issues[0].message
