import re
import unicodedata
from collections import defaultdict
from typing import Any

from app.domain.entities.section import Section


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", text).strip()


def is_bold_span(span: dict[str, Any]) -> bool:
    # PyMuPDF flags include font properties; font-name fallback helps with some PDFs.
    return bool(span.get("flags", 0) & 16) or "bold" in span.get("font", "").lower()


def is_italic_span(span: dict[str, Any]) -> bool:
    return bool(span.get("flags", 0) & 2) or "italic" in span.get("font", "").lower()


def span_style_key(span: dict[str, Any]) -> tuple[str, float, bool, bool]:
    return (
        span.get("font", ""),
        round(float(span.get("size", 0)), 1),
        is_bold_span(span),
        is_italic_span(span),
    )


class SectionDetector:
    """Detect numbered headings and group candidates by keyword, x-position and style."""

    X_TOLERANCE = 2.0

    def detect(self, document: Any, keywords: list[str]) -> list[Section]:
        normalized_keywords = [normalize_text(word) for word in keywords if word.strip()]
        if not normalized_keywords:
            return []

        candidates: list[Section] = []
        for page_index, page in enumerate(document):
            page_dict = page.get_text("dict")
            for block in page_dict.get("blocks", []):
                for line in block.get("lines", []):
                    spans = line.get("spans", [])
                    if not spans:
                        continue

                    title = "".join(span.get("text", "") for span in spans).strip()
                    matched_keyword = self._match_keyword(title, normalized_keywords)
                    if matched_keyword is None:
                        continue

                    first_span = next(
                        (span for span in spans if span.get("text", "").strip()), None
                    )
                    if first_span is None:
                        continue

                    x0 = float(first_span["bbox"][0])
                    x_bucket = round(x0 / self.X_TOLERANCE) * self.X_TOLERANCE
                    candidates.append(
                        Section(
                            title=title,
                            page_index=page_index,
                            y_top=float(first_span["bbox"][1]),
                            group_key=(matched_keyword, x_bucket, span_style_key(first_span)),
                        )
                    )

        if not candidates:
            return []

        groups: dict[tuple[object, ...], list[Section]] = defaultdict(list)
        for candidate in candidates:
            groups[candidate.group_key].append(candidate)

        # Preserve the original strategy: use the most common heading style/group.
        best_group = max(
            groups.values(),
            key=lambda group: (
                len(group),
                -group[0].page_index,
                -group[0].y_top,
            ),
        )
        return sorted(best_group, key=lambda section: (section.page_index, section.y_top))

    @staticmethod
    def _match_keyword(line_text: str, keywords: list[str]) -> str | None:
        normalized_line = normalize_text(line_text)
        for keyword in keywords:
            pattern = re.escape(keyword).replace(r"\ ", r"\s+")
            if re.match(rf"^{pattern}\s*\d+\b", normalized_line):
                return keyword
        return None
