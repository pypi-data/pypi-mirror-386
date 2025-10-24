# docprocessor/integrations/meilisearch_indexer.py

"""
Meilisearch integration for document indexing.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MeiliSearchIndexer:
    """
    Simplified Meilisearch indexer for document chunks.

    Handles indexing of processed document chunks and summaries to Meilisearch.
    """

    def __init__(
        self,
        url: str,
        api_key: str,
        index_prefix: Optional[str] = None,
        client: Optional[Any] = None,
    ):
        """
        Initialize the Meilisearch indexer.

        Args:
            url: Meilisearch server URL
            api_key: Meilisearch API key
            index_prefix: Optional prefix for index names (e.g., 'dev_', 'prod_')
            client: Optional pre-configured Meilisearch client (for testing)
        """
        self.url = url
        self.api_key = api_key
        self.index_prefix = index_prefix or ""

        if client is None:
            try:
                import meilisearch
            except ImportError:
                raise ImportError(
                    "meilisearch not installed. Install with: pip install meilisearch"
                )
            client = meilisearch.Client(url, api_key)

        self.client = client

    def _get_prefixed_index_name(self, base_name: str) -> str:
        """Get full index name with optional prefix."""
        if self.index_prefix:
            return f"{self.index_prefix}{base_name}"
        return base_name

    def _get_index_name(self, base_name: str) -> str:
        """Alias for backward compatibility."""
        return self._get_prefixed_index_name(base_name)

    def index_chunks(
        self, chunks: List[Dict[str, Any]], index_name: str, primary_key: str = "id"
    ) -> Dict[str, Any]:
        """
        Index document chunks to Meilisearch.

        Args:
            chunks: List of chunk dictionaries to index
            index_name: Name of the index (without prefix)
            primary_key: Primary key field name (default: 'id')

        Returns:
            Meilisearch task info
        """
        full_index_name = self._get_index_name(index_name)
        index = self.client.index(full_index_name)

        try:
            result = index.add_documents(chunks, primary_key=primary_key)
            logger.info(f"Indexed {len(chunks)} chunks to {full_index_name}")
            return result
        except Exception as e:
            logger.error(f"Error indexing to {full_index_name}: {e}")
            raise

    def index_document(
        self, document: Dict[str, Any], index_name: str, primary_key: str = "id"
    ) -> Dict[str, Any]:
        """
        Index a single document to Meilisearch.

        Args:
            document: Document dictionary to index
            index_name: Name of the index (without prefix)
            primary_key: Primary key field name (default: 'id')

        Returns:
            Meilisearch task info
        """
        return self.index_chunks([document], index_name, primary_key)

    def search(
        self, query: str, index_name: str, filters: Optional[str] = None, limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search documents in an index.

        Args:
            query: Search query
            index_name: Name of the index (without prefix)
            filters: Optional Meilisearch filter string
            limit: Maximum number of results

        Returns:
            Search results
        """
        full_index_name = self._get_index_name(index_name)
        index = self.client.index(full_index_name)

        search_params = {"limit": limit}
        if filters:
            search_params["filter"] = filters

        return index.search(query, search_params)

    def delete_document(self, document_id: str, index_name: str) -> Dict[str, Any]:
        """
        Delete a document from an index.

        Args:
            document_id: ID of document to delete
            index_name: Name of the index (without prefix)

        Returns:
            Meilisearch task info
        """
        full_index_name = self._get_index_name(index_name)
        index = self.client.index(full_index_name)
        return index.delete_document(document_id)

    def delete_documents_by_filter(self, filter_str: str, index_name: str) -> Dict[str, Any]:
        """
        Delete documents matching a filter.

        Args:
            filter_str: Meilisearch filter string
            index_name: Name of the index (without prefix)

        Returns:
            Meilisearch task info
        """
        full_index_name = self._get_index_name(index_name)
        index = self.client.index(full_index_name)
        return index.delete_documents({"filter": filter_str})

    def create_index(
        self, index_name: str, primary_key: str = "id", settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new index with optional settings.

        Args:
            index_name: Name of the index (without prefix)
            primary_key: Primary key field name
            settings: Optional index settings (searchable attributes, etc.)

        Returns:
            Meilisearch task info
        """
        full_index_name = self._get_index_name(index_name)

        # Create index
        task = self.client.create_index(full_index_name, {"primaryKey": primary_key})

        # Apply settings if provided
        if settings:
            index = self.client.index(full_index_name)
            index.update_settings(settings)

        logger.info(f"Created index: {full_index_name}")
        return task
