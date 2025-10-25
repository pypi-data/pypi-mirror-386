## Print Dog

Watch a directory and automatically print PDF files as soon as they finish downloading.

### Install

Install directly from the source checkout (editable)

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

### Testing without a printer

- Use `--dry-run` to simulate printing while keeping the watcher logic intact.
- Or provide a custom command that receives the file path, e.g.:

    ```bash
    print-dog --print-command "echo printing {file}"
    ```

### Building a distribution

Use `python -m build` (requires `pip install build`) to produce source and wheel distributions that can be uploaded to PyPI with `twine upload dist/*`. The resulting package installs the `print-dog` command on macOS, Linux, and Windows.
