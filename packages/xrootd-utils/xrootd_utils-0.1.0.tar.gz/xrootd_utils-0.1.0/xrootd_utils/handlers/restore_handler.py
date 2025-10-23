import logging

from XRootD.client import FileSystem
from XRootD.client.flags import PrepareFlags

from .progress_handler import ProgressHandler
from ..common import is_ok


log = logging.getLogger(__name__)


class RestoreHandler(ProgressHandler):
    """
    Subclass to handle logging and cleanup of XRootD restore jobs.
    """

    def __init__(self, file_system: FileSystem, auto_evict: bool = True) -> None:
        super().__init__()
        self.file_system = file_system
        self.auto_evict = auto_evict

    def _handle_success(self, path: str) -> None:
        if self.auto_evict:
            log.debug("Evicting source file: %s", path)
            status, _ = self.file_system.prepare([path], flags=PrepareFlags.EVICT)
            is_ok(status, log, "Evict failed with: %s")
