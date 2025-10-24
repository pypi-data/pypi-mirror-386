import subprocess
import sys
from pathlib import Path
import functools
import os

if sys.version_info >= (3, 9):
    # Only available on 3.9 or later, and required on 3.12
    from importlib.resources import files
else:
    import pkg_resources


@functools.cache
def _get_executable(name: str) -> Path:
    if sys.version_info >= (3, 9):
        # Only available in 3.9 or later, and required in 3.12
        possibles = [
            Path(files("clangd") / f"data/bin/{name}{s}")
            for s in ("", ".exe", ".bin", ".dmg")
        ]
    else:
        possibles = [
            Path(pkg_resources.resource_filename("clangd", f"data/bin/{name}{s}"))
            for s in ("", ".exe", ".bin", ".dmg")
        ]
    for exe in possibles:
        if exe.exists():
            if os.environ.get("CLANGD_WHEEL_VERBOSE", None):
                print(f"Found binary: {exe} ")
            return exe

    raise FileNotFoundError(f"No executable found for {name} at\n{possibles}")


def _run(name, *args):
    command = [_get_executable(name)]
    if args:
        command += list(args)
    else:
        command += sys.argv[1:]
    return subprocess.call(command)


def clangd():
    raise SystemExit(_run("clangd"))
