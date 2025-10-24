# backend/app/utils/ocr.py

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from io import BytesIO
from typing import List

import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_bytes
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTTextBox, LTTextLine
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class TextElement:
    text: str
    x: float
    y: float
    page_number: int


def extract_pdf_for_llm(pdf_bytes: bytes) -> str:
    """
    Extract text with layout on a per-page basis, falling back to OCR only on pages
    with no extractable text. Returns a structured string for LLM analysis.
    """
    try:
        all_elements: List[TextElement] = []
        pages_to_ocr: List[int] = []

        # Safer text extraction with explicit PDFObjRef handling
        try:
            # Create LAParams for better extraction
            laparams = LAParams(
                line_margin=0.5, word_margin=0.1, boxes_flow=0.5, detect_vertical=True
            )

            # Process each page safely
            for page_num, page in enumerate(
                extract_pages(BytesIO(pdf_bytes), laparams=laparams), start=1
            ):
                page_elements = []

                # Safely iterate elements with PDFObjRef handling
                for element in safe_iter_elements(page):
                    if isinstance(element, (LTTextBox, LTTextLine)):
                        page_elements.append(
                            TextElement(
                                text=element.get_text().strip(),
                                x=element.x0,
                                y=element.y0,
                                page_number=page_num,
                            )
                        )

                if page_elements:
                    all_elements.extend(page_elements)
                else:
                    pages_to_ocr.append(page_num)
        except Exception as e:
            logger.error(f"Error in text extraction: {e}")
            # Fall back to OCR for all pages
            pages_to_ocr = list(range(1, 100))  # Assume max 100 pages as fallback

        # OCR only on pages without native text
        if pages_to_ocr:
            try:
                ocr_elements = perform_structured_ocr(pdf_bytes, pages_to_ocr)
                all_elements.extend(ocr_elements)
            except Exception as ocr_e:
                logger.error(f"OCR processing failed: {ocr_e}")

        return format_for_llm(all_elements)

    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        raise


# NEW HELPER FUNCTION: Safe iteration that handles PDFObjRef objects
def safe_iter_elements(obj):
    """Safely iterate over page elements, handling PDFObjRef objects."""
    try:
        # This is the standard iteration approach
        for item in obj:
            yield item
    except TypeError as e:
        if "'PDFObjRef' object is not iterable" in str(e):
            # If we hit a PDFObjRef issue, just return an empty iterator
            logger.warning("Encountered PDFObjRef object, skipping")
            return
        else:
            # Re-raise other TypeError exceptions
            raise


def perform_structured_ocr(pdf_bytes: bytes, pages_to_ocr: List[int]) -> List[TextElement]:
    """
    OCR with structure preservation only on specified pages.
    """
    # Convert PDF pages to images at lower DPI for speed
    images = convert_from_bytes(pdf_bytes, dpi=150)

    # Filter pages to OCR to only include pages that exist
    pages_to_ocr = [p for p in pages_to_ocr if 1 <= p <= len(images)]

    if not pages_to_ocr:
        return []

    # Process pages in parallel
    with ThreadPoolExecutor() as pool:
        results = pool.map(lambda pg: _ocr_one_page(images[pg - 1], pg), pages_to_ocr)

    # Flatten list of lists
    elements: List[TextElement] = []
    for sublist in results:
        elements.extend(sublist)

    return elements


def _ocr_one_page(image: Image.Image, page_num: int) -> List[TextElement]:
    """
    Perform OCR on a single page image and group words into lines.
    """
    # Preprocess image for better OCR accuracy
    pre = preprocess_image(image)
    data = pytesseract.image_to_data(
        pre, output_type=pytesseract.Output.DICT, config="--oem 3 --psm 6"
    )

    # Group words into lines to reduce element count
    lines = {}
    for i, word in enumerate(data["text"]):
        if not word.strip():
            continue

        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])

        if key not in lines:
            lines[key] = {"words": [], "x": data["left"][i], "y": data["top"][i]}

        lines[key]["words"].append(word)

    elements: List[TextElement] = []
    for v in lines.values():
        elements.append(
            TextElement(text=" ".join(v["words"]), x=v["x"], y=v["y"], page_number=page_num)
        )

    return elements


def format_for_llm(elements: List[TextElement]) -> str:
    """
    Formats extracted text to help the LLM understand document structure.
    """
    # Sort by page, then top-to-bottom, left-to-right
    elements.sort(key=lambda e: (e.page_number, -e.y, e.x))

    formatted = []
    current_page = 0

    for element in elements:
        if element.page_number != current_page:
            formatted.append(f"\n<page_{element.page_number}>\n")
            current_page = element.page_number

        if is_likely_table_column(element, elements):
            formatted.append(f"<col>{element.text}</col>")
        else:
            formatted.append(element.text)

    return "\n".join(formatted)


def is_likely_table_column(element: TextElement, all_elements: List[TextElement]) -> bool:
    """
    Identifies potential table columns based on alignment.
    """
    aligned = [e for e in all_elements if abs(e.x - element.x) < 5 and e != element]
    return len(aligned) >= 2


def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Optimize image for OCR: grayscale and threshold.
    """
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    # Apply Otsu thresholding
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return Image.fromarray(thresh)
