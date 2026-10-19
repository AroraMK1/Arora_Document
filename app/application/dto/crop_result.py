from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CroppedSectionResult:
    index: int
    title: str
    page: int
    image_base64: str


@dataclass(frozen=True, slots=True)
class CropResult:
    total: int
    sections: list[CroppedSectionResult]
