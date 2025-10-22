import base64
import os
import sys
import threading
from collections import defaultdict
from pathlib import Path

import fitz  # PyMuPDF
from dotenv import load_dotenv
from loguru import logger

from ..static_visual_format.models import (
    qwen2_vl_7b_model_agent,
)

# Optional unstructured.io support
try:
    from unstructured.partition.pdf import partition_pdf

    HAS_UNSTRUCTURED = True
    print("unstructured available")
except Exception:
    HAS_UNSTRUCTURED = False


load_dotenv()


logger.remove()
log_level = os.getenv("RAGOPS_LOG_LEVEL", os.getenv("LOG_LEVEL", "ERROR"))
logger.add(
    sys.stderr,
    level=log_level,
    enqueue=True,
    backtrace=False,
    diagnose=False,
)


class StructuredPDFProcessor:
    """Structured PDF processor using PyMuPDF to extract text and images
    while preserving hierarchical structure.

    This processor preserves headings, paragraphs, lists, and other structural
    elements, which is critical for high-quality RAG.
    """

    def __init__(self, analyze_images: bool = True):
        """Initialize the PDF processor.

        Args:
            analyze_images: Whether to analyze images using an AI model
        """
        self.analyze_images = analyze_images
        self.temp_dir = Path(os.path.dirname(__file__)) / "tmp"
        self.temp_dir.mkdir(exist_ok=True)

    def process_pdf(self, pdf_path: str) -> list[dict[str, str | int]]:
        """Process a PDF file and extract structured content.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of dictionaries with extracted content and page numbers
        """
        logger.debug(f"Processing PDF file: {pdf_path}")

        raw_results = []
        threads = []
        lock = threading.Lock()

        try:
            # Open PDF document to get page count
            document = fitz.open(pdf_path)
            page_count = len(document)
            document.close()

            # Threading for parallel processing
            def process_page_thread(page_num: int):
                page_content = self._process_page(pdf_path, page_num)
                with lock:
                    raw_results.extend(page_content)

            # Start a thread for each page with a semaphore to limit concurrency
            semaphore = threading.Semaphore(4)  # Limit to 4 concurrent threads

            for page_num in range(page_count):
                thread = threading.Thread(
                    target=lambda p=page_num: self._thread_wrapper(
                        process_page_thread, semaphore, p
                    )
                )
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # Группируем весь текст по страницам
            page_text: dict[int, list[str]] = defaultdict(list)
            result = []

            # Сначала собираем весь текст по страницам
            for item in raw_results:
                page_num = item.get("page", 1)
                item_type = item.get("type", "")

                if item_type == "Text":
                    page_text[page_num].append(item.get("content", ""))
                elif item_type == "Image" or item_type == "Error":
                    result.append(item)

            # Добавляем объединенный текст для каждой страницы
            for page_num, texts in sorted(page_text.items()):
                result.append(
                    {"page": page_num, "type": "Text", "content": "\n\n".join(texts)}
                )

            # Сортируем результат по страницам и типу (сначала текст, потом изображения)
            result.sort(
                key=lambda x: (
                    x.get("page", 0),
                    0 if x.get("type", "") == "Text" else 1,
                    x.get("image_index", 0),
                )
            )

            return result

        except Exception as e:
            logger.exception(f"Error processing PDF: {e}")
            return [
                {
                    "page": 1,
                    "type": "Error",
                    "content": f"Error processing PDF: {e!s}",
                }
            ]

    def _thread_wrapper(self, func, semaphore, *args, **kwargs):
        """Helper to run a function with semaphore protection."""
        with semaphore:
            return func(*args, **kwargs)

    def _process_page(self, pdf_path: str, page_num: int) -> list[dict[str, str | int]]:
        """Process a single PDF page and extract structured text and images.

        Args:
            pdf_path: Path to the PDF file
            page_num: Page number (0-based)

        Returns:
            List of dictionaries with extracted content
        """
        result = []

        try:
            # Extract text and images
            text_content, images = self._extract_text_and_images(pdf_path, page_num)

            # Add text content to result
            if text_content:
                result.append(
                    {
                        "page": page_num + 1,  # Convert to 1-based page numbers
                        "type": "Text",
                        "content": text_content.strip(),
                    }
                )

            # Process images if requested
            if self.analyze_images:
                for img_idx, img_bytes in enumerate(images):
                    try:
                        # Encode image for AI model
                        encoded_image = base64.b64encode(img_bytes).decode("utf-8")

                        # Analyze image
                        image_context = qwen2_vl_7b_model_agent(
                            encoded_image, image_type="Slides"
                        )

                        result.append(
                            {
                                "page": page_num + 1,  # Convert to 1-based page numbers
                                "type": "Image",
                                "content": image_context,
                                "image_index": img_idx,
                            }
                        )
                    except Exception as e:
                        logger.error(
                            f"Error analyzing image {img_idx} on page {page_num + 1}: {e}"
                        )
                        result.append(
                            {
                                "page": page_num + 1,
                                "type": "Image",
                                "content": "Image analysis error",
                                "image_index": img_idx,
                            }
                        )

        except Exception as e:
            logger.error(f"Error processing page {page_num + 1}: {e}")
            result.append(
                {
                    "page": page_num + 1,
                    "type": "Error",
                    "content": f"Error processing page: {e!s}",
                }
            )

        return result

    def _extract_text_and_images(
        self, pdf_path: str, page_num: int
    ) -> tuple[str, list[bytes]]:
        """Extract structured text and images from a PDF page.

        Args:
            pdf_path: Path to the PDF file
            page_num: Page number (0-based)

        Returns:
            Tuple with text and a list of image bytes
        """
        document = fitz.open(pdf_path)
        page = document[page_num]

        # Извлечение текста с форматированием
        text_blocks = []

        # Попробуем определить заголовки на основе размера шрифта
        blocks = page.get_text("dict")["blocks"]

        # Найдем наиболее распространенный размер шрифта для определения основного текста
        font_sizes = []
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    font_sizes.append(span["size"])

        # Используем наиболее распространенный размер как базовый
        body_font_size = 11.0  # значение по умолчанию
        if font_sizes:
            # Простой расчет моды
            sizes_count = {}
            for size in font_sizes:
                sizes_count[size] = sizes_count.get(size, 0) + 1
            most_common = max(sizes_count.items(), key=lambda x: x[1])
            body_font_size = most_common[0]

        # Обработка блоков текста
        for block in blocks:
            if "lines" not in block:
                continue

            block_text = ""
            is_heading = False
            is_list_item = False

            for line in block["lines"]:
                line_text = ""
                line_is_heading = False

                # Проверка на списки
                first_span = line["spans"][0] if line["spans"] else None
                if first_span and first_span["text"].strip():
                    first_char = first_span["text"].strip()[0]
                    if first_char in ["•", "·", "-", "*"] or (
                        first_char.isdigit()
                        and len(first_span["text"].strip()) > 1
                        and first_span["text"].strip()[1] in [".", ")"]
                    ):
                        is_list_item = True

                for span in line["spans"]:
                    # Проверка на заголовок (заметно больше основного текста)
                    if (
                        span["size"] > body_font_size * 1.2
                        and len(span["text"].strip()) > 0
                    ):
                        line_is_heading = True
                    line_text += span["text"]

                if line_text.strip():
                    if line_is_heading:
                        is_heading = True
                    block_text += line_text.strip() + " "

            block_text = block_text.strip()
            if block_text:
                if is_heading:
                    # Маркируем как заголовок на основе размера шрифта
                    if block["lines"][0]["spans"][0]["size"] > body_font_size * 1.5:
                        text_blocks.append(f"# {block_text}\n\n")
                    else:
                        text_blocks.append(f"## {block_text}\n\n")
                elif is_list_item:
                    # Сохраняем форматирование списка
                    if block_text[0].isdigit():
                        # Нумерованный список
                        text_blocks.append(f"{block_text}\n")
                    else:
                        # Маркированный список
                        text_blocks.append(f"{block_text}\n")
                else:
                    text_blocks.append(f"{block_text}\n\n")

        # Извлечение изображений
        image_list = []
        for img_index, img in enumerate(page.get_images(full=True)):
            try:
                xref = img[0]
                base_image = document.extract_image(xref)
                image_bytes = base_image["image"]
                image_list.append(image_bytes)
            except Exception as e:
                logger.error(
                    f"Error extracting image {img_index} from page {page_num}: {e}"
                )

        document.close()

        return "".join(text_blocks), image_list


