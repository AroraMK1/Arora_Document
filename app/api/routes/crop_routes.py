from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.api.schemas.crop_schemas import CropResponse, CroppedSectionResponse
from app.application.services.crop_service import CropService
from app.domain.errors import InvalidPdfError, NoSectionsFoundError, PdfProcessingError

router = APIRouter()
crop_service = CropService()


@router.post(
    "/crop-sections",
    response_model=CropResponse,
    summary="Detect and crop PDF question sections",
)
async def crop_sections(
    file: UploadFile = File(..., description="PDF file to process"),
    scale: float = Form(2.0, gt=0, le=4.0, description="Render scale; 2.0 is approximately 144 DPI"),
    keywords: str = Form(
        "cau,bai,question,questions,task,exercise",
        description="Comma-separated heading keywords",
    ),
) -> CropResponse:
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted.",
        )

    try:
        pdf_bytes = await file.read()
        if not pdf_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )
        keyword_list = [item.strip() for item in keywords.split(",") if item.strip()]
        result = await crop_service.crop_sections(pdf_bytes, scale, keyword_list)
        return CropResponse(
            total=result.total,
            sections=[
                CroppedSectionResponse(
                    index=section.index,
                    title=section.title,
                    page=section.page,
                    image_base64=section.image_base64,
                )
                for section in result.sections
            ],
        )
    except NoSectionsFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidPdfError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PdfProcessingError as exc:
        raise HTTPException(status_code=500, detail="Failed to process the PDF.") from exc
    finally:
        await file.close()
