import base64
import io
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import fitz
from PIL import Image

from app.domain.entities.section import Section
from app.domain.errors import InvalidPdfError, PdfProcessingError


class PdfRenderer:
    """PyMuPDF/Pillow adapter responsible for rendering and encoding images."""

    WHITESPACE_THRESHOLD = 250
    WHITESPACE_MIN_CONTENT_PIXELS = 5
    PNG_COMPRESS_LEVEL = 1

    def __init__(self, max_workers: int = 4) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max(1, max_workers))

    def open_document(self, pdf_bytes: bytes) -> fitz.Document:
        try:
            return fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as exc:
            raise InvalidPdfError("Unable to read the uploaded PDF.") from exc

    def render_pages(
        self, pdf_bytes: bytes, page_indices: list[int], scale: float
    ) -> dict[int, Image.Image]:
        # Each worker opens its own document. Do not share a PyMuPDF Document across threads.
        futures = {
            index: self._executor.submit(self._render_page, pdf_bytes, index, scale)
            for index in page_indices
        }
        try:
            return {index: future.result() for index, future in futures.items()}
        except Exception as exc:
            for future in futures.values():
                future.cancel()
            raise PdfProcessingError("Could not render one or more PDF pages.") from exc

    @staticmethod
    def _render_page(pdf_bytes: bytes, page_index: int, scale: float) -> Image.Image:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
        try:
            page = document[page_index]
            pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            with Image.open(io.BytesIO(pixmap.tobytes("png"))) as image:
                image.load()
                return image.convert("RGB")
        finally:
            document.close()

    def crop_section(
        self,
        page_images: dict[int, Image.Image],
        scale: float,
        start: Section,
        end: Section | None,
    ) -> Image.Image:
        def crop(page_index: int, y0: float, y1: float | None = None) -> Image.Image:
            image = page_images[page_index]
            top = max(0, min(image.height, round(y0 * scale)))
            bottom = image.height if y1 is None else max(
                top, min(image.height, round(y1 * scale))
            )
            return image.crop((0, top, image.width, bottom))

        if end is None:
            images = [
                crop(index, start.y_top if index == start.page_index else 0.0)
                for index in range(start.page_index, max(page_images) + 1)
            ]
        elif start.page_index == end.page_index:
            images = [crop(start.page_index, start.y_top, end.y_top)]
        else:
            images = [crop(start.page_index, start.y_top)]
            images.extend(
                crop(index, 0.0)
                for index in range(start.page_index + 1, end.page_index)
            )
            images.append(crop(end.page_index, 0.0, end.y_top))

        return self._stack_images(images) if len(images) > 1 else self._trim_whitespace(images[0])

    def image_to_base64(self, image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", compress_level=self.PNG_COMPRESS_LEVEL)
        return base64.b64encode(buffer.getvalue()).decode("ascii")

    def _trim_whitespace(self, image: Image.Image) -> Image.Image:
        gray = image.convert("L")
        width, height = gray.size
        pixels = gray.tobytes()

        def has_content(y: int) -> bool:
            row_start = y * width
            count = 0
            for pixel in pixels[row_start : row_start + width]:
                if pixel < self.WHITESPACE_THRESHOLD:
                    count += 1
                    if count >= self.WHITESPACE_MIN_CONTENT_PIXELS:
                        return True
            return False

        top = next((y for y in range(height) if has_content(y)), 0)
        bottom = next(
            (y for y in range(height - 1, top - 1, -1) if has_content(y)),
            height - 1,
        )
        return image.crop((0, top, width, bottom + 1))

    def _stack_images(self, images: list[Image.Image]) -> Image.Image:
        trimmed = [self._trim_whitespace(image) for image in images]
        total_width = max(image.width for image in trimmed)
        total_height = sum(image.height for image in trimmed)
        combined = Image.new("RGB", (total_width, total_height), "white")
        y = 0
        for image in trimmed:
            combined.paste(image, (0, y))
            y += image.height
        return combined
