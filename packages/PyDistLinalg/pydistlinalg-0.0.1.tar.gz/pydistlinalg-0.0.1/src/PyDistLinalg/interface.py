# __init__.py будет импортировать ключевые функции
from .utils import setup_dask_client, close_dask_client, create_random_dask_matrix
from .core import add, subtract, dot, transpose, inverse, determinant, norm
from .decompositions import cholesky, qr, svd, eigh
from .solvers import solve
from .config import DEFAULT_CHUNKS