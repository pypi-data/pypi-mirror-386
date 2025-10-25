from __future__ import annotations

import argparse
import logging
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Final, Set

from watchdog.events import FileCreatedEvent, FileMovedEvent, FileSystemEventHandler
from watchdog.observers import Observer


LOGGER: Final = logging.getLogger("print_dog")


class PdfPrintHandler(FileSystemEventHandler):
    """Prints PDFs as they appear in the watched directory."""

    def __init__(
        self,
        printer: str | None,
        print_command: str | None,
        dry_run: bool,
    ) -> None:
        super().__init__()
        self._printer = printer
        self._print_command = print_command
        self._dry_run = dry_run
        self._printed: Set[Path] = set()

    def on_created(self, event: FileCreatedEvent) -> None:
        if not event.is_directory:
            self._handle_path(Path(event.src_path))

    def on_moved(self, event: FileMovedEvent) -> None:
        if not event.is_directory:
            self._handle_path(Path(event.dest_path))

    def _handle_path(self, path: Path) -> None:
        if path.suffix.lower() != ".pdf":
            return

        resolved = path.resolve()
        if resolved in self._printed:
            LOGGER.debug("Skipping %s; already printed.", resolved)
            return

        LOGGER.info("Detected new PDF: %s", resolved)
        if not wait_for_download_completion(resolved):
            LOGGER.warning("Timed out waiting for download to finish: %s", resolved)
            return

        try:
            if self._dry_run:
                LOGGER.info("Dry run enabled; would print %s", resolved)
            else:
                print_pdf(
                    resolved,
                    printer=self._printer,
                    print_command=self._print_command,
                )
        except Exception as exc:  # noqa: BLE001 - log and continue
            LOGGER.exception("Failed to print %s: %s", resolved, exc)
        else:
            if self._dry_run:
                LOGGER.info("Dry run complete for %s", resolved)
            else:
                LOGGER.info("Sent to printer: %s", resolved)
            self._printed.add(resolved)


def wait_for_download_completion(path: Path, timeout: float = 120.0) -> bool:
    """Wait until the file size stops changing, indicating download completion."""
    start = time.time()
    last_size = -1
    stable_checks = 0
    while time.time() - start < timeout:
        if not path.exists():
            time.sleep(0.5)
            continue

        try:
            size = path.stat().st_size
        except OSError:
            time.sleep(0.5)
            continue

        if size == last_size and size > 0:
            stable_checks += 1
            if stable_checks >= 3:
                return True
        else:
            stable_checks = 0
            last_size = size

        time.sleep(0.5)

    return False


def print_pdf(path: Path, *, printer: str | None, print_command: str | None) -> None:
    """Send the PDF to the system print queue."""
    if print_command:
        _print_with_custom_command(path, print_command)
        return

    if sys.platform.startswith("win"):
        _print_on_windows(path)
    else:
        _print_with_lp(path, printer=printer)


def _print_on_windows(path: Path) -> None:
    try:
        os.startfile(path, "print")  # type: ignore[attr-defined]
    except AttributeError as exc:
        raise RuntimeError("Printing is not supported on this platform.") from exc


def _print_with_lp(path: Path, *, printer: str | None) -> None:
    command = shutil.which("lp") or shutil.which("lpr")
    if not command:
        raise RuntimeError(
            "Could not find a printing command. Install CUPS and provide `lp` or `lpr`."
        )
    cmd = [command]
    if printer:
        cmd.extend(["-d", printer])
    cmd.append(str(path))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        hint = (
            "Set a default printer with `lpoptions -d <printer>` or pass --printer."
            if printer is None
            else f"Verify that printer `{printer}` exists with `lpstat -p`."
        )
        raise RuntimeError(f"Print command failed ({exc}). {hint}") from exc


def _print_with_custom_command(path: Path, command_template: str) -> None:
    parts = shlex.split(command_template)
    if "{file}" in command_template:
        args = [part.replace("{file}", str(path)) for part in parts]
    else:
        args = parts + [str(path)]
    subprocess.run(args, check=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Watch a directory and automatically print new PDF files."
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=str(Path.home() / "Downloads"),
        help="Folder to watch for PDF files (default: ~/Downloads).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level.",
    )
    parser.add_argument(
        "--printer",
        help="Printer name to use; otherwise the system default printer is used.",
    )
    parser.add_argument(
        "--print-command",
        help=(
            "Custom command to run for printing. Use {file} as a placeholder or the file path"
            " is appended automatically."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Detect PDFs without sending them to a printer.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    watch_dir = Path(args.folder).expanduser().resolve()
    if not watch_dir.exists():
        raise SystemExit(f"Folder does not exist: {watch_dir}")

    if not watch_dir.is_dir():
        raise SystemExit(f"Not a directory: {watch_dir}")

    LOGGER.info("Watching %s for new PDF files...", watch_dir)

    event_handler = PdfPrintHandler(
        printer=args.printer,
        print_command=args.print_command,
        dry_run=args.dry_run,
    )
    observer = Observer()
    observer.schedule(event_handler, str(watch_dir), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        LOGGER.info("Stopping watcher...")
    finally:
        observer.stop()
        observer.join()
