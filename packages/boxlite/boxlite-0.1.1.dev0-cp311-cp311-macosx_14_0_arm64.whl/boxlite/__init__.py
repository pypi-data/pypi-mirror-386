"""
BoxLite - Lightweight, secure containerization for any environment.

Following SQLite philosophy: "BoxLite" for branding, "boxlite" for code APIs.
"""

import os
import warnings
from pathlib import Path

# Import core functionality from Rust extension
try:
    from .boxlite import (
        Options,
        BoxOptions,
        Boxlite,
        Box,
        BoxInfo,
    )

    __all__ = [
        "Options",
        "BoxOptions",
        "Boxlite",
        "Box",
        "BoxInfo",
    ]
except ImportError as e:
    warnings.warn(f"BoxLite native extension not available: {e}", ImportWarning)
    __all__ = []

# Import Python convenience wrappers
try:
    from .basebox import BaseBox
    from .codebox import CodeBox
    __all__.extend(["BaseBox", "CodeBox"])
except ImportError:
    pass

# Future specialized containers can be added here at top-level
# Example: BrowserBox (see browserbox.py for implementation template)
# from .browserbox import BrowserBox
# __all__.append("BrowserBox")

__version__ = "0.1.1-dev"
