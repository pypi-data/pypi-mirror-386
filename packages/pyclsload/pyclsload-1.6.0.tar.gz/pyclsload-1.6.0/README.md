# pyclsload

[![CodeFactor](https://www.codefactor.io/repository/github/nbdy/pyclsload/badge)](https://www.codefactor.io/repository/github/nbdy/pyclsload)

Lightweight helpers to load classes from Python source files and directories with sensible defaults, clear errors, and a tiny CLI.

## Why

Avoid repeating the importlib boilerplate when you just want a class from a `.py` file:

```python
from pathlib import Path
from pyclsload import load_cls

inst = load_cls(Path("somefile.py"), "MyClass", foo=1, bar=2)
print(inst)
```

## Features

- Load a class from a file with `load_cls(path, name, *args, **kwargs)`
- Load all classes defined in a directory with `load_dir(directory, arguments=None, on_collision=...)`
  - Only `*.py` files, skips files starting with `_` (like `__init__.py`)
  - Deterministic ordering (lexicographic by filename)
  - Per-class kwargs via the `arguments` mapping
  - Collision policy: `overwrite` (default), `keep_first`, or `error`
- Helpful errors (`FileNotFoundError`, `ModuleLoadError`, `ClassNotFoundError`)
- Simple in-process cache to avoid re-executing the same file repeatedly
- Small CLI to try things out quickly

## Usage

### Load a single class
```python
from pathlib import Path
from pyclsload import load_cls

inst = load_cls(Path("plugins/example.py"), "Plugin", answer=42)
print(inst)
```

### Load a directory of classes
```python
from pathlib import Path
from pyclsload import load_dir

instances = load_dir(Path("plugins"), {
    "Example": {"answer": 42},
})
print(instances["Example"])  # -> Plugin instance
```

### CLI
Install the package and run:

```bash
python -m pyclsload -f path/to/file.py -c ClassName -m run -fa x=1 y=2
```

Or list and instantiate all classes from a directory:

```bash
python -m pyclsload -d path/to/dir
```

Notes:
- `--class-arguments` and `--function-arguments` accept space-separated tokens. Use `key=value` for kwargs; tokens without `=` are passed as positional strings.

## Safety
Executing arbitrary Python files will execute code at import time. Only load trusted code.

## Install

```shell
pip install pyclsload
```

See the [tests](/tests) for usage examples.
