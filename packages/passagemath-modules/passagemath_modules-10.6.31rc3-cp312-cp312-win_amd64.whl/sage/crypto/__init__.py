# sage_setup: distribution = sagemath-modules
# start delvewheel patch
def _delvewheel_patch_1_11_2():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'passagemath_modules.libs'))):
        os.add_dll_directory(libs_dir)


_delvewheel_patch_1_11_2()
del _delvewheel_patch_1_11_2
# end delvewheel patch
from sage.misc.lazy_import import lazy_import
lazy_import('sage.crypto.lattice', 'gen_lattice')
