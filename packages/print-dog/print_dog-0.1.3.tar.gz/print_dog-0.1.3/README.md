## Print Dog

Watch a directory and automatically print PDF files as soon as they finish downloading.

### Install

Install directly from the source checkout (editable):

```bash
pip install -e .
```

Once published to PyPI, anyone can install with:

```bash
pip install print-dog
```

### Usage

Run the watcher with the console script that gets installed:

```bash
print-dog /path/to/watch --printer My_Printer
```

The folder argument is optional; if omitted the watcher monitors `~/Downloads`. Use `--log-level DEBUG` for verbose logging.

If you omit `--printer`, the system default printer is used. Set it via `lpoptions -d <printer-name>` or list printers with `lpstat -p`.

### Windows + SumatraPDF

To avoid per-user paths when using SumatraPDF:

```powershell
print-dog "C:\Users\%USERNAME%\Downloads" --use-sumatra
```

`--use-sumatra` searches the common installation folders (`%LOCALAPPDATA%`, `%PROGRAMFILES%`, etc.) or the path pointed to by the `SUMATRAPDF_PATH` environment variable. Override the location or CLI flags when needed:

- `--sumatra-path "C:\Custom\SumatraPDF\SumatraPDF.exe"`
- `--sumatra-args "-print-to \"Office Printer\" -silent"`

### Filter by filename

Limit processing to PDFs whose names start with specific prefixes:

```bash
print-dog --allow-prefix Invoice --allow-prefix Statement
```

Only files beginning with `Invoice` or `Statement` will be printed. Supply `--allow-prefix` multiple times to add prefixes.

### Slow downloads

The watcher waits for a PDF to stabilise before printing. Tweak the behaviour when downloads are large or networks are slow:

```bash
print-dog --download-timeout 1200 --stable-checks 6 --poll-interval 1.5
```

- `--download-timeout` (seconds) controls the maximum time to wait.
- `--stable-checks` is the number of consecutive unchanged size checks required.
- `--poll-interval` (seconds) adjusts how often the file size is checked.
- Temporary files such as `.crdownload` or `.part` are ignored until they disappear, so browsers that rename at the end (Chrome, Edge, Firefox) are handled gracefully.

### Testing without a printer

- Use `--dry-run` to simulate printing while keeping the watcher logic intact.
- Or provide a custom command that receives the file path, e.g.:

    ```bash
    print-dog --print-command "echo printing {file}"
    ```

Environment variables and `~` are expanded automatically inside `--print-command`, so Windows users can rely on `%LOCALAPPDATA%\SumatraPDF\SumatraPDF.exe`.

### Building a distribution

Use `python -m build` (requires `pip install build`) to produce source and wheel distributions that can be uploaded to PyPI with `twine upload dist/*`. The resulting package installs the `print-dog` command on macOS, Linux, and Windows.

For repeatable releases, the repo ships `scripts/release.sh`. Run `./scripts/release.sh 0.1.x` from a clean git tree; it bumps the version, builds, runs `twine check`, uploads, and tags. Set `TWINE_USERNAME=__token__` and `TWINE_PASSWORD=<pypi-token>` beforehand.

### Platform helpers

- **Windows**: run `scripts\run-print-dog.bat` (uses `py -3.14`) or `scripts\run-print-dog-simple.bat` (uses the default `python`). Both scripts upgrade the package then launch the watcher; create shortcuts for quick access and edit the `PRINT_ARGS` variable to set prefixes or printers.
- **macOS**: run `scripts/run-print-dog-macos.sh`. It upgrades the package and starts the watcher. Export `PYTHON_BIN`, `WATCH_DIR`, or `PRINT_ARGS` before execution to override defaults. Make it executable with `chmod +x` and launch manually or via Automator/launchd.
