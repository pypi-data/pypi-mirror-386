'''
"vendorizing" the following package: https://github.com/Maarten-vd-Sande/qnorm

(
MIT License

Copyright (c) 2020, Maarten van der Sande

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
)


Changes:
-- Only focused on the functions that I use in PalmettoBUG (quantile_normalize) -- remove anything not needed for that
-- Joined all files into one (.util import in the original ---> .util functions moved into this file)
-- Removed multiple dispatch (I only pass in numpy arrays to qnorm) and pandas check
-- Removed unused imports
-- add __all__ for docs
-- commented out code for handling ncpus > 1 (multiprocessing), as palmettobug was not using it. This will 'improve' code coverage, and if multiprocessing is desired again
    the code can be un-commented out

'''
__all__ = []
from typing import Union
#from multiprocessing import Pool, RawArray

import numba
import numpy as np


#def _parallel_argsort(_array, ncpus, dtype):
 #   """
 #   private argsort function of qnorm that works with multiple cpus
 #   """
    # multiproces sorting
    # first we make a shared array
#    data_shared = RawArray(
#        np.ctypeslib.as_ctypes_type(dtype), _array.shape[0] * _array.shape[1]
#    )
    # and wrap it with a numpy array and fill it with our data
#    data = np.frombuffer(data_shared, dtype=dtype).reshape(_array.shape)
#    np.copyto(data, _array.astype(dtype))

    # now multiprocess sort
#    with Pool(
#        processes=ncpus,
#        initializer=_worker_init,
#        initargs=(data_shared, dtype, data.shape),
#    ) as pool:
#        sorted_idx = np.array(
#            pool.map(_worker_sort, range(data.shape[1])), dtype=np.int64
#        ).T
#    return data, sorted_idx

#var_dict = {}
#def _worker_init(X, X_dtype, X_shape):
#    """
#    helper function to pass our reference of X to the sorter
#    """
#    var_dict["X"] = X
#    var_dict["X_dtype"] = X_dtype
#    var_dict["X_shape"] = X_shape


#def _worker_sort(i):
#    """
#    argsort a single axis
#    """
#    X_np = np.frombuffer(var_dict["X"], dtype=var_dict["X_dtype"]).reshape(
#        var_dict["X_shape"]
#    )
#    return np.argsort(X_np[:, i])

def quantile_normalize(
    _data: np.ndarray,
    axis: int = 1,
    target: Union[None, np.ndarray] = None,
    ncpus: int = 1,
) -> np.ndarray:
    # check for supported dtypes
    if not np.issubdtype(_data.dtype, np.number):
        raise ValueError(
            f"The type of your data ({_data.dtype}) is is not "
            f"supported, and might lead to undefined behaviour. "
            f"Please use numeric data only."
        )
    # numba does not (yet) support smaller
    elif any(
        np.issubdtype(_data.dtype, dtype) for dtype in [np.int32, np.float32]
    ):
        dtype = np.float32
    else:
        dtype = np.float64

    # take a transposed view of our data if axis is one
    if axis == 0:
        _data = np.transpose(_data)
    elif axis == 1:
        pass
    else:
        raise ValueError(
            f"qnorm only supports 2 dimensional data, so the axis"
            f"has to be either 0 or 1, but you set axis to "
            f"{axis}."
        )

    # sort the array, single process or multiprocessing
    if ncpus == 1:
        # single process sorting
        data = _data.astype(dtype=dtype)
        # we do the sorting outside of numba because the numpy implementation
        # is faster, and numba does not support the axis argument.
        sorted_idx = np.argsort(data, axis=0)
    #elif ncpus > 1:
        # multiproces sorting
    #    data, sorted_idx = _parallel_argsort(_data, ncpus, dtype)
    else:
        raise ValueError("The number of cpus needs to be a positive integer.")

    sorted_val = np.take_along_axis(data, sorted_idx, axis=0)

    if target is None:
        # if no target supplied get the (sorted) rowmeans
        target = np.mean(sorted_val, axis=1)
    else:
        # otherwise make sure target is correct data type and shape
        if not isinstance(target, np.ndarray):
            try:
                target = np.array(target)
            except Exception:
                raise ValueError(
                    "The target could not be converted to a " "numpy.ndarray."
                )
        if target.ndim != 1:
            raise ValueError(
                f"The target array should be a 1-dimensionsal vector, however "
                f"you supplied a vector with {target.ndim} dimensions"
            )
        if target.shape[0] != data.shape[0]:
            raise ValueError(
                f"The target array does not contain the same amount of values "
                f"({target.shape[0]}) as the data contains rows "
                f"({data.shape[0]})"
            )
        if not np.issubdtype(target.dtype, np.number):
            raise ValueError(
                f"The type of your target ({data.dtype}) is is not "
                f"supported, and might lead to undefined behaviour. "
                f"Please use numeric data only."
            )
        target = np.sort(target.astype(dtype=dtype))

    final_res = _numba_accel_qnorm(data, sorted_idx, sorted_val, target)
    if axis == 0:
        final_res = final_res.T
    return final_res


@numba.jit(nopython=True, fastmath=True, cache=True)
def _numba_accel_qnorm(
    qnorm: np.ndarray,
    sorted_idx: np.ndarray,
    sorted_val: np.ndarray,
    target: np.ndarray,
) -> np.ndarray:
    """
    numba accelerated "actual" qnorm normalization.
    """
    # get the shape of the input
    n_rows = qnorm.shape[0]
    n_cols = qnorm.shape[1]

    for col_i in range(n_cols):
        i = 0
        # we fill out a column not from lowest index to highest index,
        # but we fill out qnorm from lowest value to highest value
        while i < n_rows:
            n = 0
            val = 0.0
            # since there might be duplicate numbers in a column, we search for
            # all the indices that have these duplcate numbers. Then we take
            # the mean of their rowmeans.
            while (
                i + n < n_rows
                and sorted_val[i, col_i] == sorted_val[i + n, col_i]
            ):
                val += target[i + n]
                n += 1

            # fill out qnorm with our new value
            if n > 0:
                val /= n
                for j in range(n):
                    idx = sorted_idx[i + j, col_i]
                    qnorm[idx, col_i] = val

            i += n

    return qnorm