from __future__ import annotations

from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterable, Literal, Mapping, Optional, Union
from inspect import getmembers, isclass


# Simple in-process cache to avoid re-executing the same file repeatedly
_MODULE_CACHE: Dict[str, ModuleType] = {}


class ModuleLoadError(RuntimeError):
    """Raised when a Python module cannot be loaded from a given path."""


class ClassNotFoundError(LookupError):
    """Raised when the requested class is not defined in the loaded module."""


def _as_path(path: Union[str, Path]) -> Path:
    return path if isinstance(path, Path) else Path(path)


def load_module(path: Union[str, Path], *, use_cache: bool = True) -> ModuleType:
    """
    Load a Python module from a file path.

    - Accepts str or Path.
    - Validates existence and file type.
    - Only supports .py files.
    - Caches loaded modules (by absolute path) within the current process when use_cache=True.

    :param path: Path to a .py file
    :param use_cache: Whether to return a cached module if already loaded
    :return: The loaded module object
    :raises FileNotFoundError: if the path does not exist
    :raises IsADirectoryError: if the path points to a directory
    :raises ValueError: if the file does not have a .py suffix
    :raises ModuleLoadError: if importlib cannot load the module
    """
    p = _as_path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    if not p.is_file():
        raise IsADirectoryError(f"Not a file: {p}")
    if p.suffix != ".py":
        raise ValueError(f"Only .py files are supported, got: {p.suffix} for {p}")

    key = str(p.resolve())
    if use_cache and key in _MODULE_CACHE:
        return _MODULE_CACHE[key]

    name = p.stem
    spec = spec_from_file_location(name, str(p))
    if spec is None or spec.loader is None:
        raise ModuleLoadError(f"Could not create a module spec for {p}")
    mod = module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        raise ModuleLoadError(f"Failed to execute module {p}: {e}") from e

    if use_cache:
        _MODULE_CACHE[key] = mod
    return mod


def get_class_names(module: ModuleType) -> list[str]:
    """Return class names defined in the given module (not imported ones)."""
    return [name for name, obj in getmembers(module, isclass) if getattr(obj, "__module__", None) == module.__name__]


def load_cls(path: Union[str, Path], name: str, *args, **kwargs):
    """
    Load and instantiate a class by name from a Python source file.

    :param path: Path to file containing the class (str or Path)
    :param name: Class name to instantiate
    :param args: Positional arguments to pass to the constructor
    :param kwargs: Keyword arguments to pass to the constructor
    :return: Instantiated class object
    :raises ClassNotFoundError: if the class name is not found in the module
    """
    module = load_module(path)
    try:
        cls = getattr(module, name)
    except AttributeError as e:
        raise ClassNotFoundError(f"Class '{name}' not found in {path}") from e
    if not isclass(cls):
        raise ClassNotFoundError(f"Attribute '{name}' in {path} is not a class")
    return cls(*args, **kwargs)


def load_dir(
    directory: Union[str, Path],
    arguments: Optional[dict[str, dict[str, Any]]] = None,
    *,
    on_collision: Literal["overwrite", "error", "keep_first"] = "overwrite",
) -> dict[str, Any]:
    """
    Load and instantiate classes from all Python files in a directory.

    - Only scans files matching *.py
    - Skips files whose names start with '_' (e.g., __init__.py)
    - Deterministic: files are processed in lexicographic order

    :param directory: Directory to load modules from
    :param arguments: Optional per-class kwargs mapping {ClassName: {kw: value}}
    :param on_collision: Policy when multiple files define the same class name:
        - "overwrite" (default): last one wins
        - "error": raise a ValueError
        - "keep_first": keep the first occurrence, ignore later ones
    :return: Mapping of class name to instantiated object
    """
    arguments = arguments or {}
    d = _as_path(directory)
    if not d.exists():
        raise FileNotFoundError(f"Directory not found: {d}")
    if not d.is_dir():
        raise NotADirectoryError(f"Not a directory: {d}")

    results: dict[str, Any] = {}

    files = sorted([p for p in d.glob("*.py") if not p.name.startswith("_")])
    for path in files:
        mod = load_module(path)
        for name in get_class_names(mod):
            kwargs = arguments.get(name, {})
            instance = load_cls(path, name, **kwargs)
            if name in results:
                if on_collision == "error":
                    raise ValueError(f"Duplicate class name '{name}' found in directory {d}")
                if on_collision == "keep_first":
                    continue
            results[name] = instance
    return results


__all__ = [
    "load_module",
    "get_class_names",
    "load_cls",
    "load_dir",
    "ModuleLoadError",
    "ClassNotFoundError",
]
