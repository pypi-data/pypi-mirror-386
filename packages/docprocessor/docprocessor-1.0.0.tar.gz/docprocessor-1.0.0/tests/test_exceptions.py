"""
Tests for custom exception classes.
"""

import pytest

from docprocessor.exceptions import (
    ChunkingError,
    ConfigurationError,
    DocProcessorError,
    ExtractionError,
    IndexingError,
    LLMError,
    OCRError,
    PDFProcessingError,
    SearchError,
    SummarizationError,
    ValidationError,
)


class TestBaseException:
    """Tests for base DocProcessorError exception."""

    def test_base_exception_creation(self):
        """Test creating base exception with message."""
        error = DocProcessorError("Test error message")

        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_base_exception_raising(self):
        """Test raising base exception."""
        with pytest.raises(DocProcessorError, match="Test error"):
            raise DocProcessorError("Test error")

    def test_base_exception_catching(self):
        """Test catching base exception."""
        try:
            raise DocProcessorError("Caught error")
        except DocProcessorError as e:
            assert str(e) == "Caught error"


class TestExtractionError:
    """Tests for ExtractionError exception."""

    def test_extraction_error_creation(self):
        """Test creating ExtractionError."""
        error = ExtractionError("Failed to extract text")

        assert str(error) == "Failed to extract text"
        assert isinstance(error, DocProcessorError)
        assert isinstance(error, Exception)

    def test_extraction_error_inheritance(self):
        """Test ExtractionError inherits from DocProcessorError."""
        with pytest.raises(DocProcessorError):
            raise ExtractionError("Test")


class TestChunkingError:
    """Tests for ChunkingError exception."""

    def test_chunking_error_creation(self):
        """Test creating ChunkingError."""
        error = ChunkingError("Failed to chunk text")

        assert str(error) == "Failed to chunk text"
        assert isinstance(error, DocProcessorError)

    def test_chunking_error_raising(self):
        """Test raising ChunkingError."""
        with pytest.raises(ChunkingError, match="Chunking failed"):
            raise ChunkingError("Chunking failed")


class TestSummarizationError:
    """Tests for SummarizationError exception."""

    def test_summarization_error_creation(self):
        """Test creating SummarizationError."""
        error = SummarizationError("Failed to summarize")

        assert str(error) == "Failed to summarize"
        assert isinstance(error, DocProcessorError)

    def test_summarization_error_inheritance(self):
        """Test SummarizationError can be caught as base exception."""
        with pytest.raises(DocProcessorError):
            raise SummarizationError("Test")


class TestIndexingError:
    """Tests for IndexingError exception."""

    def test_indexing_error_creation(self):
        """Test creating IndexingError."""
        error = IndexingError("Failed to index")

        assert str(error) == "Failed to index"
        assert isinstance(error, DocProcessorError)

    def test_indexing_error_raising(self):
        """Test raising IndexingError."""
        with pytest.raises(IndexingError):
            raise IndexingError("Indexing failed")


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_configuration_error_creation(self):
        """Test creating ConfigurationError."""
        error = ConfigurationError("Invalid configuration")

        assert str(error) == "Invalid configuration"
        assert isinstance(error, DocProcessorError)

    def test_configuration_error_raising(self):
        """Test raising ConfigurationError."""
        with pytest.raises(ConfigurationError, match="Config error"):
            raise ConfigurationError("Config error")


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_validation_error_creation(self):
        """Test creating ValidationError."""
        error = ValidationError("Validation failed")

        assert str(error) == "Validation failed"
        assert isinstance(error, DocProcessorError)

    def test_validation_error_raising(self):
        """Test raising ValidationError."""
        with pytest.raises(ValidationError):
            raise ValidationError("Invalid input")


class TestOCRError:
    """Tests for OCRError exception."""

    def test_ocr_error_creation(self):
        """Test creating OCRError."""
        error = OCRError("OCR processing failed")

        assert str(error) == "OCR processing failed"
        assert isinstance(error, ExtractionError)
        assert isinstance(error, DocProcessorError)

    def test_ocr_error_inheritance(self):
        """Test OCRError inherits from ExtractionError."""
        with pytest.raises(ExtractionError):
            raise OCRError("Test")


