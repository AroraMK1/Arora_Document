from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Section:
    """A detected section heading. page_index is zero-based; y_top uses PDF points."""

    title: str
    page_index: int
    y_top: float
    group_key: tuple[object, ...]

    def __post_init__(self) -> None:
        if self.page_index < 0:
            raise ValueError("page_index must be zero or greater")
        if self.y_top < 0:
            raise ValueError("y_top must be zero or greater")
