"""Unit tests for AWS Global Conditions module."""

import pytest

from iam_validator.core.aws_global_conditions import (
    AWS_GLOBAL_CONDITION_KEYS,
    AWSGlobalConditions,
    get_global_conditions,
)


class TestAWSGlobalConditions:
    """Test the AWSGlobalConditions class."""

    @pytest.fixture
    def conditions(self):
        """Create a fresh AWSGlobalConditions instance."""
        return AWSGlobalConditions()

    def test_initialization(self, conditions):
        """Test that the class initializes correctly."""
        assert conditions._global_keys is not None
        assert len(conditions._global_keys) > 0
        assert conditions._patterns is not None
        assert len(conditions._patterns) > 0

    def test_valid_explicit_global_key(self, conditions):
        """Test validation of explicit global condition keys."""
        assert conditions.is_valid_global_key("aws:SourceIp") is True
        assert conditions.is_valid_global_key("aws:PrincipalArn") is True
        assert conditions.is_valid_global_key("aws:CurrentTime") is True
        assert conditions.is_valid_global_key("aws:SecureTransport") is True
        assert conditions.is_valid_global_key("aws:MultiFactorAuthPresent") is True

    def test_invalid_global_key(self, conditions):
        """Test validation of invalid condition keys."""
        assert conditions.is_valid_global_key("aws:InvalidKey") is False
        assert conditions.is_valid_global_key("custom:MyKey") is False
        assert conditions.is_valid_global_key("s3:BucketName") is False
        assert conditions.is_valid_global_key("") is False

    def test_request_tag_pattern(self, conditions):
        """Test validation of aws:RequestTag/* patterns."""
        assert conditions.is_valid_global_key("aws:RequestTag/Environment") is True
        assert conditions.is_valid_global_key("aws:RequestTag/Owner") is True
        assert conditions.is_valid_global_key("aws:RequestTag/CostCenter") is True
        assert conditions.is_valid_global_key("aws:RequestTag/Team-Name") is True
        assert conditions.is_valid_global_key("aws:RequestTag/app.example.com/role") is True

    def test_resource_tag_pattern(self, conditions):
        """Test validation of aws:ResourceTag/* patterns."""
        assert conditions.is_valid_global_key("aws:ResourceTag/Environment") is True
        assert conditions.is_valid_global_key("aws:ResourceTag/Owner") is True
        assert conditions.is_valid_global_key("aws:ResourceTag/Project") is True
        assert conditions.is_valid_global_key("aws:ResourceTag/app:component") is True

    def test_principal_tag_pattern(self, conditions):
        """Test validation of aws:PrincipalTag/* patterns."""
        assert conditions.is_valid_global_key("aws:PrincipalTag/Department") is True
        assert conditions.is_valid_global_key("aws:PrincipalTag/Role") is True
        assert conditions.is_valid_global_key("aws:PrincipalTag/Access-Level") is True

    def test_invalid_tag_patterns(self, conditions):
        """Test that invalid tag patterns are rejected."""
        # Missing tag name
        assert conditions.is_valid_global_key("aws:RequestTag/") is False
        assert conditions.is_valid_global_key("aws:ResourceTag/") is False
        assert conditions.is_valid_global_key("aws:PrincipalTag/") is False

        # Wrong prefix
        assert conditions.is_valid_global_key("s3:RequestTag/Environment") is False
        assert conditions.is_valid_global_key("ec2:ResourceTag/Name") is False

    def test_get_all_keys(self, conditions):
        """Test getting all explicit global condition keys."""
        keys = conditions.get_all_keys()
        assert isinstance(keys, set)
        assert len(keys) > 0
        assert "aws:SourceIp" in keys
        assert "aws:PrincipalArn" in keys
        # Ensure it's a copy, not the original
        keys.add("test:key")
        assert "test:key" not in conditions._global_keys

    def test_get_patterns(self, conditions):
        """Test getting all condition key patterns."""
        patterns = conditions.get_patterns()
        assert isinstance(patterns, list)
        assert len(patterns) == 3  # RequestTag, ResourceTag, PrincipalTag

        # Verify pattern structure
        for pattern_config in patterns:
            assert "pattern" in pattern_config
            assert "description" in pattern_config

        # Ensure it's a copy, not the original
        patterns.append({"pattern": "test", "description": "test"})
        assert len(conditions._patterns) == 3

    def test_singleton_get_global_conditions(self):
        """Test the singleton factory function."""
        instance1 = get_global_conditions()
        instance2 = get_global_conditions()

        # Should return the same instance
        assert instance1 is instance2
        assert isinstance(instance1, AWSGlobalConditions)

    def test_all_predefined_keys_are_valid(self, conditions):
        """Test that all predefined keys in AWS_GLOBAL_CONDITION_KEYS are valid."""
        for key in AWS_GLOBAL_CONDITION_KEYS:
            assert conditions.is_valid_global_key(key) is True, f"{key} should be valid"

    def test_case_sensitivity(self, conditions):
        """Test that condition keys are case-sensitive."""
        # Valid key
        assert conditions.is_valid_global_key("aws:SourceIp") is True

        # Invalid cases (wrong capitalization)
        assert conditions.is_valid_global_key("aws:sourceip") is False
        assert conditions.is_valid_global_key("AWS:SourceIp") is False
        assert conditions.is_valid_global_key("aws:SOURCEIP") is False

    def test_tag_with_special_characters(self, conditions):
        """Test tag patterns with allowed special characters."""
        # According to the pattern: [a-zA-Z0-9+\-=._:/@]+
        assert conditions.is_valid_global_key("aws:RequestTag/my-tag") is True
        assert conditions.is_valid_global_key("aws:RequestTag/my_tag") is True
        assert conditions.is_valid_global_key("aws:RequestTag/my.tag") is True
        assert conditions.is_valid_global_key("aws:RequestTag/my:tag") is True
        assert conditions.is_valid_global_key("aws:RequestTag/my/tag") is True
        assert conditions.is_valid_global_key("aws:RequestTag/my@tag") is True
        assert conditions.is_valid_global_key("aws:RequestTag/my+tag") is True
        assert conditions.is_valid_global_key("aws:RequestTag/my=tag") is True

    def test_known_service_specific_keys_are_invalid(self, conditions):
        """Test that service-specific condition keys are not treated as global."""
        # S3-specific keys
        assert conditions.is_valid_global_key("s3:x-amz-acl") is False
        assert conditions.is_valid_global_key("s3:prefix") is False

        # EC2-specific keys
        assert conditions.is_valid_global_key("ec2:InstanceType") is False
        assert conditions.is_valid_global_key("ec2:Region") is False

        # IAM-specific keys
        assert conditions.is_valid_global_key("iam:PassedToService") is False
