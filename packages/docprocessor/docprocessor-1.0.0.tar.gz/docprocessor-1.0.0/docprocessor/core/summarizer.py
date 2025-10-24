# docprocessor/core/summarizer.py

"""
Document summarization service.

Generates concise summaries of documents for semantic search and document discovery.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SummarizationError(Exception):
    """Raised when summarization fails."""

    pass


class DocumentSummarizer:
    """
    Generates document summaries using an LLM.

    Creates summaries suitable for semantic search and quick document discovery.
    """

    def __init__(
        self, llm_client: Optional[Any] = None, target_words: int = 500, temperature: float = 0.3
    ):
        """
        Initialize the summarizer.

        Args:
            llm_client: LLM client with a complete_chat(messages, temperature) method.
                       If None, summarization will use fallback truncation only.
            target_words: Target summary length in words (default: 500)
            temperature: LLM temperature for generation (default: 0.3)
        """
        self.target_words = target_words
        self.temperature = temperature
        self.llm_client = llm_client

    def summarize(self, text: str, filename: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a summary of the document.

        Args:
            text: Full document text
            filename: Name of the file being summarized
            metadata: Optional extraction metadata

        Returns:
            Summary text (approximately target_words length)

        Raises:
            SummarizationError: If summarization fails
        """
        if not text or len(text.strip()) < 100:
            logger.warning(f"Text too short to summarize: {len(text)} characters")
            return text.strip()

        if not self.llm_client:
            logger.warning("No LLM client provided, using fallback truncation")
            return self._create_fallback_summary(text)

        try:
            # Truncate very long documents to save on API costs
            max_input_length = 30000  # ~7500 tokens
            if len(text) > max_input_length:
                logger.info(
                    f"Truncating long document from {len(text)} to {max_input_length} chars"
                )
                text = text[:max_input_length] + "\n\n[Document truncated for summarization]"

            prompt = self._build_prompt(text, filename)
            summary = self._call_llm(prompt)

            logger.info(f"Generated summary for {filename}: {len(summary)} characters")
            return summary

        except Exception as e:
            logger.error(f"Error summarizing document: {e}")
            raise SummarizationError(f"Failed to generate summary: {str(e)}")

    def _build_prompt(self, text: str, filename: str) -> str:
        """Build the prompt for the LLM."""
        return (
            f"""You are a document summarization assistant. """
            f"""Generate a comprehensive {self.target_words}-word summary """
            f"""of the following document.

The summary should:
- Capture the main topics, themes, and key points
- Be written in clear, professional language
- Focus on substantive content rather than document structure
- Maintain factual accuracy
- Be suitable for semantic search and document discovery

Document: {filename}

Content:
{text}

Generate a {self.target_words}-word summary:"""
        )

    def _call_llm(self, prompt: str) -> str:
        """Call the LLM to generate summary."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a professional document summarization assistant. "
                    "Generate clear, accurate summaries that capture key information."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        try:
            # Call the LLM client
            # Expects a method like: complete_chat(messages=..., temperature=...)
            # Returns: {"content": "summary text"}
            response = self.llm_client.complete_chat(
                messages=messages, temperature=self.temperature
            )

            summary = response.get("content", "").strip()

            if not summary:
                raise SummarizationError("LLM returned empty summary")

            return summary

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise SummarizationError(f"LLM call failed: {str(e)}")

    def summarize_with_fallback(
        self, text: str, filename: str, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Summarize with automatic fallback to truncation.

        If LLM summarization fails, returns a simple truncated preview.

        Args:
            text: Full document text
            filename: Name of the file
            metadata: Optional extraction metadata

        Returns:
            Summary text or truncated preview
        """
        try:
            return self.summarize(text, filename, metadata)
        except SummarizationError as e:
            logger.warning(f"Summarization failed, using fallback: {e}")
            return self._create_fallback_summary(text)

    def _create_fallback_summary(self, text: str) -> str:
        """Create a simple truncated preview as fallback."""
        # Take first ~2000 characters (approximately 500 words)
        preview_length = 2000

        if len(text) <= preview_length:
            return text

        # Truncate at sentence boundary
        truncated = text[:preview_length]
        last_period = truncated.rfind(". ")

        if last_period > preview_length // 2:
            return truncated[: last_period + 1] + " [...]"

        return truncated + " [...]"
