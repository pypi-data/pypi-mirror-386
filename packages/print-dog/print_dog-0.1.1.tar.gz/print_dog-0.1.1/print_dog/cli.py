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
SUMATRA_DEFAULT_ARGS: Final = "-print-to-default -silent"


def find_sumatra_executable(path_hint: str | None = None) -> Path | None:
    """Best-effort search for SumatraPDF.exe on Windows systems."""
    candidates: list[Path] = []

    def _add(path_str: str | None) -> None:
        if not path_str:
            return
        expanded = os.path.expandvars(os.path.expanduser(path_str))
        candidates.append(Path(expanded))

    _add(path_hint)
    _add(os.environ.get("SUMATRAPDF_PATH"))

    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            _add(os.path.join(local_app_data, "SumatraPDF", "SumatraPDF.exe"))

        for env_name in ("PROGRAMFILES", "PROGRAMFILES(X86)", "ProgramW6432"):
            base = os.environ.get(env_name)
            if base:
                _add(os.path.join(base, "SumatraPDF", "SumatraPDF.exe"))

    exe_in_path = shutil.which("SumatraPDF.exe")
    if exe_in_path:
        _add(exe_in_path)

    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate

    return None


def build_sumatra_command(executable: Path, args: str | None) -> str:
    flags = args.strip() if args else SUMATRA_DEFAULT_ARGS
    command = f'"{executable}" {flags}'.strip()
    if "{file}" not in command:
        command = f"{command} {{file}}"
    return command


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
    expanded = os.path.expandvars(os.path.expanduser(command_template))
    parts = shlex.split(expanded, posix=(os.name != "nt"))
    placeholder_present = any("{file}" in part for part in parts)
    args = [part.replace("{file}", str(path)) for part in parts]
    if not placeholder_present:
        args.append(str(path))
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
    parser.add_argument(
        "--use-sumatra",
        action="store_true",
        help="(Windows only) Automatically invoke SumatraPDF for printing.",
    )
    parser.add_argument(
        "--sumatra-path",
        help="Path to SumatraPDF.exe. Used with --use-sumatra or as a fallback search hint.",
    )
    parser.add_argument(
        "--sumatra-args",
        help=(
            "Extra arguments passed to SumatraPDF when --use-sumatra is set."
            f" Defaults to: {SUMATRA_DEFAULT_ARGS!r}"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    if args.use_sumatra and args.print_command:
        parser.error("--use-sumatra cannot be combined with --print-command.")

    if args.use_sumatra and args.printer:
        parser.error("--use-sumatra manages the printer; remove --printer or set --sumatra-args.")

    print_command = args.print_command
    if args.use_sumatra:
        sumatra_executable = find_sumatra_executable(args.sumatra_path)
        if not sumatra_executable:
            raise SystemExit(
                "Could not locate SumatraPDF.exe. Install SumatraPDF, set SUMATRAPDF_PATH,"
                " or provide --sumatra-path."
            )
        print_command = build_sumatra_command(sumatra_executable, args.sumatra_args)
        LOGGER.info("Using SumatraPDF at %s", sumatra_executable)

    watch_dir = Path(args.folder).expanduser().resolve()
    if not watch_dir.exists():
        raise SystemExit(f"Folder does not exist: {watch_dir}")

    if not watch_dir.is_dir():
        raise SystemExit(f"Not a directory: {watch_dir}")

    LOGGER.info("Watching %s for new PDF files...", watch_dir)

    event_handler = PdfPrintHandler(
        printer=args.printer,
        print_command=print_command,
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
