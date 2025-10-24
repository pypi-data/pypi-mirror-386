try:
    from importlib.metadata import version
    __version__ = version("dochain-block")
except Exception:
    # Fallback for development installs
    __version__ = "unknown"