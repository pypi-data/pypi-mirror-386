"""IAM Policy Loader Module.

This module provides functionality to load and parse IAM policy documents
from various file formats (JSON, YAML) and directories.

The loader supports both eager loading (load all at once) and streaming
(process one file at a time) to optimize memory usage.

Example usage:
    loader = PolicyLoader()

    # Eager loading (loads all files into memory)
    policy = loader.load_from_file("policy.json")
    policies = loader.load_from_directory("./policies/", recursive=True)
    policies = loader.load_from_path("./policies/", recursive=False)

    # Streaming (memory-efficient, processes one file at a time)
    for file_path, policy in loader.stream_from_path("./policies/"):
        # Process each policy immediately
        validate_and_report(file_path, policy)

    # Batch processing (configurable batch size)
    for batch in loader.batch_from_paths(["./policies/"], batch_size=10):
        # Process batch of up to 10 policies
        validate_batch(batch)
"""

import json
import logging
from collections.abc import Generator
from pathlib import Path

import yaml

from iam_validator.core.models import IAMPolicy

logger = logging.getLogger(__name__)


class PolicyLoader:
    """Loads and parses IAM policy documents from files.

    Supports both eager loading and streaming for memory efficiency.
    """

    SUPPORTED_EXTENSIONS = {".json", ".yaml", ".yml"}

    def __init__(self, max_file_size_mb: int = 100) -> None:
        """Initialize the policy loader.

        Args:
            max_file_size_mb: Maximum file size in MB to load (default: 100MB)
        """
        self.loaded_policies: list[tuple[str, IAMPolicy]] = []
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024

    @staticmethod
    def _find_statement_line_numbers(file_content: str) -> list[int]:
        """Find line numbers for each statement in a JSON policy file.

        Args:
            file_content: Raw content of the policy file

        Returns:
            List of line numbers (1-indexed) for each statement's Sid or opening brace
        """
        lines = file_content.split("\n")
        statement_lines = []
        in_statement_array = False
        brace_depth = 0
        statement_start_line = None
        current_statement_first_field = None

        for line_num, line in enumerate(lines, start=1):
            # Look for "Statement" array
            if '"Statement"' in line or "'Statement'" in line:
                in_statement_array = True
                continue

            if not in_statement_array:
                continue

            # Track opening braces for statement objects
            for char in line:
                if char == "{":
                    if brace_depth == 0 and statement_start_line is None:
                        # Found the start of a statement object
                        statement_start_line = line_num
                        current_statement_first_field = None
                    brace_depth += 1
                elif char == "}":
                    brace_depth -= 1
                    if brace_depth == 0 and statement_start_line is not None:
                        # Completed a statement object
                        # Use first field line if found, otherwise use opening brace
                        statement_lines.append(
                            current_statement_first_field or statement_start_line
                        )
                        statement_start_line = None
                        current_statement_first_field = None
                elif char == "]" and brace_depth == 0:
                    # End of Statement array
                    in_statement_array = False
                    break

            # Track first field in statement (usually Sid, Effect, or Action)
            if (
                in_statement_array
                and brace_depth == 1
                and current_statement_first_field is None
                and statement_start_line is not None
            ):
                stripped = line.strip()
                # Look for first JSON field (e.g., "Sid":, "Effect":, "Action":)
                if (
                    stripped
                    and stripped[0] == '"'
                    and ":" in stripped
                    and not stripped.startswith('"{')
                ):
                    current_statement_first_field = line_num

        return statement_lines

    def _check_file_size(self, path: Path) -> bool:
        """Check if file size is within limits.

        Args:
            path: Path to the file

        Returns:
            True if file size is acceptable, False otherwise
        """
        try:
            file_size = path.stat().st_size
            if file_size > self.max_file_size_bytes:
                logger.warning(
                    f"File {path} exceeds maximum size "
                    f"({file_size / 1024 / 1024:.2f}MB > "
                    f"{self.max_file_size_bytes / 1024 / 1024:.2f}MB). Skipping."
                )
                return False
            return True
        except OSError as e:
            logger.error(f"Failed to check file size for {path}: {e}")
            return False

    def load_from_file(self, file_path: str) -> IAMPolicy | None:
        """Load a single IAM policy from a file.

        Args:
            file_path: Path to the policy file

        Returns:
            Parsed IAMPolicy or None if loading fails
        """
        path = Path(file_path)

        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return None

        if not path.is_file():
            logger.error(f"Not a file: {file_path}")
            return None

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            logger.warning(
                f"Unsupported file extension: {path.suffix}. "
                f"Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )
            return None

        # Check file size before loading
        if not self._check_file_size(path):
            return None

        try:
            with open(path, encoding="utf-8") as f:
                file_content = f.read()

            # Parse line numbers for JSON files
            statement_line_numbers = []
            if path.suffix.lower() == ".json":
                statement_line_numbers = self._find_statement_line_numbers(file_content)
                data = json.loads(file_content)
            else:  # .yaml or .yml
                data = yaml.safe_load(file_content)
                # TODO: Add YAML line number tracking if needed

            # Validate and parse the policy
            policy = IAMPolicy.model_validate(data)

            # Attach line numbers to statements
            if statement_line_numbers:
                for idx, statement in enumerate(policy.statement):
                    if idx < len(statement_line_numbers):
                        statement.line_number = statement_line_numbers[idx]

            logger.info(f"Successfully loaded policy from {file_path}")
            return policy

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return None
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load policy from {file_path}: {e}")
            return None

    def load_from_directory(
        self, directory_path: str, recursive: bool = True
    ) -> list[tuple[str, IAMPolicy]]:
        """Load all IAM policies from a directory.

        Args:
            directory_path: Path to the directory
            recursive: Whether to search subdirectories

        Returns:
            List of tuples (file_path, policy)
        """
        path = Path(directory_path)

        if not path.exists():
            logger.error(f"Directory not found: {directory_path}")
            return []

        if not path.is_dir():
            logger.error(f"Not a directory: {directory_path}")
            return []

        policies: list[tuple[str, IAMPolicy]] = []
        pattern = "**/*" if recursive else "*"

        for file_path in path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                policy = self.load_from_file(str(file_path))
                if policy:
                    policies.append((str(file_path), policy))

        logger.info(f"Loaded {len(policies)} policies from {directory_path}")
        return policies

    def load_from_path(self, path: str, recursive: bool = True) -> list[tuple[str, IAMPolicy]]:
        """Load IAM policies from a file or directory.

        Args:
            path: Path to file or directory
            recursive: Whether to search subdirectories (only applies to directories)

        Returns:
            List of tuples (file_path, policy)
        """
        path_obj = Path(path)

        if path_obj.is_file():
            policy = self.load_from_file(path)
            return [(path, policy)] if policy else []
        elif path_obj.is_dir():
            return self.load_from_directory(path, recursive)
        else:
            logger.error(f"Path not found: {path}")
            return []

    def load_from_paths(
        self, paths: list[str], recursive: bool = True
    ) -> list[tuple[str, IAMPolicy]]:
        """Load IAM policies from multiple files or directories.

        Args:
            paths: List of paths to files or directories
            recursive: Whether to search subdirectories (only applies to directories)

        Returns:
            List of tuples (file_path, policy) from all paths combined
        """
        all_policies: list[tuple[str, IAMPolicy]] = []

        for path in paths:
            policies = self.load_from_path(path.strip(), recursive)
            all_policies.extend(policies)

        logger.info(f"Loaded {len(all_policies)} total policies from {len(paths)} path(s)")
        return all_policies

    def _get_policy_files(self, path: str, recursive: bool = True) -> Generator[Path, None, None]:
        """Get all policy files from a path (file or directory).

        This is a generator that yields file paths without loading them,
        enabling memory-efficient iteration.

        Args:
            path: Path to file or directory
            recursive: Whether to search subdirectories

        Yields:
            Path objects for policy files
        """
        path_obj = Path(path)

        if path_obj.is_file():
            if path_obj.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                yield path_obj
        elif path_obj.is_dir():
            pattern = "**/*" if recursive else "*"
            for file_path in path_obj.glob(pattern):
                if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    yield file_path
        else:
            logger.error(f"Path not found: {path}")

    def stream_from_path(
        self, path: str, recursive: bool = True
    ) -> Generator[tuple[str, IAMPolicy], None, None]:
        """Stream IAM policies from a file or directory one at a time.

        This is a memory-efficient alternative to load_from_path that yields
        policies one at a time instead of loading all into memory.

        Args:
            path: Path to file or directory
            recursive: Whether to search subdirectories

        Yields:
            Tuples of (file_path, policy) for each successfully loaded policy
        """
        for file_path in self._get_policy_files(path, recursive):
            policy = self.load_from_file(str(file_path))
            if policy:
                yield (str(file_path), policy)

    def stream_from_paths(
        self, paths: list[str], recursive: bool = True
    ) -> Generator[tuple[str, IAMPolicy], None, None]:
        """Stream IAM policies from multiple paths one at a time.

        This is a memory-efficient alternative to load_from_paths that yields
        policies one at a time instead of loading all into memory.

        Args:
            paths: List of paths to files or directories
            recursive: Whether to search subdirectories

        Yields:
            Tuples of (file_path, policy) for each successfully loaded policy
        """
        for path in paths:
            yield from self.stream_from_path(path.strip(), recursive)

    def batch_from_paths(
        self, paths: list[str], batch_size: int = 10, recursive: bool = True
    ) -> Generator[list[tuple[str, IAMPolicy]], None, None]:
        """Load policies in batches for balanced memory usage and performance.

        Args:
            paths: List of paths to files or directories
            batch_size: Number of policies per batch (default: 10)
            recursive: Whether to search subdirectories

        Yields:
            Lists of (file_path, policy) tuples, up to batch_size per list
        """
        batch: list[tuple[str, IAMPolicy]] = []

        for file_path, policy in self.stream_from_paths(paths, recursive):
            batch.append((file_path, policy))

            if len(batch) >= batch_size:
                yield batch
                batch = []

        # Yield remaining policies
        if batch:
            yield batch

    @staticmethod
    def parse_policy_string(policy_json: str) -> IAMPolicy | None:
        """Parse an IAM policy from a JSON string.

        Args:
            policy_json: JSON string containing the policy

        Returns:
            Parsed IAMPolicy or None if parsing fails
        """
        try:
            data = json.loads(policy_json)
            policy = IAMPolicy.model_validate(data)
            logger.info("Successfully parsed policy from string")
            return policy
        except Exception as e:
            logger.error(f"Failed to parse policy string: {e}")
            return None
