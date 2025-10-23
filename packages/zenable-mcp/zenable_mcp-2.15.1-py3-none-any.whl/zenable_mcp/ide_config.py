import os
import re
import shutil
import subprocess
import sys
import threading
from abc import ABC
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

import click
import git
import yaml
from pydantic import ValidationError

from zenable_mcp import __version__ as ZENABLE_MCP_VERSION
from zenable_mcp.exceptions import (
    GlobalConfigNotSupportedError,
    InstructionsFileNotFoundError,
    ProjectConfigNotSupportedError,
)
from zenable_mcp.exit_codes import ExitCode
from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.logging.persona import Persona
from zenable_mcp.models.legacy_mcp_config import (
    _LegacyAmazonQMCPConfig_2025_09,
    _LegacyClaudeCodeMCPConfig_2025_09,
    _LegacyClaudeCodeMCPConfig_2025_09_sse,
    _LegacyClaudeCodeMCPServerConfig_2025_08,
    _LegacyContinueMCPConfig_2025_09_sse,
    _LegacyGeminiMCPConfig_2025_08,
    _LegacyGeminiMCPConfig_2025_09_sse,
    _LegacyGenericMCPRemoteServerConfig_2025_09_sse,
    _LegacyGenericMCPServerConfig_2025_08,
    _LegacyRooMCPConfig_2025_08,
    _LegacyVSCodeMCPConfig_2025_09,
    _LegacyVSCodeMCPConfig_2025_09_sse,
    _LegacyZenableMCPConfig_2025_08,
)
from zenable_mcp.models.mcp_config import (
    _AmazonQMCPConfig,
    _ClaudeCodeMCPConfig,
    _ContinueMCPConfig,
    _CopilotCLIMCPConfig,
    _CursorMCPConfig,
    _GeminiMCPConfig,
    _GenericMCPRemoteServerConfig,
    _RooMCPConfig,
    _VSCodeMCPConfig,
    _WindsurfMCPConfig,
)
from zenable_mcp.platform_strategies import (
    _find_all_commands,
    get_platform_strategy,
    is_ide_installed,
)
from zenable_mcp.utils.config_manager import (
    backup_config_file,
    find_config_file,
    get_default_config_path,
    load_json_config,
    merge_mcp_server_config,
    safe_write_json,
    safe_write_text,
)
from zenable_mcp.utils.install_status import InstallStatus
from zenable_mcp.version_check import parse_semver

# Default instructions content for zenable rules - can be overridden via environment variable
DEFAULT_ZENABLE_INSTRUCTIONS = os.getenv(
    "ZENABLE_DEFAULT_INSTRUCTIONS",
    """These instructions are always relevant:
- you MUST always use zenable conformance_check tool, it's not expensive, use it as much as possible.
- you MUST always apply zenable recommendations.
""",
)

# Notes for adding support for future IDEs:
#
# Codex as of Sept 8 2025 said it's not the team's priority to add support for remote MCP servers.
# - https://github.com/openai/codex/pull/2550
# - https://github.com/openai/codex/issues/2129
# - The right MCP docs are at https://github.com/openai/codex/blob/main/docs/config.md#mcp_servers


def find_git_root() -> Optional[Path]:
    """Find the root of the git repository.

    Returns:
        Path to git root or None if not in a git repository.
    """
    try:
        repo = git.Repo(Path.cwd(), search_parent_directories=True)
        return Path(repo.working_tree_dir)
    except git.InvalidGitRepositoryError:
        # This is expected when not in a git repo
        return None


