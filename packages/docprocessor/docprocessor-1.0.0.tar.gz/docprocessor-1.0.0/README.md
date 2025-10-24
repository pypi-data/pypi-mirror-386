# DocProcessor

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI Status](https://github.com/Knowledge-Innovation-Centre/doc-processor/workflows/CI/badge.svg)](https://github.com/Knowledge-Innovation-Centre/doc-processor/actions)

A Python library for processing documents with OCR, semantic chunking, and LLM-based summarization. Designed for building semantic search systems and document analysis workflows.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Advanced Usage](#advanced-usage)
- [API Reference](#api-reference)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Multi-format Support**: PDF, DOCX, TXT, MD, and images (PNG, JPG, GIF, BMP)
- **Intelligent OCR**: Layout-aware PDF text extraction with OCR fallback for images
- **Semantic Chunking**: Smart text segmentation using LangChain's RecursiveCharacterTextSplitter
- **LLM Summarization**: Generate concise document summaries (with fallback)
- **Meilisearch Integration**: Built-in support for indexing to Meilisearch
- **Flexible API**: Use components individually or as a unified pipeline

## Installation

### From PyPI (Coming Soon)

```bash
pip install docprocessor
```

### From GitHub

```bash
pip install git+https://github.com/Knowledge-Innovation-Centre/doc-processor.git
```

### For Development

```bash
git clone https://github.com/Knowledge-Innovation-Centre/doc-processor.git
cd doc-processor
pip install -e ".[dev]"
```

### System Dependencies

For OCR functionality, install system packages:

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr poppler-utils
```

**macOS:**
```bash
brew install tesseract poppler
```

## Quick Start

### Basic Usage

```python
from docprocessor import DocumentProcessor

# Initialize processor
processor = DocumentProcessor()

# Process a document
result = processor.process(
    file_path="document.pdf",
    extract_text=True,
    chunk=True,
    summarize=False  # Requires LLM client
)

print(f"Extracted {len(result.text)} characters")
print(f"Created {len(result.chunks)} chunks")
```

### With LLM Summarization

```python
from docprocessor import DocumentProcessor

# Your LLM client (must have a complete_chat method)
class MyLLMClient:
    def complete_chat(self, messages, temperature):
        # Call your LLM API (OpenAI, Anthropic, Mistral, etc.)
        return {"content": "Generated summary here"}

llm_client = MyLLMClient()

processor = DocumentProcessor(
    llm_client=llm_client,
    summary_target_words=500
)

result = processor.process(
    file_path="document.pdf",
    summarize=True
)

print(f"Summary: {result.summary}")
```

### With Meilisearch Indexing

```python
from docprocessor import DocumentProcessor, MeiliSearchIndexer

# Process document
processor = DocumentProcessor()
result = processor.process("document.pdf", chunk=True)

# Index to Meilisearch
indexer = MeiliSearchIndexer(
    url="http://localhost:7700",
    api_key="your_master_key",
    index_prefix="dev_"  # Optional environment prefix
)

# Convert chunks to search documents
search_docs = processor.chunks_to_search_documents(result.chunks)

# Index chunks
indexer.index_chunks(
    chunks=search_docs,
    index_name="document_chunks"
)

# Search
results = indexer.search(
    query="artificial intelligence",
    index_name="document_chunks",
    limit=10
)
```

## Advanced Usage

### Custom Chunking Parameters

```python
processor = DocumentProcessor(
    chunk_size=1024,      # Larger chunks
    chunk_overlap=100,    # More overlap
    min_chunk_size=200    # Higher minimum
)

chunks = processor.chunk_text(
    text="Your long document text here...",
    filename="document.txt"
)
```

### Extract Text Only

```python
processor = DocumentProcessor()

extraction = processor.extract_text("document.pdf")

print(f"Text: {extraction['text']}")
print(f"Pages: {extraction['page_count']}")
print(f"Format: {extraction['metadata']['format']}")
```

### Multi-Environment Indexing

```python
# Index to multiple environments
environments = {
    "dev": {
        "url": "http://localhost:7700",
        "api_key": "dev_key",
        "prefix": "dev_"
    },
    "prod": {
        "url": "https://search.production.com",
        "api_key": "prod_key",
        "prefix": "prod_"
    }
}

for env_name, config in environments.items():
    indexer = MeiliSearchIndexer(
        url=config["url"],
        api_key=config["api_key"],
        index_prefix=config["prefix"]
    )

    indexer.index_chunks(search_docs, "document_chunks")
    print(f"Indexed to {env_name}")
```

## API Reference

### DocumentProcessor

Main class for document processing.

**Parameters:**
- `ocr_enabled` (bool): Enable OCR for PDFs/images. Default: `True`
- `chunk_size` (int): Target chunk size in tokens. Default: `512`
- `chunk_overlap` (int): Overlap between chunks. Default: `50`
- `min_chunk_size` (int): Minimum chunk size. Default: `100`
- `summary_target_words` (int): Target summary length. Default: `500`
- `llm_client` (Optional[Any]): LLM client for summarization
- `llm_temperature` (float): LLM temperature. Default: `0.3`

**Methods:**
- `process()`: Full pipeline (extract, chunk, summarize)
- `extract_text()`: Extract text from document
- `chunk_text()`: Chunk text into segments
- `summarize_text()`: Generate summary
- `chunks_to_search_documents()`: Convert chunks for indexing

### MeiliSearchIndexer

Interface for Meilisearch operations.

**Parameters:**
- `url` (str): Meilisearch server URL
- `api_key` (str): Meilisearch API key
- `index_prefix` (Optional[str]): Prefix for index names

**Methods:**
- `index_chunks()`: Index multiple documents
- `index_document()`: Index single document
- `search()`: Search an index
- `delete_document()`: Delete by ID
- `delete_documents_by_filter()`: Delete by filter
- `create_index()`: Create new index

### DocumentChunk

Data class representing a text chunk.

**Attributes:**
- `chunk_id` (str): Unique identifier
- `file_id` (str): Source file identifier
- `output_id` (str): Output identifier
- `project_id` (int): Project identifier
- `filename` (str): Source filename
- `chunk_number` (int): Chunk sequence number
- `total_chunks` (int): Total chunks in document
- `chunk_text` (str): The chunk text content
- `token_count` (int): Number of tokens
- `pages` (List[int]): Page numbers (for PDFs)
- `metadata` (Dict): Additional metadata

## Architecture

DocProcessor consists of several independent components:

1. **ContentExtractor**: Extracts text from various file formats
2. **DocumentChunker**: Splits text into semantic segments
3. **DocumentSummarizer**: Generates LLM-based summaries
4. **MeiliSearchIndexer**: Indexes documents to Meilisearch

Each component can be used independently or through the unified `DocumentProcessor` API.

## Requirements

**Python**: 3.10+ (tested on 3.10, 3.11, 3.12)

**Core Dependencies:**
- pdfminer.six - PDF text extraction
- pdf2image - PDF to image conversion
- pytesseract - OCR engine
- opencv-python - Image preprocessing
- Pillow - Image handling
- python-docx - DOCX extraction
- langchain-text-splitters - Semantic chunking
- tiktoken - Token counting

**Optional:**
- meilisearch - Search engine integration

## Examples

See the `examples/` directory for more usage examples:

- `basic_usage.py` - Simple document processing
- `multi_environment.py` - Indexing to multiple environments
- `custom_chunking.py` - Advanced chunking options

## Development

### Using GitHub Codespaces (Recommended)

The easiest way to start developing:

1. Click the **Code** button on GitHub
2. Select **Codespaces** → **Create codespace on main**
3. Wait for the environment to build (includes all dependencies)
4. Start coding!

The devcontainer automatically installs:
- Python 3.11
- All system dependencies (Tesseract, Poppler)
- Python dependencies in editable mode
- Pre-commit hooks
- VS Code extensions (Black, isort, flake8, etc.)

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/Knowledge-Innovation-Centre/doc-processor.git
cd doc-processor

# Install system dependencies
# Ubuntu/Debian
sudo apt-get install tesseract-ocr poppler-utils

# macOS
brew install tesseract poppler

# Install Python dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run tests with coverage
pytest --cov=docprocessor
```

### Code Quality

We use automated tools to maintain code quality:

```bash
# Format code
black docprocessor tests

# Sort imports
isort docprocessor tests

# Lint
flake8 docprocessor tests

# Type check
mypy docprocessor

# Or run all checks with pre-commit
pre-commit run --all-files
```

### Running Tests

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=docprocessor --cov-report=html

# Run specific test file
pytest tests/test_processor.py -v

# Run tests matching pattern
pytest -k "test_extract" -v
```

## Contributing

We love contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on:

- Development setup
- Code style guidelines
- Testing requirements
- Pull request process
- Issue reporting

Quick tips:
- Use the devcontainer for consistent environment
- Write tests for new features
- Follow PEP 8 and use pre-commit hooks
- Update documentation for API changes
- Add entries to CHANGELOG.md

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/Knowledge-Innovation-Centre/doc-processor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Knowledge-Innovation-Centre/doc-processor/discussions)
- **Email**: info@knowledgeinnovation.eu

## Citation

If you use docprocessor in your research or project, please cite:

```bibtex
@software{docprocessor2025,
  title = {docprocessor: Intelligent Document Processing Library},
  author = {Knowledge Innovation Centre},
  year = {2025},
  url = {https://github.com/Knowledge-Innovation-Centre/doc-processor}
}
```

---

Made with ❤️ by [Knowledge Innovation Centre](https://knowledgeinnovation.eu)
