_instance_counters: dict[str, int] = {}


def generate_name(base_name: str) -> str:
    """
    Generates a unique name by appending an incrementing counter.

    Parameters
    ----------
    base_name : str
        The base name to use for generating the unique name.

    Returns
    -------
    str
        A unique name in the format "{base_name}:{counter}"

    Examples
    --------
    >>> generate_name("sensor")
    'sensor'
    >>> generate_name("sensor")
    'sensor_1'
    >>> generate_name("sensor")
    'sensor_2'
    """
    if base_name not in _instance_counters:
        _instance_counters[base_name] = 0
    counter = _instance_counters[base_name]
    _instance_counters[base_name] += 1
    return f"{base_name}_{counter}" if counter > 0 else base_name
