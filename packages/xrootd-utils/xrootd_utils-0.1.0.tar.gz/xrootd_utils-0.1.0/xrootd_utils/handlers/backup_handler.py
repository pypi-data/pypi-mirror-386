import logging
import os

from .progress_handler import ProgressHandler
from ..common import AutoRemove


log = logging.getLogger(__name__)


class BackupHandler(ProgressHandler):
    """
    Subclass to handle logging and cleanup of XRootD backup jobs.
    """

    def __init__(self, auto_remove: AutoRemove = AutoRemove.NEVER) -> None:
        """
        Args:
            auto_remove (AutoRemove, optional):
                When to remove local copy of the data, either when it is CACHED
                remotely, is BACKED_UP remotely, or NEVER. Defaults to AutoRemove.NEVER.
        """
        super().__init__()
        self.auto_remove = auto_remove
        self.removed = []

    def _handle_success(self, path: str) -> None:
        """
        Called on the end of each job. Uses the cached source to clean up the local
        cache iff requested.

        Args:
            path (str): Local absolute path of a successful job within the CopyProcess.
        """
        if self.auto_remove == AutoRemove.CACHED:
            log.debug("Removing source file: %s", path)
            os.remove(path)
            self.removed.append(path)
