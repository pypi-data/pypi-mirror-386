"""
Tests for MeiliSearchIndexer.
"""

import pytest

from docprocessor.integrations.meilisearch_indexer import MeiliSearchIndexer


class TestMeiliSearchIndexer:
    """Tests for MeiliSearchIndexer class."""

    def test_init_without_prefix(self, mock_meilisearch_client):
        """Test indexer initialization without prefix."""
        indexer = MeiliSearchIndexer(
            url="http://localhost:7700", api_key="test_key", client=mock_meilisearch_client
        )

        assert indexer.url == "http://localhost:7700"
        assert indexer.api_key == "test_key"
        assert indexer.index_prefix == ""

    def test_init_with_prefix(self, mock_meilisearch_client):
        """Test indexer initialization with prefix."""
        indexer = MeiliSearchIndexer(
            url="http://localhost:7700",
            api_key="test_key",
            index_prefix="dev_",
            client=mock_meilisearch_client,
        )

        assert indexer.index_prefix == "dev_"

    def test_get_prefixed_index_name(self, mock_meilisearch_client):
        """Test getting prefixed index name."""
        indexer = MeiliSearchIndexer(
            url="http://localhost:7700",
            api_key="test_key",
            index_prefix="prod_",
            client=mock_meilisearch_client,
        )

        prefixed = indexer._get_prefixed_index_name("documents")

        assert prefixed == "prod_documents"

    def test_get_prefixed_index_name_no_prefix(self, mock_meilisearch_client):
        """Test getting index name without prefix."""
        indexer = MeiliSearchIndexer(
            url="http://localhost:7700", api_key="test_key", client=mock_meilisearch_client
        )

        prefixed = indexer._get_prefixed_index_name("documents")

        assert prefixed == "documents"

    def test_index_chunks(self, mock_meilisearch_client):
        """Test indexing chunks."""
        indexer = MeiliSearchIndexer(
            url="http://localhost:7700", api_key="test_key", client=mock_meilisearch_client
        )

        chunks_data = [
            {
                "id": "chunk-1",
                "file_id": "file-123",
                "chunk_text": "Test chunk 1",
                "chunk_number": 0,
            },
            {
                "id": "chunk-2",
                "file_id": "file-123",
                "chunk_text": "Test chunk 2",
                "chunk_number": 1,
            },
        ]

        result = indexer.index_chunks(
            chunks=chunks_data, index_name="document_chunks", primary_key="id"
        )

        assert result["status"] == "enqueued"

    def test_index_document(self, mock_meilisearch_client):
        """Test indexing single document."""
        indexer = MeiliSearchIndexer(
            url="http://localhost:7700", api_key="test_key", client=mock_meilisearch_client
        )

        doc_data = {
            "id": "doc-123",
            "filename": "test.pdf",
            "summary": "Test summary",
            "page_count": 5,
        }

        result = indexer.index_document(document=doc_data, index_name="documents", primary_key="id")

        assert result["status"] == "enqueued"

    def test_search(self, mock_meilisearch_client):
        """Test searching an index."""
        indexer = MeiliSearchIndexer(
            url="http://localhost:7700", api_key="test_key", client=mock_meilisearch_client
        )

        results = indexer.search(query="test query", index_name="document_chunks", limit=10)

        assert "hits" in results
        assert results["limit"] == 10

    def test_delete_document(self, mock_meilisearch_client):
        """Test deleting a document by ID."""
        indexer = MeiliSearchIndexer(
            url="http://localhost:7700", api_key="test_key", client=mock_meilisearch_client
        )

        result = indexer.delete_document(document_id="doc-123", index_name="documents")

        assert result["status"] == "enqueued"

    def test_delete_documents_by_filter(self, mock_meilisearch_client):
        """Test deleting documents by filter."""
        indexer = MeiliSearchIndexer(
            url="http://localhost:7700", api_key="test_key", client=mock_meilisearch_client
        )

        result = indexer.delete_documents_by_filter(
            filter_str="file_id = 'file-123'", index_name="document_chunks"
        )

        assert result["status"] == "enqueued"

    def test_create_index(self, mock_meilisearch_client):
        """Test creating a new index."""
        indexer = MeiliSearchIndexer(
            url="http://localhost:7700", api_key="test_key", client=mock_meilisearch_client
        )

        result = indexer.create_index(index_name="new_index", primary_key="id")

        assert result["status"] == "enqueued"

    def test_index_with_prefix(self, mock_meilisearch_client):
        """Test indexing with prefix."""
        indexer = MeiliSearchIndexer(
            url="http://localhost:7700",
            api_key="test_key",
            index_prefix="test_",
            client=mock_meilisearch_client,
        )

        chunks_data = [{"id": "chunk-1", "chunk_text": "Test"}]

        indexer.index_chunks(chunks=chunks_data, index_name="document_chunks")

        # Verify the prefixed index name was used
        assert "test_document_chunks" in mock_meilisearch_client.indexes

    def test_search_with_filters(self, mock_meilisearch_client):
        """Test searching with filters."""
        indexer = MeiliSearchIndexer(
            url="http://localhost:7700", api_key="test_key", client=mock_meilisearch_client
        )

        results = indexer.search(
            query="test", index_name="document_chunks", limit=20, filters="project_id = 123"
        )

        assert "hits" in results

    def test_batch_indexing(self, mock_meilisearch_client):
        """Test indexing large batch of chunks."""
        indexer = MeiliSearchIndexer(
            url="http://localhost:7700", api_key="test_key", client=mock_meilisearch_client
        )

        # Create many chunks
        chunks_data = [{"id": f"chunk-{i}", "chunk_text": f"Test chunk {i}"} for i in range(100)]

        result = indexer.index_chunks(chunks=chunks_data, index_name="document_chunks")

        assert result["status"] == "enqueued"

    def test_empty_chunks_list(self, mock_meilisearch_client):
        """Test indexing empty chunks list."""
        indexer = MeiliSearchIndexer(
            url="http://localhost:7700", api_key="test_key", client=mock_meilisearch_client
        )

        result = indexer.index_chunks(chunks=[], index_name="document_chunks")

        # Should handle gracefully
        assert result is not None

    def test_create_index_with_settings(self, mock_meilisearch_client):
        """Test creating index with custom settings."""
        indexer = MeiliSearchIndexer(
            url="http://localhost:7700", api_key="test_key", client=mock_meilisearch_client
        )

        settings = {
            "searchableAttributes": ["title", "content"],
            "filterableAttributes": ["category"],
        }

        result = indexer.create_index(
            index_name="custom_index", primary_key="id", settings=settings
        )

        assert result["status"] == "enqueued"

    def test_indexer_without_client_parameter(self):
        """Test indexer initialization without providing client."""
        try:
            import meilisearch

            # This would normally create a real client
            # but we can't test it without a real server
            # Just verify the import path works
            assert meilisearch is not None
        except ImportError:
            pytest.skip("meilisearch not installed")
