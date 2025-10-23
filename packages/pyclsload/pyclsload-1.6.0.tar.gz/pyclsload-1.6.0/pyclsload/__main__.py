from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pathlib import Path
from typing import Tuple, Dict, Any

from pyclsload import load_cls, load_dir


def _split_args(tokens) -> Tuple[tuple, Dict[str, Any]]:
    """Split a list like ["x", "y=1", "z=true"] into positional args and kwargs (all strings)."""
    if not tokens:
        return (), {}
    args = []
    kwargs = {}
    for t in tokens:
        if isinstance(t, str) and "=" in t:
            k, v = t.split("=", 1)
            kwargs[k] = v
        else:
            args.append(t)
    return tuple(args), kwargs


def main():
    ap = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("-f", "--file", help="Target Python file path", type=str)
    group.add_argument("-d", "--directory", help="Load all files in directory", type=str)

    ap.add_argument("-c", "--cls", help="Class to load (file mode)", type=str)
    ap.add_argument("-m", "--method", help="Instance method to call (file mode)", type=str)
    ap.add_argument("-ca", "--class-arguments", help="Constructor args/kwargs (e.g., a b=2)", nargs='+')
    ap.add_argument("-fa", "--function-arguments", help="Method args/kwargs (e.g., x y=3)", nargs='+')
    a = ap.parse_args()

    if a.file:
        if not a.cls:
            ap.error("--cls is required in --file mode")
        cargs, ckwargs = _split_args(a.class_arguments)
        print(f"Loading and initializing class '{a.cls}' from '{a.file}'.")
        inst = load_cls(Path(a.file), a.cls, *cargs, **ckwargs)

        if a.method:
            fargs, fkwargs = _split_args(a.function_arguments)
            print(f"Executing method '{a.method}'.")
            meth = getattr(inst, a.method)
            result = meth(*fargs, **fkwargs)
            if result is not None:
                print(result)
        else:
            # If no method was provided, just show the instance repr
            print(inst)
    else:
        # Directory mode
        if a.class_arguments:
            ap.error("--class-arguments is not supported with --directory mode (per-class settings not implemented)")
        instances = load_dir(Path(a.directory), {})
        for name, obj in instances.items():
            print(f"{name}: {obj}")


if __name__ == '__main__':
    main()
