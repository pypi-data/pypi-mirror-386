import gstaichi
from gstaichi._lib.utils import ti_python_core as _ti_python_core

_type_factory = _ti_python_core.get_type_factory_instance()


class CompoundType:
    def from_kernel_struct_ret(self, launch_ctx, index: tuple):
        raise NotImplementedError()


# TODO: maybe move MatrixType, StructType here to avoid the circular import?
def matrix(n=None, m=None, dtype=None):
    """Creates a matrix type with given shape and data type.

    Args:
        n (int): number of rows of the matrix.
        m (int): number of columns of the matrix.
        dtype (:mod:`~gstaichi.types.primitive_types`): matrix data type.

    Returns:
        A matrix type.

    Example::

        >>> mat2x2 = ti.types.matrix(2, 2, ti.f32)  # 2x2 matrix type
        >>> M = mat2x2([[1., 2.], [3., 4.]])  # an instance of this type
    """
    return gstaichi.lang.matrix.MatrixType(n, m, 2, dtype)  # type: ignore


def vector(n=None, dtype=None):
    """Creates a vector type with given shape and data type.

    Args:
        n (int): dimension of the vector.
        dtype (:mod:`~gstaichi.types.primitive_types`): vector data type.

    Returns:
        A vector type.

    Example::

        >>> vec3 = ti.types.vector(3, ti.f32)  # 3d vector type
        >>> v = vec3([1., 2., 3.])  # an instance of this type
    """
    return gstaichi.lang.matrix.VectorType(n, dtype)  # type: ignore


def struct(**kwargs):
    """Creates a struct type with given members.

    Args:
        kwargs (dict): a dictionary contains the names and types of the
            struct members.

    Returns:
        A struct type.

    Example::

        >>> vec3 = ti.types.vector(3, ti.f32)
        >>> sphere = ti.types.struct(center=vec3, radius=float)
        >>> s = sphere(center=vec3([0., 0., 0.]), radius=1.0)
    """
    return gstaichi.lang.struct.StructType(**kwargs)  # type: ignore


__all__ = ["matrix", "vector", "struct"]
