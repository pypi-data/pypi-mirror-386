from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="docprocessor",
    version="1.0.0",
    author="Knowledge Innovation Centre",
    author_email="info@knowledgeinnovation.eu",
    description="A Python library for document processing with OCR, chunking, and summarization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Knowledge-Innovation-Centre/doc-processor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "pdfminer.six>=20221105",
        "pdf2image>=1.16.3",
        "pytesseract>=0.3.10",
        "opencv-python>=4.9.0",
        "Pillow>=10.2.0",
        "python-docx>=1.1.0",
        "langchain-text-splitters>=0.2.0",
        "tiktoken>=0.7.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "meilisearch": ["meilisearch>=0.31.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
        ],
    },
)
