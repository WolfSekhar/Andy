"""Layouts package for Andy.

Contains the Classic cards layout and abstract BaseLayout.
"""

from .base_layout import BaseLayout
from .classic_layout import ClassicLayout

LAYOUT_CLASSIC = "classic"

__all__ = [
    "BaseLayout",
    "ClassicLayout",
    "LAYOUT_CLASSIC",
]
