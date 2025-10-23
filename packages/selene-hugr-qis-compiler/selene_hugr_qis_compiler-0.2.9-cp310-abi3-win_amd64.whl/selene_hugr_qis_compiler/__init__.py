"""""" # start delvewheel patch
def _delvewheel_patch_1_11_2():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'selene_hugr_qis_compiler.libs'))):
        os.add_dll_directory(libs_dir)


_delvewheel_patch_1_11_2()
del _delvewheel_patch_1_11_2
# end delvewheel patch

from .selene_hugr_qis_compiler import (
    HugrReadError,
    check_hugr,
    compile_to_bitcode,
    compile_to_llvm_ir,
)

__all__ = ["compile_to_bitcode", "compile_to_llvm_ir", "check_hugr", "HugrReadError"]

# This is updated by our release-please workflow, triggered by this
# annotation: x-release-please-version
__version__ = "0.2.6"
