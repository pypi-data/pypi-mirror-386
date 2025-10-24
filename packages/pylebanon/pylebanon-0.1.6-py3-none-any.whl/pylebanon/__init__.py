from .lebanon import Lebanon

try:
    from ._version import version as __version__  # type: ignore
except ImportError:
    __version__ = "0.0.0"

__all__ = ["Lebanon"]
