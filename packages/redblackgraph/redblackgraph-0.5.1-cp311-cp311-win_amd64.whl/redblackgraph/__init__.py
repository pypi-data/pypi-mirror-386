# from .rbm import rb_matrix, Color


# start delvewheel patch
def _delvewheel_patch_1_11_2():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'redblackgraph.libs'))):
        os.add_dll_directory(libs_dir)


_delvewheel_patch_1_11_2()
del _delvewheel_patch_1_11_2
# end delvewheel patch

try:
    from ._version import __version__
except ImportError:
    # Version file not yet generated (e.g., in development without build)
    __version__ = "0.0.0.dev0"

from .core import *
from .sparse import *
from .util import RelationshipFileReader, RedBlackGraphWriter, RbgGraphBuilder
from redblackgraph.types.color import Color

__all__ = ['__version__']
__all__.extend(core.__all__)
__all__.extend(sparse.__all__)
__all__.extend(['RelationshipFileReader', 'RedBlackGraphWriter', 'Color'])
