"""Top-level package for showtracetable.

Public API:
 - trace_file(path) -> prints ascii trace for a target script
 - SimpleTracer -> tracer class for custom tracing
"""

from __future__ import annotations

from .tracer import SimpleTracer, trace_file

# package version
try:
    from importlib.metadata import version as _pkg_version

    __version__ = _pkg_version("showtracetable")
except Exception:  # pragma: no cover - best effort during editable installs
    __version__ = "0.0.0"

__all__ = ["trace_file", "SimpleTracer", "__version__"]
