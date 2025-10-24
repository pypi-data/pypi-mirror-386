import os

USER_DEFINED_LOG_LEVEL = os.getenv("MCP_EMAIL_SERVER_LOG_LEVEL", "INFO")

os.environ["LOGURU_LEVEL"] = USER_DEFINED_LOG_LEVEL

from loguru import logger  # noqa: E402

__all__ = ["logger"]
