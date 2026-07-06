from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class DigitizedPoint:
    """A user-digitized point used for plane fitting."""

    pid: int
    x: float
    y: float
    z: float

    source: str = "map"
    active: bool = True

    orthogonal_residual: Optional[float] = None
    abs_orthogonal_residual: Optional[float] = None

    note: str = ""

    @property
    def xyz(self):
        return (self.x, self.y, self.z)
