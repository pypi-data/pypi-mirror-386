# PyDistLinalg/utils.py

import dask.distributed

_global_client = None


def get_dask_client():
    """Возвращает текущий активный Dask Client или None."""
    global _global_client
    if _global_client and not _global_client.status == 'closed':
        return _global_client
    return None


def setup_dask_client(address=None, **kwargs):
    """
    Устанавливает или подключается к Dask Client.
    Если address=None, запускает локальный клиент.
    """
    global _global_client
    if _global_client:
        print("Закрытие существующего клиента Dask...")
        _global_client.close()

    if address:
        print(f"Подключение к Dask-кластеру по адресу: {address}")
        _global_client = dask.distributed.Client(address, **kwargs)
    else:
        print("Запуск локального Dask-кластера...")
        _global_client = dask.distributed.Client(**kwargs)

    print(f"Dask Dashboard: {_global_client.dashboard_link}")
    return _global_client


def close_dask_client():
    """Закрывает активный Dask Client."""
    global _global_client
    if _global_client:
        print("Закрытие Dask-клиента...")
        _global_client.close()
        _global_client = None
    else:
        print("Dask-клиент не активен.")

def create_random_dask_matrix(shape, chunks, dtype=np.float64):
    """Создает случайную распределенную матрицу Dask."""
    return da.random.random(shape, chunks=chunks, dtype=dtype)

def create_identity_dask_matrix(shape, chunks, dtype=np.float64):
    """Создает единичную распределенную матрицу Dask."""
    return da.eye(shape[0], shape[1], chunks=chunks, dtype=dtype)

def load_from_hdf5(filepath, dataset_name, chunks):
    """Загружает распределенный массив из файла HDF5."""
    return da.from_array(h5py.File(filepath)[dataset_name], chunks=chunks)

# и т.д. для других форматов данных (CSV, Parquet с dask.dataframe)