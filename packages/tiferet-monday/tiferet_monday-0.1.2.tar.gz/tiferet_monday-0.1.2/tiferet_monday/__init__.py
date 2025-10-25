"""Tiferet Monday Version and Exports"""

# *** exports

# ** app
# Export the main application context and related modules.
# Use a try-except block to avoid import errors on build systems.
try:
    from .proxies import MondayApiRequestsProxy as MondayApiProxy
except:
    pass

# *** version
__version__ = '0.1.2'