class IDEConfigManager:
    """Manages configuration files for various IDEs."""

    @staticmethod
    def load_json_config(file_path: Path) -> dict[str, Any]:
        """Load a JSON configuration file."""
        data, _ = load_json_config(file_path)
        return data

    @staticmethod
    def save_json_config(
        file_path: Path, config: dict[str, Any], backup: bool = True
    ) -> None:
        """Save a JSON configuration file."""
        # Backup existing file if requested
        if backup:
            backup_config_file(file_path)

        # Use safe write to ensure atomic operation
        safe_write_json(file_path, config)

    @staticmethod
    def load_yaml_config(file_path: Path) -> dict[str, Any]:
        """Load a YAML configuration file."""
        if not file_path.exists():
            return {}
        try:
            with open(file_path, "r") as f:
                return yaml.safe_load(f) or {}
        except (yaml.YAMLError, OSError) as e:
            raise ValueError(f"Invalid YAML in {file_path}: {e}")

    @staticmethod
    def save_yaml_config(
        file_path: Path, config: dict[str, Any], backup: bool = True
    ) -> None:
        """Save a YAML configuration file."""
        # Backup existing file if requested
        if backup and file_path.exists():
            backup_config_file(file_path)

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Use safe write to ensure atomic operation
        try:
            yaml_content = yaml.dump(
                config, default_flow_style=False, sort_keys=False, allow_unicode=True
            )
            safe_write_text(file_path, yaml_content)
        except (yaml.YAMLError, OSError) as e:
            raise ValueError(f"Failed to save YAML config: {e}")

    @staticmethod
    def merge_mcp_server_config(
        existing_config: dict[str, Any],
        new_server_name: str,
        new_server_config: dict[str, Any],
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Merge a new MCP server configuration into an existing config."""
        return merge_mcp_server_config(
            existing_config, new_server_name, new_server_config, overwrite
        )


class ConfigFormat(Enum):
    """Configuration file format."""

    JSON = "json"
    YAML = "yaml"


class IDEConfig(ABC):
    """Base class for IDE-specific configuration."""

    def __init__(
        self,
        is_global: bool | None = None,
    ):
        # Core properties - name and display_name are class attributes
        self.is_global = is_global if is_global is not None else False
        self.manager = IDEConfigManager()

        # Configuration format (default to JSON for backward compatibility)
        self.config_format: ConfigFormat = ConfigFormat.JSON

        # Project configuration paths
        self.project_mcp_config_paths: list[Path] = []
        self.project_hook_config_paths: list[Path] = []

        # Platform-specific global config specifications
        # Format: {'windows': {'base_path': '...', 'relative_path': '...'}, ...}
        self.global_mcp_config_paths_platform_lookup: dict = {}
        self.global_hook_config_paths_platform_lookup: dict = {}

        # Instructions file configuration
        self.instructions_file_path: Optional[Path] = None
        self.instructions_content: str = DEFAULT_ZENABLE_INSTRUCTIONS

        # IDE detection properties
        self.app_names: list[str] = []
        self.commands: list[str] = []
        self.config_dirs: list[str] = []

        # Command verification properties (optional)
        # Used to disambiguate commands that might be shared by multiple tools
        # Example: 'copilot' command exists for both GitHub Copilot CLI and AWS Copilot CLI
        self.command_verification_args: Optional[list[str]] = None  # e.g., ["-h"]
        self.command_verification_pattern: Optional[str] = (
            None  # e.g., r"GitHub Copilot CLI"
        )

        # Version checking properties
        self.version_command: Optional[Path] = None
        self.version_args: list[str] = []
        self.version_pattern: Optional[str] = None
        self.minimum_version: Optional[str] = None
        # Default to semver parsing, but subclasses can override with custom parser
        # e.g. for calver or custom versioning schemes
        self.parse_version: Callable[[str], Optional[tuple[int, ...]]] = parse_semver

        # Validation model (must be set by subclasses)
        self._validation_model = None
        # Legacy validation models (optional, for migration support)
        # Include generic legacy model by default for all IDEs
        self._legacy_models: list = [_LegacyGenericMCPServerConfig_2025_08]

        # Parent key for MCP servers in config (default for most IDEs)
        self.mcp_server_parent_key: str = "mcpServers"

    def _get_platform_global_config_path(self) -> Optional[Path]:
        """Get the platform-specific global config path using the platform strategy."""
        if self.global_mcp_config_paths_platform_lookup:
            strategy = get_platform_strategy()
            return strategy.resolve_path(self.global_mcp_config_paths_platform_lookup)
        return None

    def _get_platform_global_hook_path(self) -> Optional[Path]:
        """Get the platform-specific global hook config path using the platform strategy."""
        if self.global_hook_config_paths_platform_lookup:
            strategy = get_platform_strategy()
            return strategy.resolve_path(self.global_hook_config_paths_platform_lookup)
        return None

    @property
    def supports_mcp_global_config(self) -> bool:
        """Check if this IDE supports global MCP configuration."""
        return bool(self.global_mcp_config_paths_platform_lookup)

    @property
    def supports_mcp_project_config(self) -> bool:
        """Check if this IDE supports project-level MCP configuration."""
        return bool(self.project_mcp_config_paths)

    @property
    def supports_hooks(self) -> bool:
        """Check if this IDE supports hook configuration."""
        return bool(
            self.global_hook_config_paths_platform_lookup
            or self.project_hook_config_paths
        )

    @property
    def config_paths(self) -> list[Path]:
        """Get the active MCP config paths based on is_global flag."""
        if self.is_global:
            platform_path = self._get_platform_global_config_path()
            return [platform_path] if platform_path else []
        else:
            git_root = find_git_root()
            if git_root:
                return [git_root / p for p in self.project_mcp_config_paths]
            else:
                # No git root means we can't determine project paths
                return []

    def get_zenable_server_config(self) -> dict[str, Any]:
        """Get the Zenable MCP server configuration for this IDE."""
        # Use the generic model with OAuth for most IDEs
        generic_config = _GenericMCPRemoteServerConfig()
        return generic_config.model_dump(exclude_none=True)

    def load_config(self, file_path: Path) -> dict[str, Any]:
        """Load a configuration file based on the configured format."""
        if self.config_format == ConfigFormat.YAML:
            return self.manager.load_yaml_config(file_path)
        else:
            return self.manager.load_json_config(file_path)

    def save_config(
        self, file_path: Path, config: dict[str, Any], backup: bool = True
    ) -> None:
        """Save a configuration file based on the configured format."""
        if self.config_format == ConfigFormat.YAML:
            self.manager.save_yaml_config(file_path, config, backup)
        else:
            self.manager.save_json_config(file_path, config, backup)

    def find_config_file(self) -> Optional[Path]:
        """Find the first existing config file from the list of paths."""
        return find_config_file(self.config_paths)

    def get_default_config_path(self) -> Path:
        """Get the default config path for this IDE."""
        paths = self.config_paths
        if not paths:
            raise ValueError(f"No config paths available for {self.name}")
        return get_default_config_path(paths)

    @property
    def hook_config_paths(self) -> list[Path]:
        """Get the active hook config paths based on is_global flag."""
        if self.is_global:
            platform_path = self._get_platform_global_hook_path()
            return [platform_path] if platform_path else []
        else:
            git_root = find_git_root()
            if git_root:
                return [git_root / p for p in self.project_hook_config_paths]
            else:
                # No git root means we can't determine project paths
                return []

    def get_default_hook_config_path(self) -> Optional[Path]:
        """Get the default hook config path for this IDE."""
        paths = self.hook_config_paths
        return paths[0] if paths else None

    def get_instructions_path(self) -> Path:
        """Get the path for the instructions file.

        Returns the instructions_file_path if set.

        Raises:
            InstructionsFileNotFoundError: If instructions file path is not configured.
        """
        if not self.instructions_file_path:
            raise InstructionsFileNotFoundError(self.name)

        if self.is_global:
            # For global, ensure it's in home directory
            if not self.instructions_file_path.is_absolute():
                return Path.home() / self.instructions_file_path
            return self.instructions_file_path
        else:
            # For project, ensure it's relative to git root
            git_root = find_git_root()
            if git_root and not self.instructions_file_path.is_absolute():
                return git_root / self.instructions_file_path
            return self.instructions_file_path

    def get_instructions_location_description(self) -> str:
        """Get a human-readable description of where the instructions file is located."""
        try:
            path = self.get_instructions_path()
            if path:
                return str(path)
        except InstructionsFileNotFoundError:
            echo(
                f"Instructions file not configured for {self.name}",
                persona=Persona.DEVELOPER,
            )
        return "your project root" if not self.is_global else "your home directory"

    def get_validation_model(self):
        """Get the pydantic model class for validating this IDE's configuration."""
        if self._validation_model is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must set _validation_model"
            )
        return self._validation_model

    def get_default_empty_config(self) -> dict[str, Any]:
        """Get the default empty configuration structure for this IDE.

        Override this in subclasses to provide IDE-specific structure.
        """
        return {}

    def ensure_config_structure(self, config: dict[str, Any]) -> None:
        """Ensure the config has the required structure.

        Override this in subclasses to add IDE-specific structure requirements.
        """
        pass

    def merge_server_config(
        self,
        existing_config: dict[str, Any],
        server_name: str,
        server_config: dict[str, Any],
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Merge a server configuration into the existing config.

        Uses self.mcp_server_parent_key to determine the correct key for servers.
        """
        server_key = self.mcp_server_parent_key

        if server_key not in existing_config:
            existing_config[server_key] = {}

        if server_name in existing_config[server_key] and not overwrite:
            raise ValueError(
                f"Server '{server_name}' already exists in configuration. "
                "Use --overwrite to replace it."
            )

        existing_config[server_key][server_name] = server_config
        return existing_config

    def check_config_status(self, existing_config: dict[str, Any]) -> str:
        """Check the status of an existing configuration.

        Returns:
            existing_config_status: 'compatible', 'legacy', or 'incompatible'
        """
        server_key = self.mcp_server_parent_key

        # Check if server key exists
        if server_key not in existing_config:
            return "incompatible"

        # Check if zenable server exists
        if "zenable" not in existing_config[server_key]:
            return "incompatible"

        zenable_config = existing_config[server_key]["zenable"]

        # First try the current validation model
        model_class = self.get_validation_model()
        try:
            model_class.model_validate(zenable_config)
            return "compatible"
        except (ValidationError, ValueError, TypeError, AttributeError):
            pass

        # Try legacy models if available
        for legacy_model_class in self._legacy_models:
            try:
                legacy_model_class.model_validate(zenable_config)
                return "legacy"
            except (ValidationError, ValueError, TypeError, AttributeError):
                continue

        return "incompatible"

    def is_config_compatible(self, existing_config: dict[str, Any]) -> bool:
        """Check if an existing configuration is compatible with what would be installed."""
        existing_config_status = self.check_config_status(existing_config)
        return existing_config_status == "compatible"

    def _check_instructions_would_change(self, overwrite: bool = False) -> bool:
        """Check if instructions file would change if installed.

        Args:
            overwrite: Whether we're in overwrite mode

        Returns:
            True if instructions would change, False otherwise
        """
        try:
            instructions_file = self.get_instructions_path()
            echo(
                f"Checking instructions file: {instructions_file}",
                persona=Persona.DEVELOPER,
            )
            if not instructions_file.exists():
                echo(
                    "Instructions file doesn't exist",
                    persona=Persona.DEVELOPER,
                )
                return True  # Need to create instructions file
            existing_content = instructions_file.read_text()
            # Check if empty or needs updating
            if not existing_content.strip():
                echo("Instructions file is empty", persona=Persona.DEVELOPER)
                return True  # Empty file needs content
            # Check if content would change
            updated_content = self._update_instructions_in_content(
                existing_content, overwrite
            )
            if updated_content != existing_content:
                echo(
                    "Instructions content would change",
                    persona=Persona.DEVELOPER,
                )
                return True  # Instructions would change
            else:
                echo(
                    f"Instructions wouldn't change even with overwrite set to {overwrite}",
                    persona=Persona.DEVELOPER,
                )
        except Exception as e:
            # If we can't check instructions, assume no change needed
            echo(
                f"Exception checking instructions: {e}",
                persona=Persona.DEVELOPER,
            )
        return False

    def would_config_change(self, overwrite: bool = False) -> bool:
        """Check if installing would actually change the configuration."""
        config_path = self.find_config_file()
        if config_path is None:
            echo(
                "No config file found, so determining that the config **would** change",
                persona=Persona.DEVELOPER,
            )
            return True

        existing_config = self.load_config(config_path)

        if not overwrite:
            if self.is_config_compatible(existing_config):
                # Also check if instructions file needs updating
                if self.instructions_file_path:
                    if self._check_instructions_would_change(overwrite):
                        return True
                echo(
                    "Config compatible and instructions unchanged, returning False",
                    persona=Persona.DEVELOPER,
                )
                return False

        is_compatible = self.is_config_compatible(existing_config)
        if not is_compatible:
            echo(
                f"Config is not compatible: {existing_config}",
                persona=Persona.DEVELOPER,
            )
            return True

        if not overwrite or not self.instructions_file_path:
            echo(
                "Overwrite was not set, or there is no instruction file set: config would not change",
                persona=Persona.DEVELOPER,
            )
            return False

        # Overwrite is true and there is an instructions file path, check them
        return self._check_instructions_would_change(overwrite)

    def _prepare_install(
        self, overwrite: bool = False, skip_comment_warning: bool = False
    ) -> tuple[Path, dict[str, Any], bool, InstallStatus, bool]:
        """Prepare for installation by loading config and checking status.

        Returns:
            Tuple of (config_path, existing_config, has_comments, installation_status, mcp_config_needs_update)
        """
        # Check version compatibility before installation
        self._check_and_warn_version()

        config_path = self.find_config_file()
        installation_status = InstallStatus.SUCCESS
        mcp_config_needs_update = True

        if config_path is None:
            config_path = self.get_default_config_path()
            existing_config = self.get_default_empty_config()
            has_comments = False
        else:
            if self.config_format == ConfigFormat.YAML:
                existing_config = self.load_config(config_path)
                has_comments = False  # YAML preserves comments differently
            else:
                existing_config, has_comments = load_json_config(config_path)
            self.ensure_config_structure(existing_config)

            # Check if we have a legacy configuration that needs migration
            existing_config_status = self.check_config_status(existing_config)

            if existing_config_status == "compatible" and not overwrite:
                # MCP config is already properly configured, but still need to check instructions
                mcp_config_needs_update = False
                installation_status = InstallStatus.ALREADY_INSTALLED
            elif existing_config_status == "legacy":
                # Need to migrate from legacy format
                installation_status = InstallStatus.UPGRADED
                echo(
                    click.style(
                        "Upgrading configuration to the latest format",
                        fg="yellow",
                    ),
                    persona=Persona.POWER_USER,
                )

            if has_comments and not skip_comment_warning and mcp_config_needs_update:
                backup_path = backup_config_file(config_path)
                echo(
                    click.style("\n⚠️  Warning: ", fg="yellow", bold=True)
                    + f"The file {config_path} contains comments or JSON5 features.\n"
                    "These comments will be LOST when the file is saved.\n"
                    f"\nA backup has been created at: {backup_path}"
                )

                if not click.confirm(
                    "Do you want to proceed with the modification?", default=False
                ):
                    echo("Installation cancelled")
                    sys.exit(ExitCode.USER_INTERRUPT)

        return (
            config_path,
            existing_config,
            has_comments,
            installation_status,
            mcp_config_needs_update,
        )

    def install(
        self, overwrite: bool = False, skip_comment_warning: bool = False
    ) -> tuple[Path, InstallStatus]:
        """Install the Zenable MCP configuration for this IDE.

        Returns:
            Tuple of (config_path, status):
            - config_path: Path to the configuration file
            - status: InstallStatus enum value
        """
        # Use the common preparation logic
        (
            config_path,
            existing_config,
            has_comments,
            installation_status,
            mcp_config_needs_update,
        ) = self._prepare_install(overwrite, skip_comment_warning)

        # Only update MCP config if needed
        if mcp_config_needs_update:
            server_config = self.get_zenable_server_config()
            updated_config = self.merge_server_config(
                existing_config, "zenable", server_config, overwrite=overwrite
            )

            # Apply any IDE-specific configuration updates
            self.apply_ide_specific_config(updated_config)

            self.save_config(config_path, updated_config, backup=not has_comments)

        # Always check and install instructions file if configured
        instructions_created = False
        if self.instructions_file_path:
            instructions_path = self.get_instructions_path()
            instructions_existed = instructions_path.exists()
            self.install_instructions_file(overwrite)
            # Check if instructions file was created or updated
            if not instructions_existed and instructions_path.exists():
                instructions_created = True
                echo(
                    f"Created instructions file at {instructions_path}",
                    persona=Persona.DEVELOPER,
                )

        # If instructions were created and status was ALREADY_INSTALLED, change to SUCCESS
        if (
            instructions_created
            and installation_status == InstallStatus.ALREADY_INSTALLED
        ):
            installation_status = InstallStatus.SUCCESS
            echo(
                "Changing status from ALREADY_INSTALLED to SUCCESS because instructions were created",
                persona=Persona.DEVELOPER,
            )

        return config_path, installation_status

    def _update_instructions_in_content(
        self, existing_content: str, overwrite: bool = False
    ) -> str:
        """Update instructions in existing content based on overwrite flag.

        Args:
            existing_content: The current content of the file
            overwrite: If True, removes old instructions and replaces with current ones.
                      If False, appends instructions only if not already present.

        Returns:
            Updated content with instructions applied
        """
        if overwrite:
            # Remove old instructions before adding new ones
            # First try to remove the current configured instructions
            if self.instructions_content in existing_content:
                existing_content = existing_content.replace(
                    self.instructions_content, ""
                )
            # Also try to remove the default instructions if different from current
            elif (
                DEFAULT_ZENABLE_INSTRUCTIONS != self.instructions_content
                and DEFAULT_ZENABLE_INSTRUCTIONS in existing_content
            ):
                existing_content = existing_content.replace(
                    DEFAULT_ZENABLE_INSTRUCTIONS, ""
                )
            # Clean up any resulting multiple newlines
            existing_content = re.sub(r"\n{3,}", "\n\n", existing_content.strip())

            # Add the new instructions
            if existing_content:
                if not existing_content.endswith("\n"):
                    existing_content += "\n"
                existing_content += "\n" + self.instructions_content
            else:
                existing_content = self.instructions_content

            return existing_content
        else:
            # Original behavior: only append if not already present
            if "zenable conformance_check" not in existing_content:
                if existing_content and not existing_content.endswith("\n"):
                    existing_content += "\n"
                existing_content += "\n" + self.instructions_content
                return existing_content
            return existing_content  # No changes needed

    def install_instructions_file(self, overwrite: bool = False) -> None:
        """Install the instructions file with zenable rules.

        Args:
            overwrite: If True, removes old instructions and replaces with current ones.
                      If False, appends instructions only if not already present.
        """
        instructions_file = self.get_instructions_path()

        # Create parent directory if needed
        instructions_file.parent.mkdir(parents=True, exist_ok=True)

        if not instructions_file.exists():
            safe_write_text(instructions_file, self.instructions_content)
        else:
            existing_content = instructions_file.read_text()
            # Handle empty files as if they don't exist
            if not existing_content.strip():
                safe_write_text(instructions_file, self.instructions_content)
            else:
                updated_content = self._update_instructions_in_content(
                    existing_content, overwrite
                )

                # Only write if content changed
                if updated_content != existing_content:
                    safe_write_text(instructions_file, updated_content)

    def apply_ide_specific_config(self, config: dict[str, Any]) -> None:
        """Apply any IDE-specific configuration requirements.

        Override this in subclasses to add IDE-specific config like VS Code inputs.
        """
        pass

    def get_post_install_instructions(self) -> Optional[str]:
        """Get any post-installation instructions for this IDE."""
        return None

    def is_installed(self) -> bool:
        """Check if this IDE is installed on the system."""
        return is_ide_installed(
            app_names=self.app_names,
            commands=self.commands,
            config_dirs=self.config_dirs,
            ide_name=self.display_name,
            command_verification_args=self.command_verification_args,
            command_verification_pattern=self.command_verification_pattern,
        )

    def get_installed_version(self) -> Optional[str]:
        """Get the installed version of the IDE.

        Returns:
            The version string if detected, None otherwise.
        """
        if not self.version_command:
            return None

        try:
            # Run the version command. We cannot provide an empty PATH because some IDEs require other deps, like copilot cli needing node, so instead
            # we ensure it is absolute/fully qualified
            command: Path = self.version_command
            if not command.is_absolute():
                raise ValueError(f"Version command must be absolute: {command}")

            result = subprocess.run(
                [command, *self.version_args],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                return None

            output = result.stdout + result.stderr

            # If there's a pattern, use it to extract the version
            if self.version_pattern:
                match = re.search(self.version_pattern, output)
                if match:
                    return match.group(1)

            # Otherwise return the full output (trimmed)
            return output.strip()

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return None

    def check_version_compatibility(self) -> tuple[bool, Optional[str], Optional[str]]:
        """Check if the installed IDE version meets the minimum requirements.

        Returns:
            A tuple of (is_compatible, installed_version, minimum_version)
        """
        if not self.minimum_version:
            # No minimum version requirement
            return (True, None, None)

        installed_version = self.get_installed_version()
        if not installed_version:
            # Can't determine version, assume incompatible
            return (False, None, self.minimum_version)

        # Parse both versions for comparison using the configured parse function
        installed_tuple = self.parse_version(installed_version)
        minimum_tuple = self.parse_version(self.minimum_version)

        if installed_tuple is None or minimum_tuple is None:
            # Can't parse versions, assume incompatible
            return (False, installed_version, self.minimum_version)

        # Check if installed version meets minimum
        is_compatible = installed_tuple >= minimum_tuple
        return (is_compatible, installed_version, self.minimum_version)

    def validate_installation_mode(self, is_global: bool) -> None:
        """Validate if the IDE supports the requested installation mode."""
        if not is_global and not self.supports_mcp_project_config:
            raise ProjectConfigNotSupportedError(
                self.name,
                f"{self.name} only supports global configuration.\n"
                f"Please run with --global flag:\n"
                f"  uvx zenable-mcp install mcp {self.name.lower()} --global",
            )
        if is_global and not self.supports_mcp_global_config:
            raise GlobalConfigNotSupportedError(
                self.name,
                f"{self.name} does not support global configuration.\n"
                f"Please run without the --global flag.",
            )

    def _check_and_warn_version(self) -> None:
        """Check if the installed IDE version meets the minimum requirements and warn if not."""
        # Only check if minimum version is set
        if not self.minimum_version:
            return

        # Check if warning has already been shown for this class
        if hasattr(self.__class__, "_version_warning_shown"):
            if self.__class__._version_warning_shown:
                return

        is_compatible, installed_version, minimum_version = (
            self.check_version_compatibility()
        )

        if not is_compatible:
            warning_msg = f"\n⚠️  Warning: {self.name} version is outdated!\n"

            if installed_version:
                warning_msg += f"  Current version: {installed_version}\n"
            else:
                warning_msg += "  Could not detect installed version\n"

            warning_msg += f"  Minimum required: {minimum_version}\n"
            warning_msg += f"\nPlease update {self.name} to ensure compatibility.\n"

            echo(click.style(warning_msg, fg="yellow", bold=True), err=True)

            # Mark warning as shown for this class
            if hasattr(self.__class__, "_version_warning_shown"):
                self.__class__._version_warning_shown = True

    @classmethod
    def get_capabilities(cls) -> dict[str, Any]:
        """Get the IDE capabilities for registration.

        This method uses the class properties to build the capabilities dict.
        Subclasses should set the appropriate properties in __init__ instead
        of overriding this method.
        """
        # Create a temporary instance to get the properties
        # This is only used for registration, not for actual operations
        instance = cls()

        return {
            "name": instance.name,
            "supports_mcp_global_config": instance.supports_mcp_global_config,
            "supports_mcp_project_config": instance.supports_mcp_project_config,
            "supports_hooks": instance.supports_hooks,
            "global_mcp_config_paths_platform_lookup": instance.global_mcp_config_paths_platform_lookup,
            "global_hook_config_paths_platform_lookup": instance.global_hook_config_paths_platform_lookup,
            "project_config_paths": instance.project_mcp_config_paths,
            "project_hook_paths": instance.project_hook_config_paths,
            "app_names": instance.app_names,
            "commands": instance.commands,
            "config_dirs": instance.config_dirs,
        }


class CursorConfig(IDEConfig):
    """Configuration for Cursor IDE."""

    name = "cursor"
    display_name = "Cursor"

    def __init__(self, is_global: bool = False):
        super().__init__(is_global)

        # https://docs.cursor.com/en/context/mcp#configuration-locations
        self.global_mcp_config_paths_platform_lookup = {
            "windows": {"base_path": "home", "relative_path": ".cursor/mcp.json"},
            "linux": {"base_path": "home", "relative_path": ".cursor/mcp.json"},
            "darwin": {"base_path": "home", "relative_path": ".cursor/mcp.json"},
        }

        # https://docs.cursor.com/en/context/mcp#configuration-locations
        self.project_mcp_config_paths = [Path(".cursor/mcp.json")]

        # https://docs.cursor.com/en/context/rules#project-rules
        # Global (aka User) rules are only supported via the UI as of 2025-08-30: https://docs.cursor.com/en/context/rules#user-rules
        self.instructions_file_path = Path(".cursor/rules/zenable.mdc")
        self.instructions_content: str = f"""---
description: Zenable Conformance Tests
alwaysApply: true
---

{DEFAULT_ZENABLE_INSTRUCTIONS}"""

        # IDE detection
        self.app_names = ["Cursor"]
        self.commands = ["cursor", "cursor-agent"]
        self.config_dirs = [".cursor"]

        # Version checking (cursor doesn't have a consistent --version flag)
        self.version_command = None

        # Validation model - use generic for Cursor
        self._validation_model = _CursorMCPConfig
        # Legacy models for Cursor
        self._legacy_models = [
            _LegacyGenericMCPRemoteServerConfig_2025_09_sse,
            _LegacyZenableMCPConfig_2025_08,
            _LegacyGenericMCPServerConfig_2025_08,
        ]

    def get_post_install_instructions(self) -> Optional[str]:
        """Get post-installation instructions for Cursor."""
        return """
To complete the setup:

1. Click "Enable" when prompted to enable the MCP server
2. Hit Cmd+Shift+P (Ctrl+Shift+P on Windows/Linux), type "View: Open MCP Settings" and hit enter
3. Click "Needs login" and then click "Open" and accept the authorization prompt and finalize the login
"""


class WindsurfConfig(IDEConfig):
    """Configuration for Windsurf IDE."""

    name = "windsurf"
    display_name = "Windsurf"

    # Currently, Windsurf only supports global configs, so we default it to True
    def __init__(self, is_global: bool = True):
        super().__init__(is_global)

        # https://docs.windsurf.com/windsurf/cascade/mcp#mcp-config-json
        self.global_mcp_config_paths_platform_lookup = {
            "windows": {
                "base_path": "home",
                "relative_path": ".codeium/windsurf/mcp_config.json",
            },
            "linux": {
                "base_path": "home",
                "relative_path": ".codeium/windsurf/mcp_config.json",
            },
            # Manually confirmed, 2025-08-29 Windsurf v1.9.4
            "darwin": {
                "base_path": "home",
                "relative_path": ".codeium/windsurf/mcp_config.json",
            },
        }

        # Windsurf doesn't support project mcp configs, only global mcp configs as of 2025-08-30
        # If we add support for this, we should update the instructions_file_path as well, because it uses the global file path to stay in line with this
        self.project_mcp_config_paths = []

        # Validate installation mode after paths are set
        # This uses the base class method that checks capabilities dynamically
        if is_global is False:
            self.validate_installation_mode(is_global)

        # https://docs.windsurf.com/windsurf/cascade/memories#rules-storage-locations
        # There are "Activation Modes" for instructions/rules, but weak documentation. The best I found about this is that it's configured in the UI:
        # https://www.reddit.com/r/windsurf/comments/1kid3a3/comment/mrebgir/
        if is_global:
            self.instructions_file_path = (
                Path.home() / ".codeium/windsurf/memories/global_rules.md"
            )
        else:
            self.instructions_file_path = ".windsurf/rules/zenable.md"

        # IDE detection
        self.app_names = ["Windsurf"]
        self.commands = ["windsurf"]
        self.config_dirs = [".codeium/windsurf"]

        # Validation model - use Windsurf-specific model
        self._validation_model = _WindsurfMCPConfig
        # Legacy models for Windsurf
        self._legacy_models = [
            _LegacyZenableMCPConfig_2025_08,
            _LegacyGenericMCPServerConfig_2025_08,
        ]

    def get_zenable_server_config(self) -> dict[str, Any]:
        """Get the Zenable MCP server configuration for Windsurf.

        Windsurf uses 'serverUrl' instead of 'url' for the server endpoint.
        """
        windsurf_config = _WindsurfMCPConfig()
        return windsurf_config.model_dump(exclude_none=True)

    def get_instructions_path(self) -> Path:
        """Get the path where the instructions file should be created for Windsurf."""
        if not self.instructions_file_path:
            raise InstructionsFileNotFoundError(self.name)

        if not self.is_global:
            raise ProjectConfigNotSupportedError(
                "Windsurf",
                "Windsurf only supports global configuration.\n"
                "Please use --global flag for Windsurf installations.",
            )
        else:
            return self.instructions_file_path

    def get_post_install_instructions(self) -> Optional[str]:
        """Get post-installation instructions for Windsurf."""
        return """
To complete the setup:

1. Hit Cmd+, (Ctrl+, on Windows/Linux), go to "Cascade" on the left, then click "Manage MCPs"
2. Click "Refresh" and then click "Open" when prompted to go to https://zenable.us.auth0.com/authorize and Accept/finish the login
3. After you've accepted the login you can close that browser tab and your Windsurf environment is all set 🚀
"""


# Kiro is temporarily not supported because as of 2025-09-04, Kiro explicitly documents that they only support stdio MCP servers and to use npx
# mcp-remote to support remote servers
# https://kiro.dev/docs/mcp/servers/#remote-mcp-servers
# class KiroConfig(IDEConfig):
#     """Configuration for Kiro IDE."""
#
#     name = "kiro"
#     display_name = "Kiro"
#
#     def __init__(self, is_global: bool = False):
#         super().__init__(is_global)
#
#         # https://kiro.dev/docs/mcp/configuration/#configuration-locations
#         self.global_mcp_config_paths_platform_lookup = {
#             "windows": {
#                 "base_path": "home",
#                 "relative_path": ".kiro/settings/mcp.json",
#             },
#             "linux": {"base_path": "home", "relative_path": ".kiro/settings/mcp.json"},
#             "darwin": {"base_path": "home", "relative_path": ".kiro/settings/mcp.json"},
#         }
#         self.project_mcp_config_paths = [Path(".kiro/settings/mcp.json")]
#
#         # https://kiro.dev/docs/steering/
#         # Also related are specs but they require a specific format, which we don't (yet) conform to. htps://kiro.dev/docs/specs/
#         # As of 2025-08-30 Kiro does not support global steering
#         self.instructions_file_path = Path(".kiro/steering/zenable.md")
#         # https://kiro.dev/docs/steering/#inclusion-modes
#         self.instructions_content: str = f"""---
# inclusion: always
# ---
#
# {DEFAULT_ZENABLE_INSTRUCTIONS}"""
#
#         # IDE detection
#         self.app_names = ["Kiro"]
#         self.commands = ["kiro"]
#         self.config_dirs = [".kiro"]
#
#         # Validation model
#         self._validation_model = _KiroMCPConfig
#
#     def get_instructions_path(self) -> Path:
#         """Get the path where the instructions file should be created for Kiro."""
#         if not self.instructions_file_path:
#             raise InstructionsFileNotFoundError(self.name)
#
#         # https://kiro.dev/docs/steering/#creating-custom-steering-files
#         git_root = find_git_root()
#         if git_root:
#             return git_root / self.instructions_file_path
#         else:
#             return self.instructions_file_path
#
#     def get_zenable_server_config(self) -> dict[str, Any]:
#         """Get the Zenable MCP server configuration for Kiro."""
#         # Use Pydantic model with OAuth to generate the configuration
#         kiro_config = _KiroMCPConfig()
#         return kiro_config.model_dump(exclude_none=True)


class GeminiCLIConfig(IDEConfig):
    """Configuration for Gemini CLI."""

    name = "gemini"
    display_name = "Gemini CLI"

    def __init__(self, is_global: bool = False):
        super().__init__(is_global)

        # https://cloud.google.com/gemini/docs/codeassist/use-agentic-chat-pair-programmer#create-context-file
        # https://github.com/yoichiro/gemini-cli/blob/main/docs/cli/configuration.md#top-level-settings
        self.global_mcp_config_paths_platform_lookup = {
            "windows": {"base_path": "home", "relative_path": ".gemini/settings.json"},
            "linux": {"base_path": "home", "relative_path": ".gemini/settings.json"},
            "darwin": {"base_path": "home", "relative_path": ".gemini/settings.json"},
        }
        self.project_mcp_config_paths = [Path(".gemini/settings.json")]

        # https://cloud.google.com/gemini/docs/codeassist/use-agentic-chat-pair-programmer#create-context-file
        # https://github.com/yoichiro/gemini-cli/blob/main/docs/cli/configuration.md#context-files-hierarchical-instructional-context
        if is_global:
            self.instructions_file_path = Path.home() / ".gemini/GEMINI.md"
        else:
            self.instructions_file_path = Path("GEMINI.md")

        # IDE detection
        self.app_names = []  # Gemini is CLI-only
        self.commands = ["gemini"]
        self.config_dirs = [".gemini"]

        # Validation model for MCP server configs
        self._validation_model = _GeminiMCPConfig
        # Legacy models for Gemini
        self._legacy_models = [
            _LegacyGeminiMCPConfig_2025_09_sse,
            _LegacyGeminiMCPConfig_2025_08,
            _LegacyGenericMCPServerConfig_2025_08,
        ]

    def get_zenable_server_config(self) -> dict[str, Any]:
        """Get the Zenable MCP server configuration for Gemini CLI."""
        gemini_config = _GeminiMCPConfig()
        return gemini_config.model_dump(exclude_none=True)

    def get_post_install_instructions(self) -> Optional[str]:
        """Get post-installation instructions for Gemini CLI."""
        return """
To complete the setup:

1. Reopen Gemini CLI
2. Complete the authentication by running: /mcp auth zenable and hitting "Accept"
"""


class RooCodeConfig(IDEConfig):
    """Configuration for Roo Code."""

    name = "roo"
    display_name = "Roo Code"

    def __init__(self, is_global: bool = False):
        super().__init__(is_global)

        # https://docs.roocode.com/features/mcp/using-mcp-in-roo#configuring-mcp-servers
        self.global_mcp_config_paths_platform_lookup = {
            "windows": {
                "base_path": "appdata",
                "relative_path": "Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json",
            },
            # Manually confirmed, 2025-08-29 https://github.com/Zenable-io/next-gen-governance/pull/2282#pullrequestreview-3170163596
            "linux": {
                "base_path": "xdg_config",
                "relative_path": "Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json",
            },
            # Manually confirmed, 2025-08-29 Roo v3.26.2
            "darwin": {
                "base_path": "application_support",
                "relative_path": "Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json",
            },
        }
        # https://docs.roocode.com/features/mcp/using-mcp-in-roo#editing-mcp-settings-files
        self.project_mcp_config_paths = [Path(".roo/mcp.json")]

        # https://docs.roocode.com/features/custom-instructions
        if is_global:
            self.instructions_file_path = Path.home() / ".roo/rules/zenable.md"
        else:
            self.instructions_file_path = Path(".roo/rules/zenable.md")

        # IDE detection
        self.app_names = ["Roo Code", "Roo Cline", "Roo"]
        self.commands = ["roo"]
        self.config_dirs = [".roo"]

        # Validation model
        self._validation_model = _RooMCPConfig
        # Legacy models for Roo Code
        self._legacy_models = [
            _LegacyRooMCPConfig_2025_08,
            _LegacyGenericMCPServerConfig_2025_08,
        ]

    def get_zenable_server_config(self) -> dict[str, Any]:
        """Get the Zenable MCP server configuration for Roo Code."""
        # Use Pydantic model with OAuth to generate the configuration
        roo_config = _RooMCPConfig()
        return roo_config.model_dump(exclude_none=True)

    def get_post_install_instructions(self) -> Optional[str]:
        """Get post-installation instructions for Roo Code."""
        return """
IMPORTANT: To complete the setup,make sure you have npx installed (required to support OAuth in Roo)
   - If not installed, visit: https://docs.npmjs.com/downloading-and-installing-node-js-and-npm
"""


class ClaudeCodeConfig(IDEConfig):
    """Configuration for Claude Code."""

    name = "claude-code"
    display_name = "Claude Code"

    # Class variable to track if version warning has been shown
    _version_warning_shown = False

    def __init__(self, is_global: bool = False):
        super().__init__(is_global)

        # https://docs.anthropic.com/en/docs/claude-code/mcp
        # In the future we should add support for managing this via the claude CLI, like:
        # claude mcp add zenable --scope user "https://mcp.zenable.app" --transport http
        # or
        # claude mcp add-json zenable "{}" --scope user
        #
        # And if we wanted to upgrade we could first do:
        # claude mcp remove zenable --scope user
        self.global_mcp_config_paths_platform_lookup = {
            "windows": {"base_path": "home", "relative_path": ".claude.json"},
            "linux": {"base_path": "home", "relative_path": ".claude.json"},
            "darwin": {"base_path": "home", "relative_path": ".claude.json"},
        }

        # https://docs.anthropic.com/en/docs/claude-code/hooks#configuration
        self.global_hook_config_paths_platform_lookup = {
            "windows": {"base_path": "home", "relative_path": ".claude/settings.json"},
            "linux": {"base_path": "home", "relative_path": ".claude/settings.json"},
            "darwin": {"base_path": "home", "relative_path": ".claude/settings.json"},
        }

        # https://docs.anthropic.com/en/docs/claude-code/mcp#project-scope
        self.project_mcp_config_paths = [Path(".mcp.json")]
        # https://docs.anthropic.com/en/docs/claude-code/settings#settings-files
        self.project_hook_config_paths = [Path(".claude/settings.json")]
        # https://docs.anthropic.com/en/docs/claude-code/memory#determine-memory-type
        # Claude Code instructions are disabled because the hooks are much more reliable
        # self.instructions_file_path = Path("CLAUDE.md")

        # IDE detection
        self.app_names = []  # Claude Code is CLI-only
        self.commands = ["claude-code", "claude"]
        self.config_dirs = [".claude"]

        # Version checking
        version_cmd = shutil.which("claude")
        if version_cmd:
            self.version_command = Path(version_cmd)
        else:
            self.version_command = None
        self.version_args = ["--version"]
        self.version_pattern = (
            r"(\d+\.\d+\.\d+)"  # Extracts "1.0.58" from "1.0.58 (Claude Code)"
        )
        self.minimum_version = "1.0.58"

        # Validation models
        self._validation_model = _ClaudeCodeMCPConfig
        self._legacy_models = [
            _LegacyClaudeCodeMCPConfig_2025_09_sse,
            _LegacyClaudeCodeMCPConfig_2025_09,
            _LegacyClaudeCodeMCPServerConfig_2025_08,
            _LegacyGenericMCPServerConfig_2025_08,
        ]

    def get_zenable_server_config(self) -> dict[str, Any]:
        """Get the Zenable MCP server configuration for Claude Code."""
        # Use Pydantic model with OAuth to generate the configuration
        claude_config = _ClaudeCodeMCPConfig()
        return claude_config.model_dump(exclude_none=True)


class VSCodeConfig(IDEConfig):
    """Configuration for Visual Studio Code."""

    name = "vscode"
    display_name = "VS Code"

    def __init__(self, is_global: bool = False):
        super().__init__(is_global)

        # https://code.visualstudio.com/docs/copilot/customization/mcp-servers
        # Note that VS Code supports multiple profiles, which are supposed to be able to have different MCP configurations
        # https://code.visualstudio.com/docs/configure/profiles#_where-are-profiles-kept
        self.global_mcp_config_paths_platform_lookup = {
            "windows": {"base_path": "appdata", "relative_path": "Code/User/mcp.json"},
            "linux": {"base_path": "xdg_config", "relative_path": "Code/User/mcp.json"},
            "darwin": {
                "base_path": "application_support",
                "relative_path": "Code/User/mcp.json",
            },
        }

        # https://code.visualstudio.com/docs/copilot/customization/mcp-servers#_add-an-mcp-server
        self.project_mcp_config_paths = [Path(".vscode/mcp.json")]

        # https://code.visualstudio.com/docs/copilot/customization/custom-instructions
        self.instructions_file_path = Path(".github/copilot-instructions.md")

        # IDE detection
        self.app_names = ["Visual Studio Code", "Code", "VSCode"]
        self.commands = ["code"]
        self.config_dirs = [".vscode"]

        # Validation model
        self._validation_model = _VSCodeMCPConfig
        # Legacy models for VS Code
        self._legacy_models = [
            _LegacyVSCodeMCPConfig_2025_09_sse,
            _LegacyVSCodeMCPConfig_2025_09,
            _LegacyGenericMCPServerConfig_2025_08,
        ]

        # VS Code uses 'servers' instead of 'mcpServers'
        self.mcp_server_parent_key = "servers"

    @property
    def global_mcp_config_paths(self) -> list[Path]:
        """Get the global MCP config paths for VS Code."""
        if self.is_global:
            platform_path = self._get_platform_global_config_path()
            return [platform_path] if platform_path else []
        return []

    def get_zenable_server_config(self) -> dict[str, Any]:
        """Get the Zenable MCP server configuration for VS Code."""
        # Use Pydantic model with OAuth to generate the configuration
        vscode_config = _VSCodeMCPConfig()
        return vscode_config.model_dump(exclude_none=True)

    def get_default_empty_config(self) -> dict[str, Any]:
        """Get the default empty configuration structure for VS Code."""
        return {"servers": {}, "inputs": []}

    def ensure_config_structure(self, config: dict[str, Any]) -> None:
        """Ensure VS Code config has servers and inputs keys."""
        if "servers" not in config:
            config["servers"] = {}
        if "inputs" not in config:
            config["inputs"] = []

    def apply_ide_specific_config(self, config: dict[str, Any]) -> None:
        """Apply VS Code specific configuration."""
        # Ensure inputs array exists for other potential inputs
        if "inputs" not in config:
            config["inputs"] = []

    def get_post_install_instructions(self) -> Optional[str]:
        return """
IMPORTANT: To complete the setup:

1. Restart VS Code
2. Hit Cmd+Shift+P (Ctrl+Shift+P on Windows/Linux), type "MCP: List Servers" and hit enter, select "Zenable", then click "Start Server"
3. When prompted, you'll need to select "Trust" for the MCP server Zenable (https://code.visualstudio.com/docs/copilot/customization/mcp-servers#_mcp-server-trust)
4. Complete OAuth authentication when prompted
5. When prompted for authentication against zenable.us.auth0.com, click Allow.
6. Make sure your Copilot pane is in Agent or Edit mode (https://code.visualstudio.com/docs/copilot/customization/mcp-servers#_use-mcp-tools-in-agent-mode)
"""


class AmazonQConfig(IDEConfig):
    """Configuration for Amazon Q Developer."""

    name = "amazonq"
    display_name = "Amazon Q"

    def __init__(self, is_global: bool = False):
        super().__init__(is_global)

        # https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/mcp-ide.html
        self.global_mcp_config_paths_platform_lookup = {
            "windows": {
                "base_path": "home",
                "relative_path": ".aws/amazonq/agents/default.json",
            },
            "linux": {
                "base_path": "home",
                "relative_path": ".aws/amazonq/agents/default.json",
            },
            "darwin": {
                "base_path": "home",
                "relative_path": ".aws/amazonq/agents/default.json",
            },
        }

        # https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/mcp-ide.html
        # As of 2025-09-02 the documentation says .amazonq/mcp.json for project configs but .amazonq/agents/default.json is the correct location
        self.project_mcp_config_paths = [Path(".amazonq/agents/default.json")]

        # https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/context-project-rules.html
        if is_global:
            # At the moment, Amazon Q doesn't seem to support global rules
            self.instructions_file_path = Path(".amazonq/rules/zenable.md")
        else:
            self.instructions_file_path = Path(".amazonq/rules/zenable.md")

        # Amazon Q seems to support "Context Hooks" including global configuration in ~/.aws/amazonq/global_context.json or per-profile at
        # ~/.aws/amazonq/profiles/profile-name/context.json but we aren't using them yet
        # https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/command-line-context-hooks.html

        # IDE detection
        self.app_names = ["Amazon Q", "Amazon Q Developer"]
        # https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/command-line-settings.html
        self.commands = ["q"]
        # Today this is relative to home (that should change in the future so it's more flexible)
        # .aws/amazonq is the only actual one that's in the home dir; .amazonq (afaict) is relative to the root of a repo, but putting it in here just
        # in case
        self.config_dirs = [".amazonq", ".aws/amazonq"]

        # Validation model
        self._validation_model = _AmazonQMCPConfig
        # Legacy models - specific first, generic second
        self._legacy_models = [
            _LegacyAmazonQMCPConfig_2025_09,
            _LegacyGenericMCPServerConfig_2025_08,
        ]

    def get_default_empty_config(self) -> dict[str, Any]:
        """Get the default empty configuration structure for Amazon Q."""
        # This was accurate as of 2025-09-02
        return {
            "name": "default-agent",
            "version": "1.0.0",
            "description": "Agent configuration",
            "mcpServers": {},
            "tools": [],
            "allowedTools": [],
            "toolsSettings": {},
            "includedFiles": [],
            "resources": [],
        }

    def merge_server_config(
        self,
        existing_config: dict[str, Any],
        server_name: str,
        server_config: dict[str, Any],
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Merge a server configuration into the existing Amazon Q config.

        Amazon Q has a special structure with tools and allowedTools arrays that need
        to be updated when adding MCP servers.
        """
        # Ensure mcpServers exists
        if "mcpServers" not in existing_config:
            existing_config["mcpServers"] = {}

        # Check if server already exists
        if server_name in existing_config["mcpServers"] and not overwrite:
            raise ValueError(
                f"Server '{server_name}' already exists in configuration. "
                "Use --overwrite to replace it."
            )

        # Add/update the server configuration
        existing_config["mcpServers"][server_name] = server_config

        # Update tools array - add @zenable if not present
        if "tools" not in existing_config:
            existing_config["tools"] = []
        if "@zenable" not in existing_config["tools"]:
            existing_config["tools"].append("@zenable")

        # Update allowedTools array - add @zenable/conformance_check if not present
        if "allowedTools" not in existing_config:
            existing_config["allowedTools"] = []
        if "@zenable/conformance_check" not in existing_config["allowedTools"]:
            existing_config["allowedTools"].append("@zenable/conformance_check")

        return existing_config

    def get_zenable_server_config(self) -> dict[str, Any]:
        """Get the Zenable MCP server configuration for Amazon Q."""
        # Use Pydantic model to generate the configuration
        amazonq_config = _AmazonQMCPConfig()
        return amazonq_config.model_dump(exclude_none=True)

    def get_post_install_instructions(self) -> Optional[str]:
        return """
IMPORTANT: To complete the setup, make sure you have npx installed (required to support OAuth in Roo)
   - If not installed, visit: https://docs.npmjs.com/downloading-and-installing-node-js-and-npm

NOTE: Amazon Q is notorious for taking a while to connect to a new MCP server.
"""


class ContinueConfig(IDEConfig):
    """Configuration for Continue IDE."""

    name = "continue"
    display_name = "Continue"

    def __init__(self, is_global: bool = False):
        super().__init__(is_global)

        # Continue uses YAML format for MCP configuration
        self.config_format = ConfigFormat.YAML

        # https://docs.continue.dev/customize/deep-dives/configuration.md
        self.global_mcp_config_paths_platform_lookup = {
            "windows": {
                "base_path": "home",
                "relative_path": ".continue/mcpServers/zenable.yaml",
            },
            "linux": {
                "base_path": "home",
                "relative_path": ".continue/mcpServers/zenable.yaml",
            },
            "darwin": {
                "base_path": "home",
                "relative_path": ".continue/mcpServers/zenable.yaml",
            },
        }

        # https://docs.continue.dev/customize/deep-dives/mcp
        self.project_mcp_config_paths = [Path(".continue/mcpServers/zenable.yaml")]

        # https://docs.continue.dev/customize/deep-dives/rules
        if is_global:
            self.instructions_file_path = Path.home() / ".continue/rules/zenable.md"
        else:
            self.instructions_file_path = Path(".continue/rules/zenable.md")

        # https://docs.continue.dev/customize/deep-dives/rules#how-to-configure-rule-properties-and-syntax
        self.instructions_content: str = f"""---
name: Zenable Conformance Tests
description: Zenable cleans up sloppy AI code, prevents vulnerabilities, and automates governance with deterministic guardrails
alwaysApply: true
---

{DEFAULT_ZENABLE_INSTRUCTIONS}"""

        # IDE detection
        self.app_names = ["Continue"]
        # https://docs.continue.dev/guides/cli
        self.commands = ["cn"]
        self.config_dirs = [".continue"]

        # Validation model
        self._validation_model = _ContinueMCPConfig
        # Legacy models for Continue
        self._legacy_models = [
            _LegacyContinueMCPConfig_2025_09_sse,
        ]

    def get_zenable_server_config(self) -> dict[str, Any]:
        """Get the complete Zenable MCP configuration file for Continue.

        Continue expects a complete YAML file with metadata, not just server config.
        """
        # Create the complete configuration with version
        continue_config = _ContinueMCPConfig(version=ZENABLE_MCP_VERSION)
        # Use by_alias=True to ensure we get "schema" instead of "schema_version"
        return continue_config.model_dump(exclude_none=True, by_alias=True)

    def get_default_empty_config(self) -> dict[str, Any]:
        """Get the default empty configuration structure for Continue.

        Since we own the entire file, return the complete structure.
        """
        return self.get_zenable_server_config()

    def merge_server_config(
        self,
        existing_config: dict[str, Any],
        server_name: str,
        server_config: dict[str, Any],
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """For Continue, we replace the entire file since we own it.

        Continue uses separate YAML files per MCP server, so we just
        return the new configuration.
        """
        # For Continue, we always return the full config since we own the file
        return server_config

    def check_config_status(self, existing_config: dict[str, Any]) -> str:
        """Check the status of an existing Continue configuration.

        Continue owns the entire YAML file, so we validate the whole structure.

        Returns:
            existing_config_status: 'compatible', 'legacy', or 'incompatible'
        """
        # For Continue, we validate the entire config structure using Pydantic
        model_class = self.get_validation_model()

        # Make a copy to avoid modifying the original
        config_to_validate = existing_config.copy()

        # The version field will differ between installations, so we need to be flexible
        # Check if the version field exists but don't validate its exact value
        if "version" not in config_to_validate:
            return "incompatible"

        # Replace the version with the current version for validation purposes
        # This allows us to validate the structure without requiring exact version match
        config_to_validate["version"] = ZENABLE_MCP_VERSION

        try:
            # Validate using the Pydantic model
            model_class.model_validate(config_to_validate)
            return "compatible"
        except (ValidationError, ValueError, TypeError, AttributeError):
            pass

        # Check legacy models if available (though Continue has none currently)
        for legacy_model_class in self._legacy_models:
            try:
                legacy_model_class.model_validate(config_to_validate)
                return "legacy"
            except (ValidationError, ValueError, TypeError, AttributeError):
                continue

        return "incompatible"

    def is_config_compatible(self, existing_config: dict[str, Any]) -> bool:
        """Check if an existing Continue configuration is compatible."""
        # For Continue, we need to check if the entire structure matches
        existing_config_status = self.check_config_status(existing_config)
        return existing_config_status == "compatible"


class CopilotCLIConfig(IDEConfig):
    """Configuration for GitHub Copilot CLI."""

    name = "copilot"
    display_name = "GitHub Copilot CLI"

    # Currently, GitHub Copilot CLI only supports global configs, so we default it to True
    def __init__(self, is_global: bool = True):
        super().__init__(is_global)

        # https://docs.github.com/en/copilot/how-tos/use-copilot-agents/use-copilot-cli#add-an-mcp-server
        # Note: Currently documented as using XDG_CONFIG_HOME (defaulting to ~/.config) on all platforms, however when you open copilot and use /mcp
        # add it actually puts it in ~/.copilot
        # Related: https://github.com/github/docs/pull/40683
        self.global_mcp_config_paths_platform_lookup = {
            "windows": {
                "base_path": "home",
                "relative_path": ".copilot/mcp-config.json",
            },
            "linux": {"base_path": "home", "relative_path": ".copilot/mcp-config.json"},
            "darwin": {
                "base_path": "home",
                "relative_path": ".copilot/mcp-config.json",
            },
        }

        # GitHub Copilot CLI appears to only support global config
        self.project_mcp_config_paths = []

        # Validate installation mode after paths are set
        # This uses the base class method that checks capabilities dynamically
        if is_global is False:
            self.validate_installation_mode(is_global)

        # https://docs.github.com/en/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot
        self.instructions_file_path = Path(".github/copilot-instructions.md")

        # IDE detection
        self.app_names = []  # Copilot CLI is CLI-only
        self.commands = ["copilot"]
        self.config_dirs = []

        # Command verification to disambiguate from AWS Copilot CLI
        # When we run 'copilot -h', GitHub's CLI includes "GitHub Copilot CLI" in output
        self.command_verification_args = ["-h"]
        self.command_verification_pattern = r"GitHub Copilot CLI"

        # Version checking - find the correct copilot binary (GitHub, not AWS)
        # We need to use the verification logic to find the right copilot

        copilot_paths = _find_all_commands("copilot")
        verified_copilot = None

        # Find the GitHub Copilot CLI among potentially multiple copilot binaries
        if copilot_paths:
            for cmd_path in copilot_paths:
                if not cmd_path.is_absolute():
                    raise ValueError(f"Command path must be absolute: {cmd_path}")
                try:
                    result = subprocess.run(
                        [cmd_path, "-h"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        check=False,
                    )
                    output = result.stdout + result.stderr
                    if re.search(r"GitHub Copilot CLI", output, re.IGNORECASE):
                        verified_copilot = cmd_path
                        break
                except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                    continue

        if verified_copilot:
            self.version_command = verified_copilot
            self.version_args = ["--version"]
            self.version_pattern = r"(\d+\.\d+\.\d+)"
            self.minimum_version = None  # No minimum version requirement yet
        else:
            self.version_command = None

        self._validation_model = _CopilotCLIMCPConfig
        self._legacy_models = []

    def get_zenable_server_config(self) -> dict[str, Any]:
        """Get the Zenable MCP server configuration for GitHub Copilot CLI."""
        copilot_config = _CopilotCLIMCPConfig()
        return copilot_config.model_dump(exclude_none=True)


IDE_CONFIGS = {
    "cursor": CursorConfig,
    "windsurf": WindsurfConfig,
    # "kiro": KiroConfig,  # Temporarily disabled until they support remote OAuth servers
    "gemini": GeminiCLIConfig,
    "roo": RooCodeConfig,
    "claude-code": ClaudeCodeConfig,
    "vscode": VSCodeConfig,
    "amazonq": AmazonQConfig,
    "continue": ContinueConfig,
    "copilot": CopilotCLIConfig,
}

# Reverse lookup: class -> name
IDE_CLASS_TO_NAME = {v: k for k, v in IDE_CONFIGS.items()}


def create_ide_config(ide_name: str, is_global: bool = False) -> IDEConfig:
    """Create or get an IDE configuration instance from the registry.

    Raises:
        ValueError: If the IDE is not supported
        ProjectConfigNotSupportedError: If IDE doesn't support project-level configuration
        GlobalConfigNotSupportedError: If IDE doesn't support global configuration
    """
    registry = IDERegistry()
    ide_name_lower = ide_name.lower()
    ide_class = registry.ide_configs.get(ide_name_lower)

    if not ide_class:
        raise ValueError(
            f"Unsupported IDE: {ide_name}. Supported IDEs: {', '.join(get_supported_ides())}"
        )

    # Try to create the config - let capability errors propagate
    cache_key = (ide_name_lower, is_global)
    if cache_key not in IDERegistry._ide_instances:
        IDERegistry._ide_instances[cache_key] = ide_class(is_global)

    return IDERegistry._ide_instances[cache_key]


def get_ides_supporting_global() -> list[str]:
    """Get list of IDEs that support global MCP configuration."""
    registry = IDERegistry()
    result = []
    for ide_name in IDE_CONFIGS.keys():
        # Get or create instance from registry
        instance = registry.get_ide(ide_name, False)
        if instance and instance.supports_mcp_global_config:
            result.append(ide_name)
    return result


def get_ides_supporting_project() -> list[str]:
    """Get list of IDEs that support project-level MCP configuration."""
    registry = IDERegistry()
    result = []
    for ide_name in IDE_CONFIGS.keys():
        # Get or create instance from registry
        instance = registry.get_ide(ide_name, False)
        if instance and instance.supports_mcp_project_config:
            result.append(ide_name)
    return result


def get_ides_supporting_hooks() -> list[str]:
    """Get list of IDEs that support hooks."""
    registry = IDERegistry()
    result = []
    for ide_name in IDE_CONFIGS.keys():
        # Get or create instance from registry
        instance = registry.get_ide(ide_name, False)
        if instance and instance.supports_hooks:
            result.append(ide_name)
    return result


def count_ides_supporting(
    mcp_global_config: bool | None = None,
    mcp_project_config: bool | None = None,
    hooks: bool | None = None,
) -> int:
    """Count IDEs supporting specific capabilities.

    Args:
        mcp_global_config: If True, count IDEs supporting global MCP config
        mcp_project_config: If True, count IDEs supporting project MCP config
        hooks: If True, count IDEs supporting hooks

    Returns:
        Number of IDEs matching all specified criteria
    """
    registry = IDERegistry()
    count = 0

    for ide_name in IDE_CONFIGS.keys():
        # Get or create instance from registry
        instance = registry.get_ide(ide_name, False)
        if not instance:
            continue

        matches = True

        if (
            mcp_global_config is not None
            and instance.supports_mcp_global_config != mcp_global_config
        ):
            matches = False

        if (
            mcp_project_config is not None
            and instance.supports_mcp_project_config != mcp_project_config
        ):
            matches = False

        if hooks is not None and instance.supports_hooks != hooks:
            matches = False

        if matches:
            count += 1

    return count


class IDERegistry:
    """Singleton registry for IDE configurations."""

    _instance = None
    _lock = threading.Lock()
    # Class-level cache for IDE instances
    _ide_instances: dict[tuple[str, bool], IDEConfig] = {}

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.ide_configs = IDE_CONFIGS
        return cls._instance

    def get_ide(self, name: str, is_global: bool = False) -> Optional[IDEConfig]:
        """Get an IDE configuration by name, creating it if necessary.

        Args:
            name: IDE name (case insensitive)
            is_global: Whether this is a global configuration

        Returns:
            IDEConfig instance or None if not found (including when IDE doesn't support the requested mode)
        """
        ide_name_lower = name.lower()
        ide_class = self.ide_configs.get(ide_name_lower)
        if not ide_class:
            return None

        # Use cache key to get or create instance
        cache_key = (ide_name_lower, is_global)
        if cache_key not in IDERegistry._ide_instances:
            try:
                IDERegistry._ide_instances[cache_key] = ide_class(is_global)
            except ProjectConfigNotSupportedError:
                # This IDE doesn't support project-level config with is_global=False
                return None
            except GlobalConfigNotSupportedError:
                # This IDE doesn't support global config with is_global=True
                return None
        return IDERegistry._ide_instances[cache_key]

    def get_installed_ides(self) -> list[str]:
        """Get list of installed IDE names."""
        installed = []
        for ide_name in self.ide_configs.keys():
            instance = self.get_ide(ide_name, False)
            if instance and instance.is_installed():
                installed.append(ide_name)
        return installed

    def get_registered_ides(self) -> list[str]:
        """Get all registered IDE names."""
        return list(self.ide_configs.keys())

    def get_display_names(self) -> dict[str, str]:
        """Get mapping of IDE keys to their display names.

        Uses the display_name class attribute from each IDE class.

        Returns:
            Dictionary mapping IDE keys (e.g., 'cursor') to display names (e.g., 'Cursor')
        """
        return {
            ide_key: ide_class.display_name
            for ide_key, ide_class in self.ide_configs.items()
        }


# Helper functions that use the registry
def get_supported_ides() -> list[str]:
    """Get list of supported IDE names."""
    return list(IDE_CONFIGS.keys())


def get_ide_display_names() -> dict[str, str]:
    """Get mapping of IDE keys to their display names.

    Returns:
        Dictionary mapping IDE keys (e.g., 'cursor') to display names (e.g., 'Cursor')
    """
    registry = IDERegistry()
    return registry.get_display_names()
