# backend/app/services/search/chunker.py

"""
Document chunking service for semantic search.

Chunks documents into appropriately-sized segments for embedding and search.
"""

import logging
import re
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Represents a single chunk of a document."""

    chunk_id: str
    file_id: str
    output_id: str
    project_id: int
    filename: str
    chunk_number: int
    total_chunks: int
    chunk_text: str
    token_count: int
    pages: List[int]
    metadata: Dict[str, Any]


class DocumentChunker:
    """
    Chunks documents using semantic splitting strategies.

    Uses langchain's RecursiveCharacterTextSplitter for intelligent chunking
    that respects sentence and paragraph boundaries.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50, min_chunk_size: int = 100):
        """
        Initialize the chunker.

        Args:
            chunk_size: Target chunk size in tokens (default: 512)
            chunk_overlap: Overlap between chunks in tokens (default: 50)
            min_chunk_size: Minimum chunk size in tokens (default: 100)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

        # Initialize tokenizer for counting
        try:
            import tiktoken

            self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
        except ImportError:
            logger.warning("tiktoken not installed, using character-based estimation")
            self.tokenizer = None

    def chunk_document(
        self,
        text: str,
        file_id: str,
        output_id: str,
        project_id: int,
        filename: str,
        extraction_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """
        Chunk a document into semantic segments.

        Args:
            text: The full document text
            file_id: UUID of the output file
            output_id: UUID of the output
            project_id: ID of the project
            filename: Name of the file
            extraction_metadata: Optional metadata from content extraction

        Returns:
            List of DocumentChunk objects
        """
        if not text or len(text.strip()) < self.min_chunk_size:
            logger.warning(f"Document too short to chunk: {len(text)} characters")
            return []

        try:
            # Use langchain for semantic chunking
            chunks_text = self._split_text_semantic(text)

            # Create chunk objects
            chunks = []
            for i, chunk_text in enumerate(chunks_text):
                # Skip very small chunks
                token_count = self._count_tokens(chunk_text)
                if token_count < self.min_chunk_size:
                    logger.debug(f"Skipping small chunk {i}: {token_count} tokens")
                    continue

                # Extract page numbers from chunk (if PDF format markers present)
                pages = self._extract_page_numbers(chunk_text)

                chunk = DocumentChunk(
                    chunk_id=str(uuid.uuid4()),
                    file_id=file_id,
                    output_id=output_id,
                    project_id=project_id,
                    filename=filename,
                    chunk_number=len(chunks),
                    total_chunks=0,  # Will be set after all chunks processed
                    chunk_text=self._clean_chunk_text(chunk_text),
                    token_count=token_count,
                    pages=pages,
                    metadata=extraction_metadata or {},
                )
                chunks.append(chunk)

            # Update total_chunks for all chunks
            total = len(chunks)
            for chunk in chunks:
                chunk.total_chunks = total

            logger.info(f"Created {len(chunks)} chunks for {filename}")
            return chunks

        except Exception as e:
            logger.error(f"Error chunking document: {e}")
            raise

    def _split_text_semantic(self, text: str) -> List[str]:
        """Split text using semantic boundaries."""
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter

            # Convert token-based sizes to character-based (rough approximation)
            char_chunk_size = self.chunk_size * 4  # ~4 chars per token
            char_overlap = self.chunk_overlap * 4

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=char_chunk_size,
                chunk_overlap=char_overlap,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""],
                is_separator_regex=False,
            )

            chunks = splitter.split_text(text)
            return chunks

        except ImportError:
            logger.warning("langchain-text-splitters not installed, using fallback")
            return self._split_text_fallback(text)

    def _split_text_fallback(self, text: str) -> List[str]:
        """
        Fallback chunking strategy using simple boundaries.

        Used when langchain is not available.
        """
        char_chunk_size = self.chunk_size * 4
        char_overlap = self.chunk_overlap * 4

        chunks = []
        start = 0

        while start < len(text):
            # Get chunk end position
            end = start + char_chunk_size

            # If not at end, try to break at sentence boundary
            if end < len(text):
                # Look for sentence break within last 20% of chunk
                search_start = end - int(char_chunk_size * 0.2)
                sentence_end = text.rfind(". ", search_start, end)

                if sentence_end > start:
                    end = sentence_end + 1

            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk)

            # Move start position with overlap
            start = end - char_overlap

        return chunks

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                logger.warning(f"Token counting failed: {e}, using estimation")

        # Fallback: estimate 4 characters per token
        return len(text) // 4

    def _extract_page_numbers(self, text: str) -> List[int]:
        """
        Extract page numbers from PDF format markers in text.

        Looks for <page_N> markers inserted by PDF extraction.
        """
        page_pattern = r"<page_(\d+)>"
        matches = re.findall(page_pattern, text)

        if matches:
            return sorted(set(int(m) for m in matches))

        return []

    def _clean_chunk_text(self, text: str) -> str:
        """
        Clean chunk text by removing format markers.

        Removes PDF page markers and other extraction artifacts.
        """
        # Remove page markers
        text = re.sub(r"<page_\d+>", "", text)

        # Remove column markers
        text = re.sub(r"<col>(.*?)</col>", r"\1", text)

        # Clean up whitespace
        text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)  # Max 2 newlines
        text = text.strip()

        return text

    def to_search_document(self, chunk: DocumentChunk) -> Dict[str, Any]:
        """
        Convert a DocumentChunk to a Meilisearch document format.

        Args:
            chunk: The chunk to convert

        Returns:
            Dictionary ready for Meilisearch indexing
        """
        return {
            "id": chunk.chunk_id,  # Use chunk_id as primary key
            "file_id": chunk.file_id,
            "output_id": chunk.output_id,
            "project_id": chunk.project_id,
            "filename": chunk.filename,
            "chunk_number": chunk.chunk_number,
            "total_chunks": chunk.total_chunks,
            "chunk_text": chunk.chunk_text,
            "chunk_preview": chunk.chunk_text[:200],  # First 200 chars
            "token_count": chunk.token_count,
            "pages": chunk.pages,
            "metadata": chunk.metadata,
        }


# Global instance
document_chunker = DocumentChunker()
