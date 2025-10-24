"""
Document Processor Library

A Python library for processing documents with OCR, chunking, and summarization capabilities.
Designed for semantic search and document analysis workflows.
"""

__version__ = "1.0.0"

from .core.chunker import DocumentChunk
from .integrations.meilisearch_indexer import MeiliSearchIndexer
from .processor import DocumentProcessor, ProcessResult

__all__ = [
    "DocumentProcessor",
    "ProcessResult",
    "MeiliSearchIndexer",
    "DocumentChunk",
]
