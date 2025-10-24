import os
import sys

from loguru import logger

logger.remove()
logger.add(
    sink=sys.stdout,
    format=os.environ.get(
        "WXUTIL_LOG_FORMAT",
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
    ),
    level=os.environ.get("WXUTIL_LOG_LEVEL", "DEBUG"),
)
