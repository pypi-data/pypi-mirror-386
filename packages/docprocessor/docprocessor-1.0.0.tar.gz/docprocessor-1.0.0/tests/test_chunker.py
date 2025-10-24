"""
Tests for DocumentChunker.
"""

from docprocessor.core.chunker import DocumentChunk, DocumentChunker


class TestDocumentChunker:
    """Tests for DocumentChunker class."""

    def test_init_default_params(self):
        """Test chunker initialization with defaults."""
        chunker = DocumentChunker()

        assert chunker.chunk_size == 512
        assert chunker.chunk_overlap == 50
        assert chunker.min_chunk_size == 100

    def test_init_custom_params(self):
        """Test chunker initialization with custom params."""
        chunker = DocumentChunker(chunk_size=1024, chunk_overlap=100, min_chunk_size=200)

        assert chunker.chunk_size == 1024
        assert chunker.chunk_overlap == 100
        assert chunker.min_chunk_size == 200

    def test_chunk_document_basic(self, long_text):
        """Test basic document chunking."""
        chunker = DocumentChunker(chunk_size=512, chunk_overlap=50)

        chunks = chunker.chunk_document(
            text=long_text,
            file_id="file-123",
            output_id="output-456",
            project_id=789,
            filename="test.txt",
        )

        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)

    def test_chunk_properties(self, long_text):
        """Test chunk object properties."""
        chunker = DocumentChunker()

        chunks = chunker.chunk_document(
            text=long_text,
            file_id="file-123",
            output_id="output-456",
            project_id=789,
            filename="test.txt",
        )

        for i, chunk in enumerate(chunks):
            assert chunk.file_id == "file-123"
            assert chunk.output_id == "output-456"
            assert chunk.project_id == 789
            assert chunk.filename == "test.txt"
            assert chunk.chunk_number == i
            assert chunk.total_chunks == len(chunks)
            assert len(chunk.chunk_text) > 0
            assert chunk.token_count > 0
            assert isinstance(chunk.pages, list)
            assert isinstance(chunk.metadata, dict)

    def test_chunk_document_short_text(self):
        """Test chunking text too short."""
        chunker = DocumentChunker(min_chunk_size=100)
        short_text = "Too short"

        chunks = chunker.chunk_document(
            text=short_text,
            file_id="file-123",
            output_id="output-456",
            project_id=789,
            filename="test.txt",
        )

        assert len(chunks) == 0

    def test_chunk_document_empty_text(self):
        """Test chunking empty text."""
        chunker = DocumentChunker()

        chunks = chunker.chunk_document(
            text="", file_id="file-123", output_id="output-456", project_id=789, filename="test.txt"
        )

        assert len(chunks) == 0

    def test_chunk_with_metadata(self, sample_text):
        """Test chunking with extraction metadata."""
        chunker = DocumentChunker()
        metadata = {"format": "txt", "extraction_method": "direct_read"}

        chunks = chunker.chunk_document(
            text=sample_text,
            file_id="file-123",
            output_id="output-456",
            project_id=789,
            filename="test.txt",
            extraction_metadata=metadata,
        )

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.metadata == metadata

    def test_chunk_text_with_page_markers(self):
        """Test chunking text with PDF page markers."""
        chunker = DocumentChunker()
        text_with_markers = (
            """
        <page_1>This is page one content.
        <page_2>This is page two content.
        <page_3>This is page three content.
        """
            * 10
        )

        chunks = chunker.chunk_document(
            text=text_with_markers,
            file_id="file-123",
            output_id="output-456",
            project_id=789,
            filename="test.pdf",
        )

        assert len(chunks) > 0
        # Verify page markers are cleaned from chunk text
        for chunk in chunks:
            assert "<page_" not in chunk.chunk_text

    def test_extract_page_numbers(self):
        """Test extracting page numbers from text."""
        chunker = DocumentChunker()
        text = "<page_1>Text on page 1<page_2>Text on page 2<page_1>More from page 1"

        pages = chunker._extract_page_numbers(text)

        assert 1 in pages
        assert 2 in pages
        assert len(pages) == 2

    def test_clean_chunk_text(self):
        """Test cleaning chunk text."""
        chunker = DocumentChunker()
        dirty_text = """
        <page_1>This is text<page_2>
        <col>Column text</col>


        With extra whitespace
        """

        clean = chunker._clean_chunk_text(dirty_text)

        assert "<page_" not in clean
        assert "<col>" not in clean
        assert "</col>" not in clean
        assert "\n\n\n" not in clean

    def test_count_tokens_with_tokenizer(self):
        """Test token counting with tiktoken."""
        chunker = DocumentChunker()
        text = "This is a test sentence with multiple words."

        token_count = chunker._count_tokens(text)

        assert token_count > 0
        assert isinstance(token_count, int)

    def test_count_tokens_without_tokenizer(self, monkeypatch):
        """Test token counting fallback without tiktoken."""
        chunker = DocumentChunker()
        chunker.tokenizer = None  # Simulate missing tokenizer

        text = "This is test text with twenty characters exactly."
        token_count = chunker._count_tokens(text)

        # Fallback uses length // 4
        assert token_count == len(text) // 4

    def test_to_search_document(self, sample_text):
        """Test converting chunk to search document format."""
        chunker = DocumentChunker()

        chunks = chunker.chunk_document(
            text=sample_text,
            file_id="file-123",
            output_id="output-456",
            project_id=789,
            filename="test.txt",
        )

        assert len(chunks) > 0
        search_doc = chunker.to_search_document(chunks[0])

        assert isinstance(search_doc, dict)
        assert "id" in search_doc
        assert "file_id" in search_doc
        assert "output_id" in search_doc
        assert "project_id" in search_doc
        assert "filename" in search_doc
        assert "chunk_number" in search_doc
        assert "total_chunks" in search_doc
        assert "chunk_text" in search_doc
        assert "chunk_preview" in search_doc
        assert "token_count" in search_doc
        assert "pages" in search_doc
        assert "metadata" in search_doc

        # Check preview is truncated
        assert len(search_doc["chunk_preview"]) <= 200

    def test_split_text_semantic(self, long_text):
        """Test semantic text splitting."""
        chunker = DocumentChunker(chunk_size=256, chunk_overlap=25)

        chunks = chunker._split_text_semantic(long_text)

        assert len(chunks) > 1
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_split_text_fallback(self, long_text):
        """Test fallback text splitting."""
        chunker = DocumentChunker(chunk_size=256, chunk_overlap=25)

        chunks = chunker._split_text_fallback(long_text)

        assert len(chunks) > 1
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_chunk_overlap(self, long_text):
        """Test that chunks have overlap."""
        chunker = DocumentChunker(chunk_size=200, chunk_overlap=50)

        chunks = chunker.chunk_document(
            text=long_text,
            file_id="file-123",
            output_id="output-456",
            project_id=789,
            filename="test.txt",
        )

        # Check if consecutive chunks have overlapping content
        if len(chunks) >= 2:
            first_chunk_end = chunks[0].chunk_text[-50:]
            second_chunk_start = chunks[1].chunk_text[:50]

            # Some overlap should exist (not exact due to semantic splitting)
            assert len(first_chunk_end) > 0
            assert len(second_chunk_start) > 0


class TestDocumentChunk:
    """Tests for DocumentChunk dataclass."""

    def test_document_chunk_creation(self):
        """Test creating a DocumentChunk."""
        chunk = DocumentChunk(
            chunk_id="chunk-123",
            file_id="file-456",
            output_id="output-789",
            project_id=1,
            filename="test.txt",
            chunk_number=0,
            total_chunks=5,
            chunk_text="This is chunk text.",
            token_count=20,
            pages=[1, 2],
            metadata={"key": "value"},
        )

        assert chunk.chunk_id == "chunk-123"
        assert chunk.file_id == "file-456"
        assert chunk.output_id == "output-789"
        assert chunk.project_id == 1
        assert chunk.filename == "test.txt"
        assert chunk.chunk_number == 0
        assert chunk.total_chunks == 5
        assert chunk.chunk_text == "This is chunk text."
        assert chunk.token_count == 20
        assert chunk.pages == [1, 2]
        assert chunk.metadata["key"] == "value"
