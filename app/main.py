from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.crop_routes import router as crop_router
from app.api.errors import register_exception_handlers

app = FastAPI(title="PDF Section Cropper", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this to your frontend origin in production.
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(crop_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
