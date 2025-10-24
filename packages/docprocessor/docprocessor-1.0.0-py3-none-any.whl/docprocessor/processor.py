# docprocessor/processor.py

"""
Main DocumentProcessor API.

Provides a simple interface for document processing operations.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .core.chunker import DocumentChunk, DocumentChunker
from .core.extractor import ContentExtractionError, ContentExtractor
from .core.summarizer import DocumentSummarizer

logger = logging.getLogger(__name__)


@dataclass
class ProcessResult:
    """Result of document processing."""

    text: str = ""  # Add default empty string
    chunks: List[DocumentChunk] = field(default_factory=list)
    summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    page_count: int = 1
    chunk_count: int = 0


class DocumentProcessor:
    """
    Main document processing class.

    Provides a unified interface for extracting text, chunking, and summarizing documents.
    """

    def __init__(
        self,
        ocr_enabled: bool = True,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100,
        summary_target_words: int = 500,
        llm_client: Optional[Any] = None,
        llm_temperature: float = 0.3,
    ):
        """
        Initialize the document processor.

        Args:
            ocr_enabled: Enable OCR for PDFs and images (default: True)
            chunk_size: Target chunk size in tokens (default: 512)
            chunk_overlap: Chunk overlap in tokens (default: 50)
            min_chunk_size: Minimum chunk size in tokens (default: 100)
            summary_target_words: Target summary length (default: 500)
            llm_client: Optional LLM client for summarization
            llm_temperature: Temperature for LLM summarization (default: 0.3)
        """
        self.extractor = ContentExtractor()
        self.chunker = DocumentChunker(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap, min_chunk_size=min_chunk_size
        )
        self.summarizer = DocumentSummarizer(
            llm_client=llm_client, target_words=summary_target_words, temperature=llm_temperature
        )
        self.ocr_enabled = ocr_enabled

    def process(
        self,
        file_path: str | Path,
        extract_text: bool = True,
        chunk: bool = True,
        summarize: bool = False,
        file_id: Optional[str] = None,
        output_id: Optional[str] = None,
        project_id: Optional[int] = None,
        extraction_metadata: Optional[Dict[str, Any]] = None,
    ) -> ProcessResult:
        """
        Process a document with extraction, chunking, and optional summarization.

        Args:
            file_path: Path to the document file
            extract_text: Extract text from document (default: True)
            chunk: Chunk the extracted text (default: True)
            summarize: Generate a summary (default: False, requires llm_client)
            file_id: Optional file identifier for chunks
            output_id: Optional output identifier for chunks
            project_id: Optional project identifier for chunks
            extraction_metadata: Optional metadata to attach to chunks

        Returns:
            ProcessResult with text, chunks, summary, and metadata
        """
        file_path = Path(file_path)
        result = ProcessResult()

        # Extract text
        if extract_text:
            try:
                extraction = self.extractor.extract(file_path)
                result.text = extraction["text"]
                result.page_count = extraction.get("page_count", 1)
                result.metadata = extraction.get("metadata", {})
                logger.info(f"Extracted {len(result.text)} characters from {file_path.name}")
            except ContentExtractionError as e:
                logger.error(f"Text extraction failed: {e}")
                raise

        # Chunk text
        if chunk and result.text:
            try:
                # Generate IDs if not provided
                file_id = file_id or str(file_path)
                output_id = output_id or "unknown"
                project_id = project_id or 0

                chunks = self.chunker.chunk_document(
                    text=result.text,
                    file_id=file_id,
                    output_id=output_id,
                    project_id=project_id,
                    filename=file_path.name,
                    extraction_metadata=extraction_metadata or result.metadata,
                )
                result.chunks = chunks
                result.chunk_count = len(chunks)
                logger.info(f"Created {len(chunks)} chunks from {file_path.name}")
            except Exception as e:
                logger.error(f"Chunking failed: {e}")
                raise

        # Summarize
        if summarize and result.text:
            try:
                summary = self.summarizer.summarize_with_fallback(
                    text=result.text, filename=file_path.name, metadata=result.metadata
                )
                result.summary = summary
                logger.info(f"Generated summary for {file_path.name}")
            except Exception as e:
                logger.warning(f"Summarization failed, using fallback: {e}")
                result.summary = self.summarizer._create_fallback_summary(result.text)

        return result

    def extract_text(self, file_path: str | Path) -> Dict[str, Any]:
        """
        Extract text from a document.

        Args:
            file_path: Path to the document file

        Returns:
            Dictionary with text, page_count, and metadata
        """
        return self.extractor.extract(Path(file_path))

    def chunk_text(
        self,
        text: str,
        file_id: str = "unknown",
        output_id: str = "unknown",
        project_id: int = 0,
        filename: str = "document.txt",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """
        Chunk text into semantic segments.

        Args:
            text: Text to chunk
            file_id: File identifier
            output_id: Output identifier
            project_id: Project identifier
            filename: Name of the file
            metadata: Optional metadata

        Returns:
            List of DocumentChunk objects
        """
        return self.chunker.chunk_document(
            text=text,
            file_id=file_id,
            output_id=output_id,
            project_id=project_id,
            filename=filename,
            extraction_metadata=metadata,
        )

    def summarize_text(
        self, text: str, filename: str = "document.txt", use_fallback: bool = True
    ) -> str:
        """
        Generate a summary of text.

        Args:
            text: Text to summarize
            filename: Name of the file
            use_fallback: Use fallback truncation if LLM fails

        Returns:
            Summary text
        """
        if use_fallback:
            return self.summarizer.summarize_with_fallback(text, filename)
        else:
            return self.summarizer.summarize(text, filename)

    def chunks_to_search_documents(self, chunks: List[DocumentChunk]) -> List[Dict[str, Any]]:
        """
        Convert chunks to Meilisearch document format.

        Args:
            chunks: List of DocumentChunk objects

        Returns:
            List of dictionaries ready for indexing
        """
        return [self.chunker.to_search_document(chunk) for chunk in chunks]
