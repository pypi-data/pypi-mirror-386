from importlib.metadata import PackageNotFoundError, version as _version

try:
    __version__ = _version("vise-logger")   # distribution name (hyphen)
except PackageNotFoundError:
    __version__ = "unknown"               # e.g., running from a checkout
