"""Transforms package exports.

Provide both the legacy framePacket helper and the new Framer class for
compatibility with the JS implementation.
"""
from .framer import Framer

try:
	# Some older code expected framePacket; preserve if defined in module
	from .framer import framePacket  # type: ignore
except Exception:
	framePacket = None

__all__ = ["Framer", "framePacket"]
