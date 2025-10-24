"""
Tests for DocumentSummarizer.
"""

import pytest

from docprocessor.core.summarizer import DocumentSummarizer, SummarizationError


class TestDocumentSummarizer:
    """Tests for DocumentSummarizer class."""

    def test_init_default_params(self):
        """Test summarizer initialization with defaults."""
        summarizer = DocumentSummarizer()

        assert summarizer.llm_client is None
        assert summarizer.target_words == 500
        assert summarizer.temperature == 0.3

    def test_init_with_llm_client(self, mock_llm_client):
        """Test summarizer initialization with LLM client."""
        summarizer = DocumentSummarizer(
            llm_client=mock_llm_client, target_words=300, temperature=0.5
        )

        assert summarizer.llm_client is not None
        assert summarizer.target_words == 300
        assert summarizer.temperature == 0.5

    def test_summarize_with_llm(self, sample_text, mock_llm_client):
        """Test summarization with LLM client."""
        summarizer = DocumentSummarizer(llm_client=mock_llm_client)

        summary = summarizer.summarize(sample_text, "test.txt")

        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "mock summary" in summary.lower()

    def test_summarize_without_llm(self, sample_text):
        """Test summarization without LLM uses fallback."""
        summarizer = DocumentSummarizer()  # No LLM client

        summary = summarizer.summarize(sample_text, "test.txt")

        # Should return fallback summary (truncated text)
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert len(summary) <= len(sample_text)

    def test_summarize_with_fallback(self, sample_text, mock_llm_client):
        """Test summarization with fallback when LLM succeeds."""
        summarizer = DocumentSummarizer(llm_client=mock_llm_client)

        summary = summarizer.summarize_with_fallback(sample_text, "test.txt")

        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_fallback_summary_no_llm(self, sample_text):
        """Test fallback summary when no LLM client."""
        summarizer = DocumentSummarizer()  # No LLM client

        summary = summarizer.summarize_with_fallback(sample_text, "test.txt")

        assert isinstance(summary, str)
        assert len(summary) > 0
        # Fallback should truncate text
        assert len(summary) <= len(sample_text)

    def test_create_fallback_summary(self, sample_text):
        """Test creating fallback summary."""
        summarizer = DocumentSummarizer(target_words=100)

        fallback = summarizer._create_fallback_summary(sample_text)

        assert isinstance(fallback, str)
        assert len(fallback) > 0
        # Should be truncated based on target words
        word_count = len(fallback.split())
        assert word_count <= 150  # Some tolerance

    def test_fallback_summary_short_text(self):
        """Test fallback summary with very short text."""
        summarizer = DocumentSummarizer(target_words=500)
        short_text = "This is a very short text."

        fallback = summarizer._create_fallback_summary(short_text)

        assert fallback == short_text

    def test_fallback_summary_empty_text(self):
        """Test fallback summary with empty text."""
        summarizer = DocumentSummarizer()

        fallback = summarizer._create_fallback_summary("")

        assert fallback == ""

    def test_summarize_with_metadata(self, sample_text, mock_llm_client):
        """Test summarization with metadata."""
        summarizer = DocumentSummarizer(llm_client=mock_llm_client)
        metadata = {"format": "pdf", "page_count": 10}

        summary = summarizer.summarize(sample_text, "test.pdf", metadata)

        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_summarize_long_text(self, long_text, mock_llm_client):
        """Test summarization of long text."""
        summarizer = DocumentSummarizer(llm_client=mock_llm_client)

        summary = summarizer.summarize(long_text, "long_doc.txt")

        assert isinstance(summary, str)
        assert len(summary) > 0
        assert len(summary) < len(long_text)

    def test_llm_client_interface(self, sample_text):
        """Test that LLM client must have complete_chat method."""

        class InvalidLLMClient:
            pass

        summarizer = DocumentSummarizer(llm_client=InvalidLLMClient())

        # Should raise SummarizationError wrapping the AttributeError
        with pytest.raises(SummarizationError, match="LLM call failed"):
            summarizer.summarize(sample_text, "test.txt")

    def test_llm_response_format(self, sample_text):
        """Test handling of different LLM response formats."""

        class CustomLLMClient:
            def complete_chat(self, messages, temperature):
                return {"content": "Custom format summary."}

        summarizer = DocumentSummarizer(llm_client=CustomLLMClient())

        summary = summarizer.summarize(sample_text, "test.txt")

        assert summary == "Custom format summary."

    def test_summarize_very_short_text(self):
        """Test summarization of very short text returns as-is."""
        summarizer = DocumentSummarizer()

        short_text = "Hello world"
        summary = summarizer.summarize(short_text, "short.txt")

        # Should return the short text as-is
        assert summary == short_text.strip()

    def test_summarize_long_text_truncation(self, mock_llm_client):
        """Test very long text gets truncated before summarization."""
        summarizer = DocumentSummarizer(llm_client=mock_llm_client)

        # Create text longer than 30000 characters
        very_long_text = "word " * 10000  # 50000 characters

        summary = summarizer.summarize(very_long_text, "long.txt")

        # Should still get a summary
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_summarize_with_fallback_on_failure(self, sample_text):
        """Test summarize_with_fallback returns fallback on error."""

        class FailingLLMClient:
            def complete_chat(self, messages, temperature):
                raise Exception("API error")

        summarizer = DocumentSummarizer(llm_client=FailingLLMClient())

        summary = summarizer.summarize_with_fallback(sample_text, "test.txt")

        # Should get fallback summary
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_create_fallback_summary_at_boundary(self):
        """Test fallback summary truncation at sentence boundary."""
        summarizer = DocumentSummarizer(target_words=100)

        # Create text with clear sentence boundaries
        text = "First sentence here. " * 200

        fallback = summarizer._create_fallback_summary(text)

        # Should truncate at sentence boundary
        assert fallback.endswith((".", " [...]", ". [...]"))


class TestSummarizationError:
    """Tests for SummarizationError exception."""

    def test_exception_creation(self):
        """Test creating SummarizationError."""
        error = SummarizationError("Test error message")

        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_exception_raising(self):
        """Test raising SummarizationError."""
        with pytest.raises(SummarizationError, match="Test error"):
            raise SummarizationError("Test error")
