import json
import logging
import os
from time import sleep
from typing import Generator

from XRootD.client import CopyProcess, FileSystem, URL
from XRootD.client.flags import DirListFlags, PrepareFlags, QueryCode, StatInfoFlags
from XRootD.client.responses import StatInfo

from .common import AutoRemove, is_ok
from .handlers.backup_handler import BackupHandler
from .handlers.restore_handler import RestoreHandler


log = logging.getLogger(__name__)


class Client:

    def __init__(self, url_str: str):
        """
        Args:
            url_str (str): URL of the XRootD server
        """
        self.url = URL(url_str)
        self.file_system = FileSystem(self.url.hostid)

    def backup(
        self,
        source_top: str,
        auto_remove: AutoRemove = AutoRemove.NEVER,
    ) -> dict[str, list[str]]:
        """
        Creates and runs a CopyProcess for all files within source_top to backup
        storage.

        Args:
            source_top (str): Local, absolute path to the top level directory to backup.
            auto_remove (AutoRemove, optional):
                When to remove local copy of the data, either when it is CACHED
                remotely, is BACKED_UP remotely, or NEVER. Defaults to AutoRemove.NEVER.

        Returns:
            dict[str, list[str]]:
                dict containing the list of paths that 'succeeded' when copied, 'failed'
                when copied, and were 'removed' from local storage due to the
                auto_remove condition.
        """
        copy_process = CopyProcess()
        files_found = False
        removed = []
        for dirpath, _dirnames, filenames in os.walk(source_top):
            for filename in filenames:
                source = os.path.join(dirpath, filename)
                relative_path = os.path.relpath(
                    path=source,
                    start=source_top,
                )
                remote_path = os.path.join(self.url.path, relative_path)
                status, stat_info = self.file_system.stat(remote_path)
                if status.errno == 3011:  # No such file of directory, so archive it
                    files_found = True
                    copy_process.add_job(
                        source=source,
                        target=os.path.join(str(self.url), relative_path),
                        mkdir=True,
                    )
                elif is_ok(status, log, "Stat failed with %s"):
                    Client._handle_existing_file(
                        auto_remove,
                        source,
                        relative_path,
                        stat_info,
                        removed,
                    )

        results = {"succeeded": [], "failed": [], "removed": removed}
        if not files_found:
            log.warning("No files found in %s", source_top)
            return results

        log.info("Starting copy")
        handler = BackupHandler(auto_remove=auto_remove)
        copy_process.prepare()
        copy_process.run(handler=handler)

        results["succeeded"] = handler.succeeded
        results["failed"] = handler.failed
        return results

    def restore(
        self,
        source_top: str,
        target_top: str,
        poll_seconds: int = 60,
        auto_evict: bool = False,
    ) -> dict[str, list[str]]:
        """
        Creates and runs a CopyProcess for all files within source_top from backup
        storage to target_top on local storage.

        Args:
            source_top (str): Remote path to directory to restore from (or single file).
            target_top (str):
                Local, absolute path to the top level directory to restore to.
            poll_seconds (int, optional):
                Number of seconds to sleep between XRootD queries. Defaults to 60.
            auto_evict (bool, optional):
                Whether to evict remote copy of the data once transfer completes.
                Defaults to False.

        Returns:
            dict[str, list[str]]:
                dict containing the list of paths that 'succeeded' when copied and
                'failed' when copied.
        """
        Client._validate_poll_seconds(poll_seconds)

        path = os.path.join(self.url.path, source_top)
        file_dict = {}
        for filepath in self._dirlist(path=path):
            relative_path = os.path.relpath(path=filepath, start=self.url.path)
            source = os.path.join(str(self.url), relative_path)
            source_path_only = os.path.join(self.url.path, relative_path)
            target = os.path.join(target_top, relative_path)
            file_dict[source_path_only] = {"source": source, "target": target}

        if len(file_dict) == 0:
            log.warning("No files found in %s", source_top)
            return {"succeeded": [], "failed": []}

        files = list(file_dict.keys())
        status, response = self.file_system.prepare(files, flags=PrepareFlags.STAGE)

        if is_ok(status, log, "Prepare failed with: %s"):
            request_id = response.strip(b"\x00").decode()
            copy_process = CopyProcess()
            while len(file_dict) > 0:
                self._poll_online(file_dict, request_id, copy_process, poll_seconds)

            log.info("All files prepared, starting copy")
            copy_process.prepare()
            handler = RestoreHandler(
                file_system=self.file_system,
                auto_evict=auto_evict,
            )
            copy_process.run(handler=handler)
            return {"succeeded": handler.succeeded, "failed": handler.failed}
        else:
            return {"succeeded": [], "failed": files}

    def _dirlist(self, path: str) -> Generator[str, None, None]:
        """Recursively list all files on a remote XRootD server.

        Args:
            path (str): Absolute path on the remote XRootD server.

        Yields:
            Generator[str, None, None]: Generator of absolute file paths.
        """
        status, directory_list = self.file_system.dirlist(path, DirListFlags.STAT)
        if directory_list is None:
            # Might be a complete path to a file not a directory
            status, stat_info = self.file_system.stat(path)
            ok = is_ok(status, log, "Dirlist and stat failed for %s with: %s", path)
            if ok and not stat_info.flags & StatInfoFlags.IS_DIR:
                yield path
        else:
            # Iterate over contents of the directory
            for entry in directory_list:
                full_path = os.path.join(path, entry.name)
                if entry.statinfo.flags & StatInfoFlags.IS_DIR:
                    for filepath in self._dirlist(full_path):
                        yield filepath
                else:
                    yield full_path

    def _poll_online(
        self,
        file_dict: dict[str, str],
        request_id: str,
        copy_process: CopyProcess,
        sleep_seconds: float = 60,
    ) -> None:
        """
        Use `file_system` to stat which files in `file_dict` are online, and add these
        to the `copy_process`.

        Args:
            file_dict (dict[str, str]): Record of all pending files to query.
            request_id (str): Prepare request id.
            copy_process (CopyProcess): CopyProcess to add prepared files to.
            sleep_seconds (float, optional):
                Number of seconds to sleep between XRootD queries. Defaults to 60.
        """
        n_files = len(file_dict)
        msg = "Waiting %s seconds for %s files to be prepared"
        log.info(msg, sleep_seconds, n_files)
        sleep(sleep_seconds)
        query = "\n".join(file_dict.keys())
        arg = f"{request_id}\n{query}"
        status, response = self.file_system.query(QueryCode.PREPARE, arg)
        if is_ok(status, log, "Query failed with: %s"):
            response_dict = json.loads(response)
            for file_response in response_dict["responses"]:
                Client._parse_response(file_dict, copy_process, file_response)

    @staticmethod
    def _handle_existing_file(
        auto_remove: AutoRemove,
        source: str,
        relative_path: str,
        stat_info: StatInfo,
        removed: list[str],
    ) -> None:
        """
        Args:
            auto_remove (AutoRemove):
                When to remove local copy of the data, either when it is CACHED
                remotely, is BACKED_UP remotely, or NEVER.
            source (str): Absolute local filepath.
            relative_path (str):
                Path relative to the top level directory, only used for logging.
            stat_info (StatInfo): StatInfo about the file in XRootD.
            removed (list[str]):
                list of paths which have been removed from local storage due to the
                auto_remove setting. Will be modified in place if source is removed.
        """
        if (
            auto_remove == AutoRemove.BACKED_UP
            and stat_info.flags & StatInfoFlags.BACKUP_EXISTS
        ):
            log.info("File %s has XRootD backup, removing local copy", relative_path)
            os.remove(source)
            removed.append(source)
        elif auto_remove == AutoRemove.CACHED:
            log.info("File %s in XRootD cache, removing local copy", relative_path)
            os.remove(source)
            removed.append(source)
        else:
            log.warning("File %s already archived, skipping", relative_path)

    @staticmethod
    def _validate_poll_seconds(poll_seconds: int) -> None:
        """
        Args:
            poll_seconds (int): Number of seconds to sleep between XRootD queries.

        Raises:
            ValueError: if poll_seconds < 0
        """
        if poll_seconds < 0:
            raise ValueError("poll_seconds cannot be negative")

    @staticmethod
    def _parse_response(
        file_dict: dict[str, str],
        copy_process: CopyProcess,
        file_response: dict,
    ) -> None:
        """
        If file is online, adds it to copy_process.
        If there is a problem with the file, logs an error.
        If there is a pending prepare request, does nothing.

        Args:
            file_dict (dict[str, str]): Record of all pending files to query.
            copy_process (CopyProcess): CopyProcess to add prepared files to.
            file_response (dict): Response from XRootD query containing the file status.
        """
        path = file_response["path"]
        error_text = file_response["error_text"]
        if error_text:
            log.warning("File %s had error: %s", path, error_text)
            file_dict.pop(path)
        elif not file_response["path_exists"]:
            log.warning("File %s does not exist", path)
            file_dict.pop(path)
        elif file_response["online"]:
            log.debug("File %s online", path)
            file_entry = file_dict.pop(path)
            source = file_entry["source"]
            target = file_entry["target"]
            copy_process.add_job(source=source, target=target, mkdir=True)
        elif not file_response["requested"] or not file_response["has_reqid"]:
            log.warning("File %s not requested for staging", path)
            file_dict.pop(path)
