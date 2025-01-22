import numpy as np

from ..types import DataType


def infer_dtype(value: DataType) -> type:
    """Infer the dtype from a given value.

    Parameters
    ----------
    value : DataType
        The value to infer dtype from. Can be numpy.ndarray, str, float, int, or bool.

    Returns
    -------
    type
        The inferred dtype of the value.

    Raises
    ------
    TypeError
        If the value type is not supported.
    """
    if isinstance(value, (np.ndarray, np.generic)):
        return value.dtype.type
    elif isinstance(value, str):
        return str
    elif isinstance(value, float):
        return float
    elif isinstance(value, bool):
        return bool
    elif type(value) is int:
        return int
    else:
        raise TypeError(f"Unsupported value type: {type(value)}")
