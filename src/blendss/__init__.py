from importlib.metadata import PackageNotFoundError, version

from .blend import blend
from .cli import cli

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # blendss not installed, likely developer mode
    __version__ = None
