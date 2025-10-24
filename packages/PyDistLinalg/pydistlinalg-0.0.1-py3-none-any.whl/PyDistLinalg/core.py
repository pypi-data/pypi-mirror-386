# PyDistLinalg/core.py

import dask.array as da
import numpy as np
from .utils import get_dask_client

def _ensure_dask_array(arr, chunks='auto'):
    """Преобразует numpy.ndarray в dask.array, если необходимо."""
    if isinstance(arr, np.ndarray):
        client = get_dask_client()
        if client:
            print(f"Преобразование NumPy-массива в Dask-массив с чанками: {chunks}")
            return da.from_array(arr, chunks=chunks, name=f"numpy_to_dask_{id(arr)}")
        else:
            raise RuntimeError("Dask Client не активен. Пожалуйста, инициализируйте его, "
                               "используя PyDistLinalg.setup_dask_client(), если вы работаете "
                               "с большими массивами или хотите распределенных вычислений.")
    elif isinstance(arr, da.Array):
        return arr
    else:
        raise TypeError("Входные данные должны быть numpy.ndarray или dask.array.Array")

def add(A, B, chunks='auto'):
    """Поэлементное сложение двух распределенных матриц/векторов."""
    A_da = _ensure_dask_array(A, chunks)
    B_da = _ensure_dask_array(B, chunks)
    return A_da + B_da

def subtract(A, B, chunks='auto'):
    """Поэлементное вычитание двух распределенных матриц/векторов."""
    A_da = _ensure_dask_array(A, chunks)
    B_da = _ensure_dask_array(B, chunks)
    return A_da - B_da

def multiply_elementwise(A, B, chunks='auto'):
    """Поэлементное умножение двух распределенных матриц/векторов."""
    A_da = _ensure_dask_array(A, chunks)
    B_da = _ensure_dask_array(B, chunks)
    return A_da * B_da

def dot(A, B, chunks='auto'):
    """Матричное умножение двух распределенных матриц."""
    A_da = _ensure_dask_array(A, chunks)
    B_da = _ensure_dask_array(B, chunks)
    # Dask handles chunking for matrix multiplication efficiently
    return A_da @ B_da # или da.dot(A_da, B_da)

def transpose(A, chunks='auto'):
    """Транспонирование распределенной матрицы."""
    A_da = _ensure_dask_array(A, chunks)
    return A_da.T

def scalar_multiply(A, scalar, chunks='auto'):
    """Умножение распределенной матрицы на скаляр."""
    A_da = _ensure_dask_array(A, chunks)
    return A_da * scalar

def inverse(A, chunks='auto'):
    """Вычисление обратной матрицы (требует осторожности для больших матриц)."""
    A_da = _ensure_dask_array(A, chunks)
    # dask.array.linalg.inv может быть очень ресурсоемким
    return da.linalg.inv(A_da)

def determinant(A, chunks='auto'):
    """Вычисление детерминанта матрицы (может быть очень ресурсоемким)."""
    A_da = _ensure_dask_array(A, chunks)
    return da.linalg.det(A_da)

def norm(A, order=None, chunks='auto'):
    """Вычисление нормы матрицы или вектора."""
    A_da = _ensure_dask_array(A, chunks)
    return da.linalg.norm(A_da, ord=order)