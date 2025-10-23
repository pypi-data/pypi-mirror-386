from enum import StrEnum
from logging import Logger

from XRootD.client.responses import XRootDStatus


class AutoRemove(StrEnum):
    NEVER = "never"
    BACKED_UP = "backed_up"
    CACHED = "cached"


def is_ok(status: XRootDStatus, log: Logger, msg: str, *args) -> bool:
    """Utility function for logging if status.ok is False.

    Args:
        status (XRootDStatus): Status of an XRootD request
        log (Logger): Logger to use if status.ok is False
        msg (str): Message to log if status.ok is False
        *args: Arguments to format msg with

    Returns:
        bool: Value of status.ok
    """
    if status.ok:
        return True
    else:
        log.error(msg, *args, status.message)
        return False
