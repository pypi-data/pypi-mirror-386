from importlib.metadata import version as _version

from pytcube.core.accessor import PytCubeAccessor
from pytcube.core.grid import GridAccessor
from pytcube.core.point import PointAccessor

try:
    __version__ = _version("pytcube")
except Exception:
    __version__ = "9999"


__all__ = [
    PytCubeAccessor,
    GridAccessor,
    PointAccessor,
]
