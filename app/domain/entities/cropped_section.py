from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CroppedSection:
    index: int
    title: str
    page: int
    image_base64: str
