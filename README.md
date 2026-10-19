# PDF Section Cropper

FastAPI service that detects numbered question/exercise headings in a PDF, crops each section into a PNG image, and returns each image as Base64 JSON.

## Requirements

- Python 3.10+
- pip

## Install

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

- API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health
- Endpoint: `POST /crop-sections`

## Example request

```bash
curl -X POST "http://127.0.0.1:8000/crop-sections" ^
  -F "file=@questions.pdf" ^
  -F "scale=2.0" ^
  -F "keywords=cau,bai,question,questions,task,exercise"
```

The response retains the existing structure:

```json
{
  "total": 1,
  "sections": [
    {
      "index": 1,
      "title": "Câu 1",
      "page": 1,
      "image_base64": "iVBORw0KGgo..."
    }
  ]
}
```

## Design

- `api/`: HTTP routes and request/response schemas.
- `application/`: use-case orchestration.
- `domain/entities/`: framework-independent data entities.
- `domain/services/`: section detection rules.
- `infrastructure/pdf/`: PyMuPDF/Pillow rendering and Base64 encoding.

## Important notes

1. This version intentionally preserves the original detection strategy: it chooses the largest group sharing keyword, horizontal position and font style. PDFs with inconsistent heading styles may have headings omitted; replace this strategy if you want to detect all heading styles.
2. `scale` is limited to `(0, 4]` to avoid accidental huge image allocations. Tune this limit and add upload/page/pixel limits before production deployment.
3. CORS currently allows every origin for ease of local development. Restrict `allow_origins` before deploying.
4. Base64 images increase response size. For large PDFs, consider returning object-storage URLs or streaming results instead.
