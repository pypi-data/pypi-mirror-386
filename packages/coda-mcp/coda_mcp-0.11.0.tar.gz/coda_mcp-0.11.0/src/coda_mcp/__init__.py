"""Coda MCP Server - Local DevSecOps MCP Implementation"""

try:
    from importlib.metadata import version as get_version
    __version__ = get_version("coda-mcp")
except ImportError:
    # Python < 3.8 fallback (though we require 3.11+)
    try:
        from importlib_metadata import version as get_version
        __version__ = get_version("coda-mcp")
    except ImportError:
        __version__ = "0.0.0+unknown"
except Exception:
    # Package not installed (development mode)
    __version__ = "0.0.0+dev"
