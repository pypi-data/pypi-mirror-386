# fastmm - Fast Map Matching for Python


# start delvewheel patch
def _delvewheel_patch_1_11_2():
    import ctypes
    import os
    import platform
    import sys
    libs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'fastmm.libs'))
    is_conda_cpython = platform.python_implementation() == 'CPython' and (hasattr(ctypes.pythonapi, 'Anaconda_GetVersion') or 'packaged by conda-forge' in sys.version)
    if sys.version_info[:2] >= (3, 8) and not is_conda_cpython or sys.version_info[:2] >= (3, 10):
        if os.path.isdir(libs_dir):
            os.add_dll_directory(libs_dir)
    else:
        load_order_filepath = os.path.join(libs_dir, '.load-order-fastmm-0.1.1')
        if os.path.isfile(load_order_filepath):
            import ctypes.wintypes
            with open(os.path.join(libs_dir, '.load-order-fastmm-0.1.1')) as file:
                load_order = file.read().split()
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel32.LoadLibraryExW.restype = ctypes.wintypes.HMODULE
            kernel32.LoadLibraryExW.argtypes = ctypes.wintypes.LPCWSTR, ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD
            for lib in load_order:
                lib_path = os.path.join(os.path.join(libs_dir, lib))
                if os.path.isfile(lib_path) and not kernel32.LoadLibraryExW(lib_path, None, 8):
                    raise OSError('Error loading {}; {}'.format(lib, ctypes.FormatError(ctypes.get_last_error())))


_delvewheel_patch_1_11_2()
del _delvewheel_patch_1_11_2
# end delvewheel patch

# Import C++ bindings
from .fastmm import *  # noqa: F401,F403

# Import Python helpers
from .matcher import MapMatcher

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

# C++ classes from bindings
__all__ = [
    # Core classes
    "Network",
    "NetworkGraph",
    "FastMapMatch",
    "FastMapMatchConfig",
    "UBODT",
    "UBODTGenAlgorithm",
    "Trajectory",
    # Geometry classes
    "Point",
    "LineString",
    # Result classes
    "PyMatchResult",
    "PyMatchSegment",
    "PyMatchCandidate",
    "PyMatchPoint",
    "PyMatchSegmentEdge",
    "MatchErrorCode",
    # Python helpers
    "MapMatcher",
]
