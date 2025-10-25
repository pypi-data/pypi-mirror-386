from itertools import product

import dask.array as da
import numpy as np


def _narray_indices(shape):
    """Generate a NumPy array containing the index values."""
    narray = np.empty(shape, dtype=object)
    for indices in product(*(range(s) for s in shape)):
        narray[indices] = str(indices)
    return narray


# def _narray_random(shape, seed=None):
#     """Generate a NumPy array with random values."""
#     rs = np.random.default_rng(seed)
#     return rs.random(shape)


def _darray_indices(shape, chunks=None):
    """Generate a Dask array containing the index values."""
    narray = _narray_indices(shape)
    darray = da.from_array(narray, chunks=chunks)
    return darray


def _darray_random(shape, chunks=None, seed=None):
    """Generate a Dask array with random values."""
    rs = da.random.RandomState(seed=seed)
    return rs.random(shape, chunks=chunks)


def generate_darray(shape, chunks=None, fmt="drandom", seed=None):
    """Generate a dask array of the requested type and format."""
    if fmt == "drandom":
        return _darray_random(shape, chunks, seed)
    elif fmt == "dindices":
        return _darray_indices(shape, chunks)
    else:
        raise ValueError(
            f"Format '{fmt}' not recognized. Use 'drandom', or 'dindices'."
        )


def generate_fancy_indexes(darray: da.Array, n: int, padding: int = 0):
    """Generate a set of random indexes for a given Dask array"""
    offsets = np.arange(-padding, padding)
    indexes = []
    for axis, size in enumerate(darray.shape):
        low, high = padding, size - padding
        base_indices = np.random.randint(low, high, size=(n, 1))
        expanded = base_indices + offsets
        shape = [1] * darray.ndim
        shape[axis] = 2 * padding
        expanded = expanded.reshape((n, *shape))
        indexes.append(expanded)
    return tuple(indexes)


def estimate_graph_size(collections):
    from collections.abc import Iterator

    import dask
    from dask.base import collections_to_expr
    from dask.utils import format_bytes
    from distributed.protocol import serialize, to_serialize
    from distributed.protocol.serialize import Serialized
    from distributed.utils import nbytes

    # issue de distributed/client.py/compute()
    collections = tuple(
        (dask.delayed(a) if isinstance(a, (list, set, tuple, dict, Iterator)) else a)
        for a in collections
    )
    variables = [a for a in collections if dask.is_dask_collection(a)]

    kwargs = {}
    optimize_graph = True
    expr = collections_to_expr(variables, optimize_graph, **kwargs)

    # issue de distributed/client.py/_graph_to_futures()
    expr_ser = Serialized(*serialize(to_serialize(expr), on_error="raise"))
    pickled_size = sum(map(nbytes, [expr_ser.header] + expr_ser.frames))
    return pickled_size, format_bytes(pickled_size)
