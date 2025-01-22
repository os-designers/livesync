import re


def to_snake_case(name: str) -> str:
    """
    Convert a CamelCase/PascalCase string to snake_case.

    Examples:
        PowerPower -> power_power
        HTTPServer -> http_server
        XMLHTTPRequest -> xml_http_request

    Args:
        name: A string in CamelCase/PascalCase

    Returns:
        The converted snake_case string
    """
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.lower()
