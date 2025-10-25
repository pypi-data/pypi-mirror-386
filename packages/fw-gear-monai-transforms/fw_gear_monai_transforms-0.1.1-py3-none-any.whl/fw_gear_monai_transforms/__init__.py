"""The fw_gear_skeleton package."""

from importlib.metadata import version

try:
    __version__ = version(__package__)
except:  # noqa: E722 (bare except)
    pass