class TestPDFProcessingError:
    """Tests for PDFProcessingError exception."""

    def test_pdf_processing_error_creation(self):
        """Test creating PDFProcessingError."""
        error = PDFProcessingError("PDF processing failed")

        assert str(error) == "PDF processing failed"
        assert isinstance(error, ExtractionError)
        assert isinstance(error, DocProcessorError)

    def test_pdf_processing_error_raising(self):
        """Test raising PDFProcessingError."""
        with pytest.raises(PDFProcessingError, match="PDF failed"):
            raise PDFProcessingError("PDF failed")


class TestLLMError:
    """Tests for LLMError exception."""

    def test_llm_error_creation(self):
        """Test creating LLMError."""
        error = LLMError("LLM API call failed")

        assert str(error) == "LLM API call failed"
        assert isinstance(error, SummarizationError)
        assert isinstance(error, DocProcessorError)

    def test_llm_error_inheritance_chain(self):
        """Test LLMError can be caught as SummarizationError or DocProcessorError."""
        # Can catch as SummarizationError
        with pytest.raises(SummarizationError):
            raise LLMError("Test")

        # Can catch as DocProcessorError
        with pytest.raises(DocProcessorError):
            raise LLMError("Test")


class TestSearchError:
    """Tests for SearchError exception."""

    def test_search_error_creation(self):
        """Test creating SearchError."""
        error = SearchError("Search failed")

        assert str(error) == "Search failed"
        assert isinstance(error, IndexingError)
        assert isinstance(error, DocProcessorError)

    def test_search_error_inheritance(self):
        """Test SearchError inherits from IndexingError."""
        with pytest.raises(IndexingError):
            raise SearchError("Test")


class TestExceptionHierarchy:
    """Tests for exception hierarchy and relationships."""

    def test_all_exceptions_inherit_from_base(self):
        """Test all custom exceptions inherit from DocProcessorError."""
        exceptions = [
            ExtractionError,
            ChunkingError,
            SummarizationError,
            IndexingError,
            ConfigurationError,
            ValidationError,
            OCRError,
            PDFProcessingError,
            LLMError,
            SearchError,
        ]

        for exc_class in exceptions:
            assert issubclass(exc_class, DocProcessorError)
            assert issubclass(exc_class, Exception)

    def test_specific_inheritance_relationships(self):
        """Test specific inheritance relationships."""
        # OCRError and PDFProcessingError inherit from ExtractionError
        assert issubclass(OCRError, ExtractionError)
        assert issubclass(PDFProcessingError, ExtractionError)

        # LLMError inherits from SummarizationError
        assert issubclass(LLMError, SummarizationError)

        # SearchError inherits from IndexingError
        assert issubclass(SearchError, IndexingError)

    def test_catching_parent_exception(self):
        """Test catching child exception with parent exception type."""
        # OCRError can be caught as ExtractionError
        try:
            raise OCRError("Test OCR error")
        except ExtractionError as e:
            assert str(e) == "Test OCR error"

        # LLMError can be caught as SummarizationError
        try:
            raise LLMError("Test LLM error")
        except SummarizationError as e:
            assert str(e) == "Test LLM error"

        # SearchError can be caught as IndexingError
        try:
            raise SearchError("Test search error")
        except IndexingError as e:
            assert str(e) == "Test search error"

    def test_catching_base_exception_catches_all(self):
        """Test catching DocProcessorError catches all custom exceptions."""
        exceptions_to_test = [
            ExtractionError("test"),
            ChunkingError("test"),
            SummarizationError("test"),
            IndexingError("test"),
            OCRError("test"),
            LLMError("test"),
        ]

        for exc in exceptions_to_test:
            try:
                raise exc
            except DocProcessorError:
                pass  # Should catch all
