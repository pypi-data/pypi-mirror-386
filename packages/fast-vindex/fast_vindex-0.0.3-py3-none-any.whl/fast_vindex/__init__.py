from importlib.metadata import version as _version

from fast_vindex.api import patched_vindex

try:
    __version__ = _version("fast_vindex")
except Exception:
    __version__ = "9999"

__all__ = ["patched_vindex"]
