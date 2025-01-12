import os
import logging
from typing import Any
from typing_extensions import override

logger: logging.Logger = logging.getLogger("livesync")
httpx_logger: logging.Logger = logging.getLogger("httpx")


SENSITIVE_HEADERS = {"api-key", "authorization"}


def _basic_config() -> None:
    logging.basicConfig(
        format="[%(asctime)s - %(name)s:%(lineno)d - %(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def setup_logging() -> None:
    env = os.environ.get("LIVESYNC_LOG")
    if env == "debug":
        _basic_config()
        logger.setLevel(logging.DEBUG)
        httpx_logger.setLevel(logging.DEBUG)
    elif env == "info":
        _basic_config()
        logger.setLevel(logging.INFO)
        httpx_logger.setLevel(logging.INFO)


class SensitiveHeadersFilter(logging.Filter):
    @override
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.args, dict) and "headers" in record.args and isinstance(record.args["headers"], dict):
            record.args["headers"] = {**record.args["headers"]}
            headers: dict[str, Any] = record.args["headers"]
            for header in headers:
                if str(header).lower() in SENSITIVE_HEADERS:
                    headers[header] = "<redacted>"
        return True
