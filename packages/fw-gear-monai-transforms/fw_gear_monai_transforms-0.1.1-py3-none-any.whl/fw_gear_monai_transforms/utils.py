"""The utils module."""

import importlib
import sys
from pathlib import Path

from fw_utils import AnyPath


def _load_transform(transform_path: AnyPath):
    """Load transform from the file, return the module.

    Args:
        transformer_path (Path-like): Path to transform module.

    Returns:
        (module): A python module.
    """
    if isinstance(transform_path, str):
        transform_path = Path(transform_path).resolve()
    if transform_path.is_file():
        old_syspath = sys.path[:]
        try:
            sys.path.append(str(transform_path.parent))
            ## Investigate import statement
            mod = importlib.import_module(transform_path.name.split(".")[0])
            mod.filename = str(transform_path)  # type: ignore
        finally:
            sys.path = old_syspath
    else:
        mod = None

    return mod
