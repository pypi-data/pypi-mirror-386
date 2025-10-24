# PyDistLinalg/solvers.py

import dask.array as da
from .core import _ensure_dask_array

def solve(A, b, chunks='auto'):
    """
    Решение системы линейных уравнений Ax = b.
    A - квадратная матрица, b - вектор или матрица правой части.
    """
    A_da = _ensure_dask_array(A, chunks)
    b_da = _ensure_dask_array(b, chunks)
    # dask.array.linalg.solve использует подходящие методы в зависимости от A
    return da.linalg.solve(A_da, b_da)