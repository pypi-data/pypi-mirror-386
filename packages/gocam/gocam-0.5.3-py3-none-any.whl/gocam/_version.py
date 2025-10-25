from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version(__package__)
except PackageNotFoundError:
    # package not installed
    __version__ = "0.0.0"
