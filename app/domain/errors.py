class PdfProcessingError(Exception):
    """Base exception for PDF processing failures."""


class InvalidPdfError(PdfProcessingError):
    """Raised when bytes cannot be opened as a PDF."""


class NoSectionsFoundError(PdfProcessingError):
    """Raised when no heading matching the supplied keywords is detected."""
