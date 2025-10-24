"""
Tests for configuration management.
"""

import json

import pytest

from docprocessor.config import (
    DEFAULT_MEILISEARCH_CONFIG,
    DEFAULT_PROCESSOR_CONFIG,
    MeiliSearchConfig,
    ProcessorConfig,
)


class TestProcessorConfig:
    """Tests for ProcessorConfig class."""

    def test_default_initialization(self):
        """Test creating ProcessorConfig with defaults."""
        config = ProcessorConfig()

        assert config.ocr_enabled is True
        assert config.chunk_size == 512
        assert config.chunk_overlap == 50
        assert config.min_chunk_size == 100
        assert config.max_chunk_size == 2000
        assert config.summary_target_words == 500
        assert config.llm_temperature == 0.3
        assert config.max_retries == 3
        assert config.timeout == 300
        assert config.log_level == "INFO"

    def test_custom_initialization(self):
        """Test creating ProcessorConfig with custom values."""
        config = ProcessorConfig(
            ocr_enabled=False,
            chunk_size=1024,
            chunk_overlap=100,
            summary_target_words=1000,
            llm_temperature=0.7,
        )

        assert config.ocr_enabled is False
        assert config.chunk_size == 1024
        assert config.chunk_overlap == 100
        assert config.summary_target_words == 1000
        assert config.llm_temperature == 0.7

    def test_from_env_basic(self, monkeypatch):
        """Test loading configuration from environment variables."""
        monkeypatch.setenv("DOCPROCESSOR_CHUNK_SIZE", "1024")
        monkeypatch.setenv("DOCPROCESSOR_CHUNK_OVERLAP", "128")
        monkeypatch.setenv("DOCPROCESSOR_OCR_ENABLED", "false")
        monkeypatch.setenv("DOCPROCESSOR_LLM_TEMPERATURE", "0.7")

        config = ProcessorConfig.from_env()

        assert config.chunk_size == 1024
        assert config.chunk_overlap == 128
        assert config.ocr_enabled is False
        assert config.llm_temperature == 0.7

    def test_from_env_bool_values(self, monkeypatch):
        """Test boolean environment variable parsing."""
        # Test various truthy values
        monkeypatch.setenv("DOCPROCESSOR_OCR_ENABLED", "true")
        config1 = ProcessorConfig.from_env()
        assert config1.ocr_enabled is True

        monkeypatch.setenv("DOCPROCESSOR_OCR_ENABLED", "1")
        config2 = ProcessorConfig.from_env()
        assert config2.ocr_enabled is True

        monkeypatch.setenv("DOCPROCESSOR_OCR_ENABLED", "yes")
        config3 = ProcessorConfig.from_env()
        assert config3.ocr_enabled is True

        # Test falsy values
        monkeypatch.setenv("DOCPROCESSOR_OCR_ENABLED", "false")
        config4 = ProcessorConfig.from_env()
        assert config4.ocr_enabled is False

        monkeypatch.setenv("DOCPROCESSOR_OCR_ENABLED", "0")
        config5 = ProcessorConfig.from_env()
        assert config5.ocr_enabled is False

    def test_from_env_custom_prefix(self, monkeypatch):
        """Test loading with custom environment variable prefix."""
        monkeypatch.setenv("CUSTOM_CHUNK_SIZE", "2048")

        config = ProcessorConfig.from_env(prefix="CUSTOM_")

        assert config.chunk_size == 2048

    def test_from_file(self, tmp_path):
        """Test loading configuration from JSON file."""
        config_file = tmp_path / "config.json"
        config_data = {
            "ocr_enabled": False,
            "chunk_size": 1024,
            "chunk_overlap": 100,
            "summary_target_words": 1000,
            "llm_temperature": 0.7,
        }

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        config = ProcessorConfig.from_file(str(config_file))

        assert config.ocr_enabled is False
        assert config.chunk_size == 1024
        assert config.chunk_overlap == 100
        assert config.summary_target_words == 1000
        assert config.llm_temperature == 0.7

    def test_from_file_not_found(self):
        """Test loading from non-existent file raises error."""
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            ProcessorConfig.from_file("/nonexistent/config.json")

    def test_from_file_invalid_json(self, tmp_path):
        """Test loading invalid JSON raises error."""
        config_file = tmp_path / "bad_config.json"
        config_file.write_text("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            ProcessorConfig.from_file(str(config_file))

    def test_to_file(self, tmp_path):
        """Test saving configuration to JSON file."""
        config = ProcessorConfig(chunk_size=1024, chunk_overlap=100, ocr_enabled=False)

        config_file = tmp_path / "output_config.json"
        config.to_file(str(config_file))

        assert config_file.exists()

        # Load and verify
        with open(config_file) as f:
            loaded_data = json.load(f)

        assert loaded_data["chunk_size"] == 1024
        assert loaded_data["chunk_overlap"] == 100
        assert loaded_data["ocr_enabled"] is False

    def test_to_dict(self):
        """Test converting configuration to dictionary."""
        config = ProcessorConfig(chunk_size=1024, ocr_enabled=False)

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["chunk_size"] == 1024
        assert config_dict["ocr_enabled"] is False
        assert "chunk_overlap" in config_dict

    def test_update(self):
        """Test updating configuration values."""
        config = ProcessorConfig(chunk_size=512)

        updated = config.update(chunk_size=1024, chunk_overlap=200)

        # Original unchanged
        assert config.chunk_size == 512

        # New instance has updates
        assert updated.chunk_size == 1024
        assert updated.chunk_overlap == 200

    def test_validate_valid_config(self):
        """Test validation passes for valid configuration."""
        config = ProcessorConfig()

        # Should not raise
        config.validate()

    def test_validate_chunk_size_negative(self):
        """Test validation fails for negative chunk_size."""
        config = ProcessorConfig(chunk_size=-100)

        with pytest.raises(ValueError, match="chunk_size must be positive"):
            config.validate()

    def test_validate_chunk_overlap_negative(self):
        """Test validation fails for negative chunk_overlap."""
        config = ProcessorConfig(chunk_overlap=-50)

        with pytest.raises(ValueError, match="chunk_overlap cannot be negative"):
            config.validate()

    def test_validate_chunk_overlap_too_large(self):
        """Test validation fails when chunk_overlap >= chunk_size."""
        config = ProcessorConfig(chunk_size=512, chunk_overlap=512)

        with pytest.raises(ValueError, match="chunk_overlap must be less than chunk_size"):
            config.validate()

    def test_validate_min_chunk_size_invalid(self):
        """Test validation fails for invalid min_chunk_size."""
        config = ProcessorConfig(min_chunk_size=0)

        with pytest.raises(ValueError, match="min_chunk_size must be positive"):
            config.validate()

    def test_validate_max_chunk_size_too_small(self):
        """Test validation fails when max_chunk_size <= min_chunk_size."""
        config = ProcessorConfig(min_chunk_size=500, max_chunk_size=400)

        with pytest.raises(ValueError, match="max_chunk_size must be greater than min_chunk_size"):
            config.validate()

    def test_validate_summary_target_words_invalid(self):
        """Test validation fails for invalid summary_target_words."""
        config = ProcessorConfig(summary_target_words=-100)

        with pytest.raises(ValueError, match="summary_target_words must be positive"):
            config.validate()

    def test_validate_llm_temperature_out_of_range(self):
        """Test validation fails for temperature outside [0.0, 2.0]."""
        config1 = ProcessorConfig(llm_temperature=-0.1)
        with pytest.raises(ValueError, match="llm_temperature must be between"):
            config1.validate()

        config2 = ProcessorConfig(llm_temperature=2.5)
        with pytest.raises(ValueError, match="llm_temperature must be between"):
            config2.validate()

    def test_validate_max_retries_negative(self):
        """Test validation fails for negative max_retries."""
        config = ProcessorConfig(max_retries=-1)

        with pytest.raises(ValueError, match="max_retries cannot be negative"):
            config.validate()

    def test_validate_timeout_invalid(self):
        """Test validation fails for non-positive timeout."""
        config = ProcessorConfig(timeout=0)

        with pytest.raises(ValueError, match="timeout must be positive"):
            config.validate()

    def test_validate_log_level_invalid(self):
        """Test validation fails for invalid log level."""
        config = ProcessorConfig(log_level="INVALID")

        with pytest.raises(ValueError, match="log_level must be one of"):
            config.validate()

    def test_default_config_constant(self):
        """Test DEFAULT_PROCESSOR_CONFIG is accessible."""
        assert isinstance(DEFAULT_PROCESSOR_CONFIG, ProcessorConfig)
        assert DEFAULT_PROCESSOR_CONFIG.chunk_size == 512


class TestMeiliSearchConfig:
    """Tests for MeiliSearchConfig class."""

    def test_default_initialization(self):
        """Test creating MeiliSearchConfig with defaults."""
        config = MeiliSearchConfig()

        assert config.url == "http://localhost:7700"
        assert config.api_key == ""
        assert config.index_prefix == ""
        assert config.timeout == 10
        assert config.batch_size == 1000
        assert config.default_limit == 20
        assert config.default_offset == 0
        assert "chunk_text" in config.searchable_attributes
        assert "file_id" in config.filterable_attributes
        assert "chunk_number" in config.sortable_attributes

    def test_custom_initialization(self):
        """Test creating MeiliSearchConfig with custom values."""
        config = MeiliSearchConfig(
            url="http://search.example.com",
            api_key="secret_key",
            index_prefix="prod_",
            timeout=30,
            batch_size=500,
        )

        assert config.url == "http://search.example.com"
        assert config.api_key == "secret_key"
        assert config.index_prefix == "prod_"
        assert config.timeout == 30
        assert config.batch_size == 500

    def test_from_env_basic(self, monkeypatch):
        """Test loading configuration from environment variables."""
        monkeypatch.setenv("MEILISEARCH_URL", "http://prod.example.com")
        monkeypatch.setenv("MEILISEARCH_API_KEY", "prod_key")
        monkeypatch.setenv("MEILISEARCH_INDEX_PREFIX", "prod_")
        monkeypatch.setenv("MEILISEARCH_TIMEOUT", "30")
        monkeypatch.setenv("MEILISEARCH_BATCH_SIZE", "2000")

        config = MeiliSearchConfig.from_env()

        assert config.url == "http://prod.example.com"
        assert config.api_key == "prod_key"
        assert config.index_prefix == "prod_"
        assert config.timeout == 30
        assert config.batch_size == 2000

    def test_from_env_list_attributes(self, monkeypatch):
        """Test loading list attributes from environment."""
        monkeypatch.setenv("MEILISEARCH_SEARCHABLE_ATTRIBUTES", '["title", "content"]')
        monkeypatch.setenv("MEILISEARCH_FILTERABLE_ATTRIBUTES", '["category", "date"]')

        config = MeiliSearchConfig.from_env()

        assert config.searchable_attributes == ["title", "content"]
        assert config.filterable_attributes == ["category", "date"]

    def test_from_env_invalid_json_list(self, monkeypatch):
        """Test invalid JSON in list field falls back to default."""
        monkeypatch.setenv("MEILISEARCH_SEARCHABLE_ATTRIBUTES", "invalid json")

        config = MeiliSearchConfig.from_env()

        # Should use default value
        assert "chunk_text" in config.searchable_attributes

    def test_from_env_custom_prefix(self, monkeypatch):
        """Test loading with custom environment variable prefix."""
        monkeypatch.setenv("SEARCH_URL", "http://custom.example.com")

        config = MeiliSearchConfig.from_env(prefix="SEARCH_")

        assert config.url == "http://custom.example.com"

    def test_from_file(self, tmp_path):
        """Test loading configuration from JSON file."""
        config_file = tmp_path / "meilisearch_config.json"
        config_data = {
            "url": "http://prod.example.com",
            "api_key": "secret",
            "index_prefix": "prod_",
            "timeout": 30,
            "batch_size": 2000,
        }

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        config = MeiliSearchConfig.from_file(str(config_file))

        assert config.url == "http://prod.example.com"
        assert config.api_key == "secret"
        assert config.index_prefix == "prod_"
        assert config.timeout == 30
        assert config.batch_size == 2000

    def test_from_file_not_found(self):
        """Test loading from non-existent file raises error."""
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            MeiliSearchConfig.from_file("/nonexistent/config.json")

    def test_to_dict(self):
        """Test converting configuration to dictionary."""
        config = MeiliSearchConfig(url="http://example.com", api_key="secret", index_prefix="test_")

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["url"] == "http://example.com"
        assert config_dict["api_key"] == "secret"
        assert config_dict["index_prefix"] == "test_"
        assert "timeout" in config_dict
        assert "searchable_attributes" in config_dict

    def test_default_config_constant(self):
        """Test DEFAULT_MEILISEARCH_CONFIG is accessible."""
        assert isinstance(DEFAULT_MEILISEARCH_CONFIG, MeiliSearchConfig)
        assert DEFAULT_MEILISEARCH_CONFIG.url == "http://localhost:7700"
