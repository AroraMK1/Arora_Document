import asyncio
import os

from app.application.dto.crop_result import CropResult, CroppedSectionResult
from app.domain.entities.cropped_section import CroppedSection
from app.domain.errors import NoSectionsFoundError, PdfProcessingError
from app.domain.services.section_detector import SectionDetector
from app.infrastructure.pdf.pdf_renderer import PdfRenderer


class CropService:
    """Application use case: detect headings, render relevant pages and build output."""

    def __init__(
        self,
        detector: SectionDetector | None = None,
        renderer: PdfRenderer | None = None,
    ) -> None:
        self._detector = detector or SectionDetector()
        self._renderer = renderer or PdfRenderer(
            max_workers=max(1, min(4, os.cpu_count() or 1))
        )

    async def crop_sections(
        self, pdf_bytes: bytes, scale: float, keywords: list[str]
    ) -> CropResult:
        if scale <= 0 or scale > 4:
            raise ValueError("scale must be greater than 0 and no more than 4")

        document = self._renderer.open_document(pdf_bytes)
        try:
            sections = self._detector.detect(document, keywords)
            page_count = document.page_count
        finally:
            document.close()

        if not sections:
            raise NoSectionsFoundError(
                f"No sections found for the supplied keywords: {keywords}"
            )

        first_page = sections[0].page_index
        page_indices = list(range(first_page, page_count))
        page_images = await asyncio.to_thread(
            self._renderer.render_pages, pdf_bytes, page_indices, scale
        )

        results: list[CroppedSectionResult] = []
        for index, section in enumerate(sections):
            next_section = sections[index + 1] if index + 1 < len(sections) else None
            image = self._renderer.crop_section(
                page_images, scale, section, next_section
            )
            entity = CroppedSection(
                index=index + 1,
                title=section.title,
                page=section.page_index + 1,
                image_base64=self._renderer.image_to_base64(image),
            )
            results.append(
                CroppedSectionResult(
                    index=entity.index,
                    title=entity.title,
                    page=entity.page,
                    image_base64=entity.image_base64,
                )
            )

        return CropResult(total=len(results), sections=results)
