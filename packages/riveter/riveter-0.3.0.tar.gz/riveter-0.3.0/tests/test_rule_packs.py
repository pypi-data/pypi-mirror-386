"""Tests for rule pack management system."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from riveter.rule_packs import RulePack, RulePackManager, RulePackMetadata
from riveter.rules import Rule, Severity


class TestRulePackMetadata:
    """Test RulePackMetadata class."""

    def test_metadata_creation(self) -> None:
        """Test creating rule pack metadata."""
        metadata = RulePackMetadata(
            name="test-pack",
            version="1.0.0",
            description="Test pack",
            author="Test Author",
            created="2024-01-01",
            updated="2024-01-01",
            dependencies=[],
            tags=["test"],
            min_riveter_version="0.1.0",
        )

        assert metadata.name == "test-pack"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Test pack"
        assert metadata.author == "Test Author"
        assert metadata.dependencies == []
        assert metadata.tags == ["test"]


class TestRulePack:
    """Test RulePack class."""

    def test_rule_pack_creation(self) -> None:
        """Test creating a rule pack."""
        metadata = RulePackMetadata(
            name="test-pack",
            version="1.0.0",
            description="Test pack",
            author="Test Author",
            created="2024-01-01",
            updated="2024-01-01",
            dependencies=[],
            tags=["test"],
            min_riveter_version="0.1.0",
        )

        rule_dict = {
            "id": "test_rule",
            "resource_type": "aws_instance",
            "description": "Test rule",
            "severity": "error",
            "assert": {"instance_type": "t3.large"},
        }
        rule = Rule(rule_dict)

        pack = RulePack(metadata=metadata, rules=[rule])

        assert pack.metadata.name == "test-pack"
        assert len(pack.rules) == 1
        assert pack.rules[0].id == "test_rule"

    def test_rule_pack_duplicate_rule_ids(self) -> None:
        """Test that rule pack validation catches duplicate rule IDs."""
        metadata = RulePackMetadata(
            name="test-pack",
            version="1.0.0",
            description="Test pack",
            author="Test Author",
            created="2024-01-01",
            updated="2024-01-01",
            dependencies=[],
            tags=["test"],
            min_riveter_version="0.1.0",
        )

        rule1_dict = {
            "id": "duplicate_rule",
            "resource_type": "aws_instance",
            "description": "First rule",
            "severity": "error",
            "assert": {"instance_type": "t3.large"},
        }
        rule2_dict = {
            "id": "duplicate_rule",
            "resource_type": "aws_s3_bucket",
            "description": "Second rule",
            "severity": "warning",
            "assert": {"versioning.enabled": True},
        }

        rule1 = Rule(rule1_dict)
        rule2 = Rule(rule2_dict)

        with pytest.raises(ValueError, match="Duplicate rule ID"):
            RulePack(metadata=metadata, rules=[rule1, rule2])

    def test_filter_by_severity(self) -> None:
        """Test filtering rules by severity."""
        metadata = RulePackMetadata(
            name="test-pack",
            version="1.0.0",
            description="Test pack",
            author="Test Author",
            created="2024-01-01",
            updated="2024-01-01",
            dependencies=[],
            tags=["test"],
            min_riveter_version="0.1.0",
        )

        error_rule = Rule(
            {
                "id": "error_rule",
                "resource_type": "aws_instance",
                "description": "Error rule",
                "severity": "error",
                "assert": {"instance_type": "t3.large"},
            }
        )

        warning_rule = Rule(
            {
                "id": "warning_rule",
                "resource_type": "aws_s3_bucket",
                "description": "Warning rule",
                "severity": "warning",
                "assert": {"versioning.enabled": True},
            }
        )

        info_rule = Rule(
            {
                "id": "info_rule",
                "resource_type": "aws_vpc",
                "description": "Info rule",
                "severity": "info",
                "assert": {"enable_dns_hostnames": True},
            }
        )

        pack = RulePack(metadata=metadata, rules=[error_rule, warning_rule, info_rule])

        # Filter by error severity (should include only error rules)
        error_pack = pack.filter_by_severity(Severity.ERROR)
        assert len(error_pack.rules) == 1
        assert error_pack.rules[0].id == "error_rule"

        # Filter by warning severity (should include warning and error rules)
        warning_pack = pack.filter_by_severity(Severity.WARNING)
        assert len(warning_pack.rules) == 2
        rule_ids = {rule.id for rule in warning_pack.rules}
        assert rule_ids == {"error_rule", "warning_rule"}

        # Filter by info severity (should include all rules)
        info_pack = pack.filter_by_severity(Severity.INFO)
        assert len(info_pack.rules) == 3

    def test_filter_by_resource_type(self) -> None:
        """Test filtering rules by resource type."""
        metadata = RulePackMetadata(
            name="test-pack",
            version="1.0.0",
            description="Test pack",
            author="Test Author",
            created="2024-01-01",
            updated="2024-01-01",
            dependencies=[],
            tags=["test"],
            min_riveter_version="0.1.0",
        )

        ec2_rule = Rule(
            {
                "id": "ec2_rule",
                "resource_type": "aws_instance",
                "description": "EC2 rule",
                "severity": "error",
                "assert": {"instance_type": "t3.large"},
            }
        )

        s3_rule = Rule(
            {
                "id": "s3_rule",
                "resource_type": "aws_s3_bucket",
                "description": "S3 rule",
                "severity": "warning",
                "assert": {"versioning.enabled": True},
            }
        )

        pack = RulePack(metadata=metadata, rules=[ec2_rule, s3_rule])

        # Filter by EC2 resource type
        ec2_pack = pack.filter_by_resource_type(["aws_instance"])
        assert len(ec2_pack.rules) == 1
        assert ec2_pack.rules[0].id == "ec2_rule"

        # Filter by multiple resource types
        multi_pack = pack.filter_by_resource_type(["aws_instance", "aws_s3_bucket"])
        assert len(multi_pack.rules) == 2

    def test_merge_rule_packs(self) -> None:
        """Test merging two rule packs."""
        metadata1 = RulePackMetadata(
            name="pack1",
            version="1.0.0",
            description="First pack",
            author="Author 1",
            created="2024-01-01",
            updated="2024-01-01",
            dependencies=[],
            tags=["test1"],
            min_riveter_version="0.1.0",
        )

        metadata2 = RulePackMetadata(
            name="pack2",
            version="2.0.0",
            description="Second pack",
            author="Author 2",
            created="2024-02-01",
            updated="2024-02-01",
            dependencies=["pack1"],
            tags=["test2"],
            min_riveter_version="0.2.0",
        )

        rule1 = Rule(
            {
                "id": "rule1",
                "resource_type": "aws_instance",
                "description": "Rule 1",
                "severity": "error",
                "assert": {"instance_type": "t3.large"},
            }
        )

        rule2 = Rule(
            {
                "id": "rule2",
                "resource_type": "aws_s3_bucket",
                "description": "Rule 2",
                "severity": "warning",
                "assert": {"versioning.enabled": True},
            }
        )

        pack1 = RulePack(metadata=metadata1, rules=[rule1])
        pack2 = RulePack(metadata=metadata2, rules=[rule2])

        merged_pack = pack1.merge_with(pack2)

        assert len(merged_pack.rules) == 2
        assert merged_pack.metadata.name == "pack1+pack2"
        assert merged_pack.metadata.version == "merged"
        assert "Author 1" in merged_pack.metadata.author
        assert "Author 2" in merged_pack.metadata.author
        assert set(merged_pack.metadata.tags) == {"test1", "test2"}
        assert merged_pack.metadata.min_riveter_version == "0.2.0"

    def test_merge_conflicting_rule_ids(self) -> None:
        """Test that merging packs with conflicting rule IDs raises an error."""
        metadata1 = RulePackMetadata(
            name="pack1",
            version="1.0.0",
            description="First pack",
            author="Author 1",
            created="2024-01-01",
            updated="2024-01-01",
            dependencies=[],
            tags=["test1"],
            min_riveter_version="0.1.0",
        )

        metadata2 = RulePackMetadata(
            name="pack2",
            version="2.0.0",
            description="Second pack",
            author="Author 2",
            created="2024-02-01",
            updated="2024-02-01",
            dependencies=[],
            tags=["test2"],
            min_riveter_version="0.1.0",
        )

        rule1 = Rule(
            {
                "id": "conflicting_rule",
                "resource_type": "aws_instance",
                "description": "Rule 1",
                "severity": "error",
                "assert": {"instance_type": "t3.large"},
            }
        )

        rule2 = Rule(
            {
                "id": "conflicting_rule",
                "resource_type": "aws_s3_bucket",
                "description": "Rule 2",
                "severity": "warning",
                "assert": {"versioning.enabled": True},
            }
        )

        pack1 = RulePack(metadata=metadata1, rules=[rule1])
        pack2 = RulePack(metadata=metadata2, rules=[rule2])

        with pytest.raises(ValueError, match="conflicting rule IDs"):
            pack1.merge_with(pack2)

    def test_to_dict(self) -> None:
        """Test converting rule pack to dictionary."""
        metadata = RulePackMetadata(
            name="test-pack",
            version="1.0.0",
            description="Test pack",
            author="Test Author",
            created="2024-01-01",
            updated="2024-01-01",
            dependencies=[],
            tags=["test"],
            min_riveter_version="0.1.0",
        )

        rule = Rule(
            {
                "id": "test_rule",
                "resource_type": "aws_instance",
                "description": "Test rule",
                "severity": "error",
                "assert": {"instance_type": "t3.large"},
                "metadata": {"tags": ["test"]},
            }
        )

        pack = RulePack(metadata=metadata, rules=[rule])
        pack_dict = pack.to_dict()

        assert pack_dict["metadata"]["name"] == "test-pack"
        assert pack_dict["metadata"]["version"] == "1.0.0"
        assert len(pack_dict["rules"]) == 1
        assert pack_dict["rules"][0]["id"] == "test_rule"
        assert pack_dict["rules"][0]["resource_type"] == "aws_instance"


class TestRulePackManager:
    """Test RulePackManager class."""

    def test_manager_initialization(self) -> None:
        """Test rule pack manager initialization."""
        manager = RulePackManager()
        assert isinstance(manager.rule_pack_dirs, list)

    def test_manager_with_custom_dirs(self) -> None:
        """Test rule pack manager with custom directories."""
        custom_dirs = ["/custom/path1", "/custom/path2"]
        manager = RulePackManager(rule_pack_dirs=custom_dirs)

        # Custom dirs should be included
        for custom_dir in custom_dirs:
            assert custom_dir in manager.rule_pack_dirs

    def test_load_rule_pack_from_file(self, fixtures_dir: Path) -> None:
        """Test loading a rule pack from file."""
        manager = RulePackManager()
        pack_file = fixtures_dir / "rule_packs" / "test-pack.yml"

        pack = manager.load_rule_pack_from_file(str(pack_file))

        assert pack.metadata.name == "test-pack"
        assert pack.metadata.version == "1.0.0"
        assert len(pack.rules) == 2
        assert pack.rules[0].id == "test_rule_1"
        assert pack.rules[1].id == "test_rule_2"

    def test_load_invalid_rule_pack(self, fixtures_dir: Path) -> None:
        """Test loading an invalid rule pack."""
        manager = RulePackManager()
        pack_file = fixtures_dir / "rule_packs" / "invalid-pack.yml"

        with pytest.raises(ValueError, match="Missing required metadata field"):
            manager.load_rule_pack_from_file(str(pack_file))

    def test_load_rule_pack_with_duplicate_ids(self, fixtures_dir: Path) -> None:
        """Test loading a rule pack with duplicate rule IDs."""
        manager = RulePackManager()
        pack_file = fixtures_dir / "rule_packs" / "duplicate-rules.yml"

        with pytest.raises(ValueError, match="Duplicate rule ID"):
            manager.load_rule_pack_from_file(str(pack_file))

    def test_load_rule_pack_by_name(self, fixtures_dir: Path) -> None:
        """Test loading a rule pack by name."""
        # Create a temporary manager with the fixtures directory
        manager = RulePackManager(rule_pack_dirs=[str(fixtures_dir / "rule_packs")])

        pack = manager.load_rule_pack("test-pack")

        assert pack.metadata.name == "test-pack"
        assert len(pack.rules) == 2

    def test_load_nonexistent_rule_pack(self) -> None:
        """Test loading a nonexistent rule pack."""
        manager = RulePackManager(rule_pack_dirs=[])

        with pytest.raises(
            FileNotFoundError, match="Rule pack 'nonexistent' version 'latest' not found"
        ):
            manager.load_rule_pack("nonexistent")

    def test_list_available_packs(self, fixtures_dir: Path) -> None:
        """Test listing available rule packs."""
        manager = RulePackManager(rule_pack_dirs=[str(fixtures_dir / "rule_packs")])

        packs = manager.list_available_packs()

        # Should find at least the test packs
        pack_names = {pack["name"] for pack in packs}
        assert "test-pack" in pack_names
        assert "second-pack" in pack_names

        # Check that pack info is populated
        test_pack = next(pack for pack in packs if pack["name"] == "test-pack")
        assert test_pack["version"] == "1.0.0"
        assert test_pack["rule_count"] == 2
        assert test_pack["author"] == "Test Author"

    def test_validate_rule_pack_valid(self, fixtures_dir: Path) -> None:
        """Test validating a valid rule pack."""
        manager = RulePackManager()
        pack_file = str(fixtures_dir / "rule_packs" / "test-pack.yml")

        result = manager.validate_rule_pack(pack_file)

        assert result["valid"] is True
        assert result["rule_count"] == 2
        assert result["metadata"]["name"] == "test-pack"
        assert len(result["errors"]) == 0

    def test_validate_rule_pack_invalid(self, fixtures_dir: Path) -> None:
        """Test validating an invalid rule pack."""
        manager = RulePackManager()
        pack_file = str(fixtures_dir / "rule_packs" / "invalid-pack.yml")

        result = manager.validate_rule_pack(pack_file)

        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_nonexistent_file(self) -> None:
        """Test validating a nonexistent file."""
        manager = RulePackManager()

        result = manager.validate_rule_pack("/nonexistent/file.yml")

        assert result["valid"] is False
        assert "File does not exist" in result["errors"][0]

    def test_merge_rule_packs(self, fixtures_dir: Path) -> None:
        """Test merging multiple rule packs."""
        manager = RulePackManager(rule_pack_dirs=[str(fixtures_dir / "rule_packs")])

        merged_pack = manager.merge_rule_packs(["test-pack", "second-pack"])

        assert len(merged_pack.rules) == 4  # 2 from test-pack + 2 from second-pack
        assert merged_pack.metadata.name == "test-pack+second-pack"

        # Check that all rules are present
        rule_ids = {rule.id for rule in merged_pack.rules}
        expected_ids = {"test_rule_1", "test_rule_2", "second_pack_rule_1", "second_pack_rule_2"}
        assert rule_ids == expected_ids

    def test_merge_empty_pack_list(self) -> None:
        """Test merging with empty pack list."""
        manager = RulePackManager()

        with pytest.raises(ValueError, match="At least one rule pack name must be provided"):
            manager.merge_rule_packs([])

    def test_create_rule_pack_template(self) -> None:
        """Test creating a rule pack template."""
        manager = RulePackManager()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            template_file = f.name

        try:
            manager.create_rule_pack_template("my-pack", template_file)

            # Verify the template was created
            assert os.path.exists(template_file)

            # Verify the template content
            with open(template_file, "r") as f:
                template_data = yaml.safe_load(f)

            assert template_data["metadata"]["name"] == "my-pack"
            assert template_data["metadata"]["version"] == "1.0.0"
            assert len(template_data["rules"]) == 1
            assert template_data["rules"][0]["id"] == "my_pack_example_rule"

        finally:
            if os.path.exists(template_file):
                os.unlink(template_file)


@pytest.fixture
def fixtures_dir() -> Path:
    """Provide path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"
