from pydantic import BaseModel, Field


class CroppedSectionResponse(BaseModel):
    index: int = Field(ge=1)
    title: str
    page: int = Field(ge=1)
    image_base64: str


class CropResponse(BaseModel):
    total: int = Field(ge=0)
    sections: list[CroppedSectionResponse]
