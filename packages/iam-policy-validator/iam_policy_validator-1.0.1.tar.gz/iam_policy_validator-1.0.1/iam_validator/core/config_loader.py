"""
Configuration loader for IAM Policy Validator.

Loads and parses configuration from YAML files, environment variables,
and command-line arguments.
"""

import importlib.util
import inspect
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

from iam_validator.core.check_registry import CheckConfig, CheckRegistry, PolicyCheck

logger = logging.getLogger(__name__)


class ValidatorConfig:
    """Main configuration object for the validator."""

    def __init__(self, config_dict: dict[str, Any] | None = None):
        """
        Initialize configuration from a dictionary.

        Args:
            config_dict: Dictionary loaded from YAML config file
        """
        self.config_dict = config_dict or {}
        self.checks_config = self.config_dict.get("checks", {})
        self.custom_checks = self.config_dict.get("custom_checks", [])
        self.custom_checks_dir = self.config_dict.get("custom_checks_dir")
        self.settings = self.config_dict.get("settings", {})

    def get_check_config(self, check_id: str) -> dict[str, Any]:
        """Get configuration for a specific check."""
        return self.checks_config.get(check_id, {})

    def is_check_enabled(self, check_id: str) -> bool:
        """Check if a specific check is enabled."""
        check_config = self.get_check_config(check_id)
        return check_config.get("enabled", True)

    def get_check_severity(self, check_id: str) -> str | None:
        """Get severity override for a check."""
        check_config = self.get_check_config(check_id)
        return check_config.get("severity")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a global setting value."""
        return self.settings.get(key, default)


class ConfigLoader:
    """Loads configuration from various sources."""

    DEFAULT_CONFIG_NAMES = [
        "iam-validator.yaml",
        "iam-validator.yml",
        ".iam-validator.yaml",  # Support hidden files as fallback
        ".iam-validator.yml",
    ]

    @staticmethod
    def find_config_file(
        explicit_path: str | None = None, search_path: Path | None = None
    ) -> Path | None:
        """
        Find configuration file.

        Search order:
        1. Explicit path if provided
        2. Current directory
        3. Parent directories (walk up to root)
        4. User home directory

        Args:
            explicit_path: Explicit config file path
            search_path: Starting directory for search (defaults to cwd)

        Returns:
            Path to config file or None if not found
        """
        # Check explicit path first
        if explicit_path:
            path = Path(explicit_path)
            if path.exists() and path.is_file():
                return path
            raise FileNotFoundError(f"Config file not found: {explicit_path}")

        # Start from search path or current directory
        current = search_path or Path.cwd()

        # Search current and parent directories
        while True:
            for config_name in ConfigLoader.DEFAULT_CONFIG_NAMES:
                config_path = current / config_name
                if config_path.exists() and config_path.is_file():
                    return config_path

            # Stop at filesystem root
            parent = current.parent
            if parent == current:
                break
            current = parent

        # Check home directory
        home = Path.home()
        for config_name in ConfigLoader.DEFAULT_CONFIG_NAMES:
            config_path = home / config_name
            if config_path.exists() and config_path.is_file():
                return config_path

        return None

    @staticmethod
    def load_yaml(file_path: Path) -> dict[str, Any]:
        """
        Load YAML configuration file.

        Args:
            file_path: Path to YAML file

        Returns:
            Parsed configuration dictionary
        """
        try:
            with open(file_path) as f:
                config = yaml.safe_load(f)
                return config or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error reading config file {file_path}: {e}")

    @staticmethod
    def load_config(
        explicit_path: str | None = None,
        search_path: Path | None = None,
        allow_missing: bool = True,
    ) -> ValidatorConfig:
        """
        Load configuration from file.

        Args:
            explicit_path: Explicit path to config file
            search_path: Starting directory for config search
            allow_missing: If True, return default config when file not found

        Returns:
            ValidatorConfig object

        Raises:
            FileNotFoundError: If config not found and allow_missing=False
        """
        config_file = ConfigLoader.find_config_file(explicit_path, search_path)

        if not config_file:
            if allow_missing:
                return ValidatorConfig()  # Return default config
            raise FileNotFoundError(
                f"No configuration file found. Searched for: {', '.join(ConfigLoader.DEFAULT_CONFIG_NAMES)}"
            )

        config_dict = ConfigLoader.load_yaml(config_file)
        return ValidatorConfig(config_dict)

    @staticmethod
    def apply_config_to_registry(config: ValidatorConfig, registry: CheckRegistry) -> None:
        """
        Apply configuration to a check registry.

        This configures all registered checks based on the loaded configuration.

        Args:
            config: Loaded configuration
            registry: Check registry to configure
        """
        # Configure built-in checks
        for check in registry.get_all_checks():
            check_id = check.check_id
            check_config_dict = config.get_check_config(check_id)

            # Get existing config to preserve defaults set during registration
            existing_config = registry.get_config(check_id)
            existing_enabled = existing_config.enabled if existing_config else True

            # Create CheckConfig object
            # If there's explicit config, use it; otherwise preserve existing enabled state
            check_config = CheckConfig(
                check_id=check_id,
                enabled=check_config_dict.get("enabled", existing_enabled),
                severity=check_config_dict.get("severity"),
                config=check_config_dict,
                description=check_config_dict.get("description", check.description),
            )

            registry.configure_check(check_id, check_config)

    @staticmethod
    def load_custom_checks(config: ValidatorConfig, registry: CheckRegistry) -> list[str]:
        """
        Load custom checks from Python modules.

        Args:
            config: Loaded configuration
            registry: Check registry to add custom checks to

        Returns:
            List of loaded check IDs

        Note:
            Custom check modules should export a class that inherits from PolicyCheck.
            The module path should be importable (e.g., "my_package.my_check.MyCheck").
        """
        loaded_checks = []

        # Handle None or missing custom_checks
        if not config.custom_checks:
            return loaded_checks

        for custom_check_config in config.custom_checks:
            if not custom_check_config.get("enabled", True):
                continue

            module_path = custom_check_config.get("module")
            if not module_path:
                continue

            try:
                # Dynamic import of custom check class
                # Format: "package.module.ClassName"
                parts = module_path.rsplit(".", 1)
                if len(parts) != 2:
                    raise ValueError(
                        f"Invalid module path: {module_path}. "
                        "Expected format: 'package.module.ClassName'"
                    )

                module_name, class_name = parts

                # Import the module
                import importlib

                module = importlib.import_module(module_name)
                check_class = getattr(module, class_name)

                # Instantiate and register the check
                check_instance = check_class()
                registry.register(check_instance)

                # Configure the check
                check_config = CheckConfig(
                    check_id=check_instance.check_id,
                    enabled=True,
                    severity=custom_check_config.get("severity"),
                    config=custom_check_config.get("config", {}),
                    description=custom_check_config.get("description", check_instance.description),
                )
                registry.configure_check(check_instance.check_id, check_config)

                loaded_checks.append(check_instance.check_id)

            except Exception as e:
                # Log error but continue loading other checks
                print(f"Warning: Failed to load custom check '{module_path}': {e}")

        return loaded_checks

    @staticmethod
    def discover_checks_in_directory(directory: Path, registry: CheckRegistry) -> list[str]:
        """
        Auto-discover and load custom checks from a directory.

        This method scans a directory for Python files, imports them,
        and automatically registers any PolicyCheck subclasses found.

        Args:
            directory: Path to directory containing custom check modules
            registry: Check registry to add discovered checks to

        Returns:
            List of loaded check IDs

        Note:
            - All .py files in the directory will be scanned (non-recursive)
            - Files starting with '_' or '.' are skipped
            - Each file can contain multiple PolicyCheck subclasses
            - Classes must inherit from PolicyCheck and implement required methods
        """
        loaded_checks = []

        if not directory.exists():
            logger.warning(f"Custom checks directory does not exist: {directory}")
            return loaded_checks

        if not directory.is_dir():
            logger.warning(f"Custom checks path is not a directory: {directory}")
            return loaded_checks

        logger.info(f"Scanning for custom checks in: {directory}")

        # Get all Python files in the directory
        python_files = [
            f
            for f in directory.iterdir()
            if f.is_file()
            and f.suffix == ".py"
            and not f.name.startswith("_")
            and not f.name.startswith(".")
        ]

        for py_file in python_files:
            try:
                # Load module from file
                module_name = f"custom_checks_{py_file.stem}"
                spec = importlib.util.spec_from_file_location(module_name, py_file)

                if spec is None or spec.loader is None:
                    logger.warning(f"Could not load spec from {py_file}")
                    continue

                module = importlib.util.module_from_spec(spec)

                # Add to sys.modules to support relative imports
                sys.modules[module_name] = module

                # Execute the module
                spec.loader.exec_module(module)

                # Find all PolicyCheck subclasses in the module
                for name, obj in inspect.getmembers(module):
                    # Skip imported classes and non-classes
                    if not inspect.isclass(obj):
                        continue

                    # Skip the base PolicyCheck class itself
                    if obj is PolicyCheck:
                        continue

                    # Check if it's a PolicyCheck subclass
                    if issubclass(obj, PolicyCheck) and obj.__module__ == module_name:
                        try:
                            # Instantiate and register the check
                            check_instance = obj()

                            # Verify the check has required properties
                            if not hasattr(check_instance, "check_id"):
                                logger.warning(
                                    f"Check class {name} in {py_file} missing check_id property"
                                )
                                continue

                            registry.register(check_instance)

                            # Create default config (disabled by default - must be explicitly enabled in config)
                            check_config = CheckConfig(
                                check_id=check_instance.check_id,
                                enabled=False,
                                description=check_instance.description,
                            )
                            registry.configure_check(check_instance.check_id, check_config)

                            loaded_checks.append(check_instance.check_id)
                            logger.info(
                                f"Loaded custom check '{check_instance.check_id}' from {py_file.name}"
                            )

                        except Exception as e:
                            logger.warning(
                                f"Failed to instantiate check {name} from {py_file}: {e}"
                            )

            except Exception as e:
                logger.warning(f"Failed to load custom check module {py_file}: {e}")

        if loaded_checks:
            logger.info(
                f"Auto-discovered {len(loaded_checks)} custom checks: {', '.join(loaded_checks)}"
            )

        return loaded_checks


def load_validator_config(
    config_path: str | None = None, allow_missing: bool = True
) -> ValidatorConfig:
    """
    Convenience function to load validator configuration.

    Args:
        config_path: Optional explicit path to config file
        allow_missing: If True, return default config when file not found

    Returns:
        ValidatorConfig object
    """
    return ConfigLoader.load_config(explicit_path=config_path, allow_missing=allow_missing)
