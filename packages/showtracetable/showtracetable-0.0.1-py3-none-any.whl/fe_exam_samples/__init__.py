"""Sample implementations for FE exam-style Python problems.

Each module contains a self-contained script. You can run them directly or import for study.
"""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent


def iter_samples() -> list[Path]:
    """Return a list of available sample script paths."""
    python_dir = PACKAGE_ROOT / "python"
    if not python_dir.exists():
        return []
    return sorted(python_dir.glob("*.py"))


__all__ = ["iter_samples", "PACKAGE_ROOT"]
