# type: ignore

from typing import Any, Optional, Sequence, Union

from gstaichi._lib import core as _ti_core
from gstaichi._lib.core.gstaichi_python import SNodeCxx
from gstaichi._snode.snode_tree import SNodeTree
from gstaichi.lang import impl, snode
from gstaichi.lang.exception import GsTaichiRuntimeError
from gstaichi.lang.util import warning

_snode_registry = _ti_core.SNodeRegistry()

_Axis = _ti_core.Axis


class FieldsBuilder:
    """A builder that constructs a SNodeTree instance.

    Example::

        x = ti.field(ti.i32)
        y = ti.field(ti.f32)
        fb = ti.FieldsBuilder()
        fb.dense(ti.ij, 8).place(x)
        fb.pointer(ti.ij, 8).dense(ti.ij, 4).place(y)

        # After this line, `x` and `y` are placed. No more fields can be placed
        # into `fb`.
        #
        # The tree looks like the following:
        # (implicit root)
        #  |
        #  +-- dense +-- place(x)
        #  |
        #  +-- pointer +-- dense +-- place(y)
        fb.finalize()
    """

    def __init__(self):
        self.ptr: SNodeCxx = _snode_registry.create_root(impl.get_runtime().prog)
        self.root = snode.SNode(self.ptr)
        self.finalized = False
        self.empty = True
        impl.get_runtime().initialize_fields_builder(self)

    # TODO: move this into SNodeTree
    @classmethod
    def _finalized_roots(cls):
        """Gets all the roots of the finalized SNodeTree.

        Returns:
            A list of the roots of the finalized SNodeTree.
        """
        roots_ptr = []
        size = impl.get_runtime().prog.get_snode_tree_size()
        for i in range(size):
            res = impl.get_runtime().prog.get_snode_root(i)
            roots_ptr.append(snode.SNode(res))
        return roots_ptr

    # TODO: move this to SNodeTree class.
    def deactivate_all(self):
        """Same as :func:`gstaichi.lang.snode.SNode.deactivate_all`"""
        if self.finalized:
            self.root.deactivate_all()
        else:
            warning("""'deactivate_all()' would do nothing if FieldsBuilder is not finalized""")

    def dense(
        self,
        indices: Union[Sequence[_Axis], _Axis],
        dimensions: Union[Sequence[int], int],
    ):
        """Same as :func:`gstaichi.lang.snode.SNode.dense`"""
        self._check_not_finalized()
        self.empty = False
        return self.root.dense(indices, dimensions)

    def pointer(
        self,
        indices: Union[Sequence[_Axis], _Axis],
        dimensions: Union[Sequence[int], int],
    ):
        """Same as :func:`gstaichi.lang.snode.SNode.pointer`"""
        if not _ti_core.is_extension_supported(impl.current_cfg().arch, _ti_core.Extension.sparse):
            raise GsTaichiRuntimeError("Pointer SNode is not supported on this backend.")
        self._check_not_finalized()
        self.empty = False
        return self.root.pointer(indices, dimensions)

    def _hash(self, indices, dimensions):
        """Same as :func:`gstaichi.lang.snode.SNode.hash`"""
        raise NotImplementedError()

    def dynamic(
        self,
        index: Union[Sequence[_Axis], _Axis],
        dimension: Union[Sequence[int], int],
        chunk_size: Optional[int] = None,
    ):
        """Same as :func:`gstaichi.lang.snode.SNode.dynamic`"""
        if not _ti_core.is_extension_supported(impl.current_cfg().arch, _ti_core.Extension.sparse):
            raise GsTaichiRuntimeError("Dynamic SNode is not supported on this backend.")

        if dimension >= 2**31:
            raise GsTaichiRuntimeError(
                f"The maximum dimension of a dynamic SNode cannot exceed the maximum value of a 32-bit signed integer: Got {dimension} > 2**31-1"
            )
        if chunk_size is not None and chunk_size >= 2**31:
            raise GsTaichiRuntimeError(
                f"Chunk size cannot exceed the maximum value of a 32-bit signed integer: Got {chunk_size} > 2**31-1"
            )

        self._check_not_finalized()
        self.empty = False
        return self.root.dynamic(index, dimension, chunk_size)

    def bitmasked(
        self,
        indices: Union[Sequence[_Axis], _Axis],
        dimensions: Union[Sequence[int], int],
    ):
        """Same as :func:`gstaichi.lang.snode.SNode.bitmasked`"""
        if not _ti_core.is_extension_supported(impl.current_cfg().arch, _ti_core.Extension.sparse):
            raise GsTaichiRuntimeError("Bitmasked SNode is not supported on this backend.")
        self._check_not_finalized()
        self.empty = False
        return self.root.bitmasked(indices, dimensions)

    def quant_array(
        self,
        indices: Union[Sequence[_Axis], _Axis],
        dimensions: Union[Sequence[int], int],
        max_num_bits: int,
    ):
        """Same as :func:`gstaichi.lang.snode.SNode.quant_array`"""
        self._check_not_finalized()
        self.empty = False
        return self.root.quant_array(indices, dimensions, max_num_bits)

    def place(self, *args: Any, offset: Optional[Union[Sequence[int], int]] = None):
        """Same as :func:`gstaichi.lang.snode.SNode.place`"""
        self._check_not_finalized()
        self.empty = False
        self.root.place(*args, offset=offset)

    def lazy_grad(self):
        """Same as :func:`gstaichi.lang.snode.SNode.lazy_grad`"""
        # TODO: This complicates the implementation. Figure out why we need this
        self._check_not_finalized()
        self.empty = False
        self.root.lazy_grad()

    def _allocate_adjoint_checkbit(self):
        """Same as :func:`gstaichi.lang.snode.SNode._allocate_adjoint_checkbit`"""
        self._check_not_finalized()
        self.empty = False
        self.root._allocate_adjoint_checkbit()

    def lazy_dual(self):
        """Same as :func:`gstaichi.lang.snode.SNode.lazy_dual`"""
        # TODO: This complicates the implementation. Figure out why we need this
        self._check_not_finalized()
        self.empty = False
        self.root.lazy_dual()

    def finalize(self, raise_warning=True):
        """Constructs the SNodeTree and finalizes this builder.

        Args:
            raise_warning (bool): Raise warning or not."""
        return self._finalize(raise_warning, compile_only=False)

    def _finalize(self, raise_warning, compile_only) -> SNodeTree:
        self._check_not_finalized()
        if self.empty and raise_warning:
            warning("Finalizing an empty FieldsBuilder!")
        self.finalized = True
        impl.get_runtime().finalize_fields_builder(self)
        return SNodeTree(
            _ti_core.finalize_snode_tree(_snode_registry, self.ptr, impl.get_runtime()._prog, compile_only)
        )

    def _check_not_finalized(self):
        if self.finalized:
            raise GsTaichiRuntimeError("FieldsBuilder finalized")