def parse_pdf(pdf_path: str) -> list[dict[str, str | int]]:
    """Analyze a PDF file and extract structured content for RAG.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        List of dictionaries with extracted content and page numbers
    """
    try:
        processor = StructuredPDFProcessor(analyze_images=True)
        return processor.process_pdf(pdf_path)
    except Exception as e:
        logger.exception(f"Error parsing PDF: {e}")
        return [{"page": 1, "type": "Error", "content": f"Error parsing PDF: {e!s}"}]


def parse_pdf_unstructured(pdf_path: str) -> list[dict[str, str | int]]:
    """Parse PDF with unstructured.io if available.

    Falls back to simple list of text chunks per page using element metadata.
    """
    if not HAS_UNSTRUCTURED:
        raise RuntimeError("unstructured not available")

    try:
        # Read strategy and OCR languages from environment (set via CLI in read_engine.py)
        # Tesseract uses language codes like "rus" for Russian, not "ru". Combine with '+'.
        strategy = os.getenv("UNSTRUCTURED_STRATEGY", "hi_res")
        languages_str = os.getenv("UNSTRUCTURED_OCR_LANG", "rus+eng")

        # Convert "rus+eng" to ["rus", "eng"] - unstructured expects a list
        languages = (
            languages_str.split("+") if "+" in languages_str else [languages_str]
        )

        # Call unstructured with correct parameter name `languages` for OCR
        elements = partition_pdf(
            filename=pdf_path,
            infer_table_structure=True,
            include_metadata=True,
            strategy=strategy,
            languages=languages,
        )

        # Group text by page
        pages: dict[int, list[str]] = defaultdict(list)
        results: list[dict[str, str | int]] = []

        for el in elements:
            # Some elements might not have metadata/page number
            meta = getattr(el, "metadata", None)
            page_num = getattr(meta, "page_number", None) or 1
            text = str(getattr(el, "text", "") or "").strip()
            if not text:
                continue
            pages[int(page_num)].append(text)

        for page_num in sorted(pages.keys()):
            content = "\n\n".join(pages[page_num]).strip()
            if content:
                results.append({"page": page_num, "type": "Text", "content": content})

        if not results:
            return [
                {
                    "page": 1,
                    "type": "Error",
                    "content": "No content extracted by unstructured",
                }
            ]

        return results
    except UnicodeDecodeError as e:
        # Common issue with Tesseract OCR output encoding - log without full traceback
        logger.error(
            f"Unicode decode error in unstructured/Tesseract OCR: {e}. "
            "Falling back to alternative PDF parser."
        )
        return [{"page": 1, "type": "Error", "content": f"OCR encoding error: {e!s}"}]
    except Exception as e:
        logger.exception(f"Error parsing PDF with unstructured: {e}")
        return [{"page": 1, "type": "Error", "content": f"unstructured failed: {e!s}"}]
