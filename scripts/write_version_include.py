"""Generate ``installer/_version.iss`` from :data:`src.__version__`.

Inno Setup's preprocessor (ISPP) cannot import Python modules, so we read the
canonical version from the Python package and emit it as an ISPP ``#define``
that ``installer.iss`` includes. Build scripts (``build.ps1`` / ``build.bat``)
invoke this module before calling ISCC, so manual ``python -m scripts.write_version_include``
is the fallback when iterating on ``installer.iss`` alone.

Usage::

    python -m scripts.write_version_include
    python -m scripts.write_version_include --target path/to/version.iss
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = PROJECT_ROOT / "installer" / "_version.iss"


def write_version_include(version: str, target: Path) -> None:
    """Emit ``target`` containing an ISPP ``#define MyAppVersion`` directive."""
    target.parent.mkdir(parents=True, exist_ok=True)
    content = (
        f"; Auto-generated from src/__version__ ({version}). Do not edit by hand.\n"
        f'#define MyAppVersion "{version}"\n'
    )
    target.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate installer/_version.iss from src.__version__."
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help="Where to write the Inno Setup version include (default: installer/_version.iss)",
    )
    args = parser.parse_args()

    from src import __version__

    write_version_include(__version__, args.target)
    print(f"Wrote {args.target} with MyAppVersion={__version__!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
