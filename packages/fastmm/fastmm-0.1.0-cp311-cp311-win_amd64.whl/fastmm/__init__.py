# fastmm - Fast Map Matching for Python


# start delvewheel patch
def _delvewheel_patch_1_11_2():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'fastmm.libs'))):
        os.add_dll_directory(libs_dir)


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
