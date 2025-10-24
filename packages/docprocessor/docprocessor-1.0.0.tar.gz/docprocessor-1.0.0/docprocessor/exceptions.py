"""
Custom exceptions for docprocessor library.

This module defines specific exception classes for different error scenarios,
providing better error handling and debugging capabilities.
"""


class DocProcessorError(Exception):
    """Base exception for all docprocessor errors."""

    pass


class ExtractionError(DocProcessorError):
    """Raised when text extraction fails."""

    pass


class ChunkingError(DocProcessorError):
    """Raised when text chunking fails."""

    pass


class SummarizationError(DocProcessorError):
    """Raised when document summarization fails."""

    pass


class IndexingError(DocProcessorError):
    """Raised when indexing to Meilisearch fails."""

    pass


class ConfigurationError(DocProcessorError):
    """Raised when there's a configuration problem."""

    pass


class ValidationError(DocProcessorError):
    """Raised when input validation fails."""

    pass


class OCRError(ExtractionError):
    """Raised when OCR processing fails."""

    pass


class PDFProcessingError(ExtractionError):
    """Raised when PDF processing fails."""

    pass


class LLMError(SummarizationError):
    """Raised when LLM API calls fail."""

    pass


class SearchError(IndexingError):
    """Raised when search operations fail."""

    pass
