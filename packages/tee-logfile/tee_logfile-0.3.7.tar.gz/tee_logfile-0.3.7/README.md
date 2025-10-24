# tee-logfile

Small Python utility to duplicate process output to a logfile while preserving console output (similar to Unix `tee`).

## Features

- Mirror `stdout` (and optionally `stderr`) to a file and the console.
- Lightweight and easy to integrate into scripts or pipelines.
- Designed for use on macOS and other Unix-like systems.

## Requirements

- Python 3.9+

## Installation

```bash
pip install tee-logfile
```

## Usage

```python
from tee_logfile import Tee

with Tee.context('/path/to/output.log'):
    my_cli_code_to_run()
```

## Development

### release

```bash
poetry version minor
tox -e release
pip install ~/projects/sandbox/tee-logfile
```