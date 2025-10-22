"""Duckrun - Lakehouse task runner powered by DuckDB"""

from duckrun.core import Duckrun

__version__ = "0.2.9.dev5"

# Expose unified connect method at module level
connect = Duckrun.connect

__all__ = ["Duckrun", "connect"]