from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.errors import PdfProcessingError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PdfProcessingError)
    async def pdf_processing_error_handler(
        request: Request, exc: PdfProcessingError
    ) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": str(exc)})
