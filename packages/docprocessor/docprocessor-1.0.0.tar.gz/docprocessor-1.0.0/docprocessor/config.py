"""
Configuration management for docprocessor.

Provides centralized configuration with support for environment variables
and configuration files.
"""

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict


@dataclass
class ProcessorConfig:
    """Configuration for DocumentProcessor."""

    # OCR settings
    ocr_enabled: bool = True

    # Chunking settings
    chunk_size: int = 512
    chunk_overlap: int = 50
    min_chunk_size: int = 100
    max_chunk_size: int = 2000

    # Summarization settings
    summary_target_words: int = 500
    llm_temperature: float = 0.3

    # Processing settings
    max_retries: int = 3
    timeout: int = 300  # seconds

    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @classmethod
    def from_env(cls, prefix: str = "DOCPROCESSOR_") -> "ProcessorConfig":
        """
        Load configuration from environment variables.

        Environment variables should be prefixed (default: DOCPROCESSOR_)
        and match the field names in uppercase.

        Example:
            DOCPROCESSOR_CHUNK_SIZE=1024
            DOCPROCESSOR_OCR_ENABLED=false

        Args:
            prefix: Prefix for environment variables

        Returns:
            ProcessorConfig instance with values from environment
        """
        config_dict = {}

        # Map of field names to their types
        type_map = {
            "ocr_enabled": bool,
            "chunk_size": int,
            "chunk_overlap": int,
            "min_chunk_size": int,
            "max_chunk_size": int,
            "summary_target_words": int,
            "llm_temperature": float,
            "max_retries": int,
            "timeout": int,
            "log_level": str,
            "log_format": str,
        }

        for field_name, field_type in type_map.items():
            env_var = f"{prefix}{field_name.upper()}"
            env_value = os.getenv(env_var)

            if env_value is not None:
                # Convert string to appropriate type
                if field_type == bool:
                    config_dict[field_name] = env_value.lower() in ("true", "1", "yes")
                elif field_type == int:
                    config_dict[field_name] = int(env_value)
                elif field_type == float:
                    config_dict[field_name] = float(env_value)
                else:
                    config_dict[field_name] = env_value

        return cls(**config_dict)

    @classmethod
    def from_file(cls, path: str) -> "ProcessorConfig":
        """
        Load configuration from a JSON file.

        Args:
            path: Path to JSON configuration file

        Returns:
            ProcessorConfig instance with values from file

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            json.JSONDecodeError: If file contains invalid JSON
        """
        config_path = Path(path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(config_path) as f:
            config_dict = json.load(f)

        return cls(**config_dict)

    def to_file(self, path: str) -> None:
        """
        Save configuration to a JSON file.

        Args:
            path: Path where configuration should be saved
        """
        config_dict = asdict(self)

        with open(path, "w") as f:
            json.dump(config_dict, f, indent=2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)

    def update(self, **kwargs) -> "ProcessorConfig":
        """
        Create a new configuration with updated values.

        Args:
            **kwargs: Fields to update

        Returns:
            New ProcessorConfig instance with updated values
        """
        config_dict = asdict(self)
        config_dict.update(kwargs)
        return ProcessorConfig(**config_dict)

    def validate(self) -> None:
        """
        Validate configuration values.

        Raises:
            ValueError: If any configuration value is invalid
        """
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

        if self.min_chunk_size <= 0:
            raise ValueError("min_chunk_size must be positive")

        if self.max_chunk_size <= self.min_chunk_size:
            raise ValueError("max_chunk_size must be greater than min_chunk_size")

        if self.summary_target_words <= 0:
            raise ValueError("summary_target_words must be positive")

        if not 0.0 <= self.llm_temperature <= 2.0:
            raise ValueError("llm_temperature must be between 0.0 and 2.0")

        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")

        if self.timeout <= 0:
            raise ValueError("timeout must be positive")

        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(f"log_level must be one of {valid_log_levels}")


@dataclass
class MeiliSearchConfig:
    """Configuration for Meilisearch integration."""

    url: str = "http://localhost:7700"
    api_key: str = ""
    index_prefix: str = ""
    timeout: int = 10
    batch_size: int = 1000

    # Search settings
    default_limit: int = 20
    default_offset: int = 0

    # Index settings
    searchable_attributes: list = field(default_factory=lambda: ["chunk_text", "filename"])
    filterable_attributes: list = field(
        default_factory=lambda: ["file_id", "project_id", "chunk_number", "pages"]
    )
    sortable_attributes: list = field(default_factory=lambda: ["chunk_number"])

    @classmethod
    def from_env(cls, prefix: str = "MEILISEARCH_") -> "MeiliSearchConfig":
        """
        Load configuration from environment variables.

        Args:
            prefix: Prefix for environment variables

        Returns:
            MeiliSearchConfig instance with values from environment
        """
        config_dict = {}

        # Simple string/int fields
        simple_fields = {
            "url": str,
            "api_key": str,
            "index_prefix": str,
            "timeout": int,
            "batch_size": int,
            "default_limit": int,
            "default_offset": int,
        }

        for field_name, field_type in simple_fields.items():
            env_var = f"{prefix}{field_name.upper()}"
            env_value = os.getenv(env_var)

            if env_value is not None:
                if field_type == int:
                    config_dict[field_name] = int(env_value)
                else:
                    config_dict[field_name] = env_value

        # List fields (JSON encoded)
        for list_field in ["searchable_attributes", "filterable_attributes", "sortable_attributes"]:
            env_var = f"{prefix}{list_field.upper()}"
            env_value = os.getenv(env_var)

            if env_value is not None:
                try:
                    config_dict[list_field] = json.loads(env_value)
                except json.JSONDecodeError:
                    pass  # Use default

        return cls(**config_dict)

    @classmethod
    def from_file(cls, path: str) -> "MeiliSearchConfig":
        """Load configuration from JSON file."""
        config_path = Path(path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(config_path) as f:
            config_dict = json.load(f)

        return cls(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)


# Default configurations
DEFAULT_PROCESSOR_CONFIG = ProcessorConfig()
DEFAULT_MEILISEARCH_CONFIG = MeiliSearchConfig()
