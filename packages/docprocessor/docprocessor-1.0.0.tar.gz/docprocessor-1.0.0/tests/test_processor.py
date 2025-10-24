"""
Tests for DocumentProcessor main API.
"""

import pytest

from docprocessor import DocumentProcessor, ProcessResult
from docprocessor.core.extractor import ContentExtractionError


class TestDocumentProcessor:
    """Tests for DocumentProcessor class."""

    def test_init_default_params(self):
        """Test processor initialization with default parameters."""
        processor = DocumentProcessor()

        assert processor.ocr_enabled is True
        assert processor.chunker.chunk_size == 512
        assert processor.chunker.chunk_overlap == 50
        assert processor.summarizer.target_words == 500

    def test_init_custom_params(self):
        """Test processor initialization with custom parameters."""
        processor = DocumentProcessor(
            ocr_enabled=False, chunk_size=1024, chunk_overlap=100, summary_target_words=300
        )

        assert processor.ocr_enabled is False
        assert processor.chunker.chunk_size == 1024
        assert processor.chunker.chunk_overlap == 100
        assert processor.summarizer.target_words == 300

    def test_process_text_file_extract_only(self, sample_txt_file):
        """Test processing text file with extraction only."""
        processor = DocumentProcessor()

        result = processor.process(
            file_path=sample_txt_file, extract_text=True, chunk=False, summarize=False
        )

        assert isinstance(result, ProcessResult)
        assert len(result.text) > 0
        assert result.page_count == 1
        assert len(result.chunks) == 0
        assert result.summary is None

    def test_process_text_file_with_chunking(self, sample_txt_file):
        """Test processing text file with chunking."""
        processor = DocumentProcessor()

        result = processor.process(
            file_path=sample_txt_file, extract_text=True, chunk=True, summarize=False
        )

        assert isinstance(result, ProcessResult)
        assert len(result.text) > 0
        assert len(result.chunks) > 0
        assert result.chunk_count == len(result.chunks)
        assert result.summary is None

    def test_process_with_summarization(self, sample_txt_file, mock_llm_client):
        """Test processing with LLM summarization."""
        processor = DocumentProcessor(llm_client=mock_llm_client)

        result = processor.process(
            file_path=sample_txt_file, extract_text=True, chunk=True, summarize=True
        )

        assert isinstance(result, ProcessResult)
        assert len(result.text) > 0
        assert len(result.chunks) > 0
        assert result.summary is not None
        assert "mock summary" in result.summary.lower()

    def test_process_with_metadata(self, sample_txt_file):
        """Test processing with custom metadata."""
        processor = DocumentProcessor()

        result = processor.process(
            file_path=sample_txt_file,
            extract_text=True,
            chunk=True,
            file_id="test-file-123",
            output_id="test-output-456",
            project_id=789,
        )

        assert len(result.chunks) > 0
        for chunk in result.chunks:
            assert chunk.file_id == "test-file-123"
            assert chunk.output_id == "test-output-456"
            assert chunk.project_id == 789

    def test_process_nonexistent_file(self):
        """Test processing non-existent file raises error."""
        processor = DocumentProcessor()

        with pytest.raises(ContentExtractionError):
            processor.process(file_path="/nonexistent/file.txt", extract_text=True)

    def test_extract_text_method(self, sample_txt_file):
        """Test extract_text convenience method."""
        processor = DocumentProcessor()

        extraction = processor.extract_text(sample_txt_file)

        assert isinstance(extraction, dict)
        assert "text" in extraction
        assert "page_count" in extraction
        assert "metadata" in extraction
        assert len(extraction["text"]) > 0

    def test_chunk_text_method(self, sample_text):
        """Test chunk_text convenience method."""
        processor = DocumentProcessor()

        chunks = processor.chunk_text(text=sample_text, file_id="test-123", filename="test.txt")

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.file_id == "test-123"
            assert chunk.filename == "test.txt"
            assert len(chunk.chunk_text) > 0

    def test_summarize_text_method(self, sample_text, mock_llm_client):
        """Test summarize_text convenience method."""
        processor = DocumentProcessor(llm_client=mock_llm_client)

        summary = processor.summarize_text(text=sample_text, filename="test.txt")

        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_summarize_text_fallback(self, sample_text):
        """Test summarize_text with fallback when no LLM client."""
        processor = DocumentProcessor()  # No LLM client

        summary = processor.summarize_text(text=sample_text, filename="test.txt", use_fallback=True)

        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_chunks_to_search_documents(self, sample_txt_file):
        """Test converting chunks to search document format."""
        processor = DocumentProcessor()

        result = processor.process(file_path=sample_txt_file, extract_text=True, chunk=True)

        search_docs = processor.chunks_to_search_documents(result.chunks)

        assert len(search_docs) == len(result.chunks)
        for doc in search_docs:
            assert "id" in doc
            assert "chunk_text" in doc
            assert "file_id" in doc
            assert "chunk_number" in doc

    def test_process_empty_file(self, tmp_path):
        """Test processing empty file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        processor = DocumentProcessor()

        result = processor.process(file_path=empty_file, extract_text=True, chunk=True)

        assert result.text == ""
        assert len(result.chunks) == 0

    def test_process_result_dataclass(self):
        """Test ProcessResult dataclass initialization."""
        result = ProcessResult(
            text="test text",
            chunks=[],
            summary="test summary",
            metadata={"key": "value"},
            page_count=5,
            chunk_count=10,
        )

        assert result.text == "test text"
        assert result.summary == "test summary"
        assert result.page_count == 5
        assert result.chunk_count == 10
        assert result.metadata["key"] == "value"

    def test_process_result_defaults(self):
        """Test ProcessResult default values."""
        result = ProcessResult()

        assert result.text == ""
        assert result.chunks == []
        assert result.summary is None
        assert result.metadata == {}
        assert result.page_count == 1
        assert result.chunk_count == 0
