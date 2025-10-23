import argparse
import logging
import os

from .client import Client
from .common import AutoRemove


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "url",
        help=(
            "Url for remote XRootD server including top level directory path, "
            "for example root://hostname.domain:1094//path/to/directory"
        ),
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Increase logging level to DEBUG.",
    )
    sub_parsers = parser.add_subparsers(required=True, dest="subcommand")

    backup_parser = sub_parsers.add_parser(
        "backup",
        help="Backup files in local directory to tape.",
    )
    backup_parser.add_argument(
        "source",
        type=str,
        help="Local source path. Directories will be walked to find all nested files.",
    )
    backup_parser.add_argument(
        "--auto-remove",
        "-r",
        choices=[
            AutoRemove.NEVER.value,
            AutoRemove.BACKED_UP.value,
            AutoRemove.CACHED.value,
        ],
        default=AutoRemove.NEVER.value,
        help=(
            "Whether to automatically remove the local copy of a file: 'never', only "
            "when the XRootD server has it 'backed_up', or as soon as the server has a "
            "'cached' copy."
        ),
    )

    restore_parser = sub_parsers.add_parser(
        "restore",
        help="Restore files in a remote directory to tape",
    )
    restore_parser.add_argument(
        "source",
        type=str,
        help=(
            "Remote relative source path. "
            "Directories will be walked to find all nested files."
        ),
    )
    restore_parser.add_argument(
        "target",
        type=str,
        help="Local directory to restore relative paths to.",
    )
    restore_parser.add_argument(
        "--poll-seconds",
        "-s",
        type=int,
        default=60,
        help=(
            "Number of seconds to wait between querying to see if requested files are "
            "online."
        ),
    )
    restore_parser.add_argument(
        "--auto-evict",
        "-e",
        action="store_true",
        help=(
            "Once copied to local storage, automatically evict the online copy cached "
            "on the remote server."
        ),
    )

    args = parser.parse_args()

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    stream_handler.setFormatter(logging.Formatter("%(levelname)8s : %(message)s"))
    logging.basicConfig(level=logging.DEBUG, handlers=[stream_handler])

    x_root_d_client = Client(args.url)
    if args.subcommand == "backup":
        x_root_d_client.backup(
            source_top=os.path.abspath(args.source),
            auto_remove=args.auto_remove,
        )
    elif args.subcommand == "restore":
        x_root_d_client.restore(
            source_top=args.source,
            target_top=os.path.abspath(args.target),
            poll_seconds=args.poll_seconds,
            auto_evict=args.auto_evict,
        )
