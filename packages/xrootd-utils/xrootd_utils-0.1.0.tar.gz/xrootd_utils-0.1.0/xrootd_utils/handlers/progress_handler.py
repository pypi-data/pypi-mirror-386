import logging

from XRootD.client import URL
from XRootD.client.responses import XRootDStatus
from XRootD.client.utils import CopyProgressHandler

from xrootd_utils.common import is_ok


log = logging.getLogger(__name__)


class ProgressHandler(CopyProgressHandler):
    """
    Subclass to handle logging and cleanup of XRootD copy jobs.
    """

    def __init__(self) -> None:
        super().__init__()
        self.jobs = {}
        self.succeeded = []
        self.failed = []

    def begin(
        self,
        jobId: int,  # noqa: N803
        total: int,
        source: URL,
        target: URL,
    ) -> None:
        """Called on the start of each job. Caches the source against jobId.

        Args:
            jobId (int): ID of the job within the CopyProcess.
            source (URL): XRootD URL of the job source.
            target (URL): XRootD URL of the job destination.
        """
        log.debug("Starting job %s of %s: %s", jobId, total, source.path)
        self.jobs[jobId] = source.path

    def end(self, jobId: int, results: dict[str, XRootDStatus]) -> None:  # noqa: N803
        """
        Called on the end of each job. Optionally evicts the file from the XRootD cache.

        Args:
            jobId (int): ID of the job within the CopyProcess.
            results (dict[str, XRootDStatus]): dict containing the status of the job.
        """
        path = self.jobs.pop(jobId)
        if is_ok(results["status"], log, "Copy failed with: %s"):
            log.info("Copy successful: %s", path)
            self.succeeded.append(path)
            self._handle_success(path)
        else:
            self.failed.append(path)

    def update(self, jobId: int, processed: int, total: int) -> None:  # noqa: N803
        """Called with the current number of bytes transferred for the job.

        Args:
            jobId (int): ID of the job within the CopyProcess.
            processed (int): Number of bytes process so far.
            total (int): Number of bytes to process in total.
        """
        msg = "Update on job %s: %s of %s bytes transferred"
        log.debug(msg, jobId, processed, total)

    def _handle_success(self, path: str) -> None: ...
