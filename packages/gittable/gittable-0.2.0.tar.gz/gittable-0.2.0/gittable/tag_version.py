from __future__ import annotations

import argparse
import json
import os
import sys
from typing import TYPE_CHECKING

try:
    from functools import cache  # type: ignore
except ImportError:
    from functools import lru_cache as cache
from pathlib import Path
from shlex import quote
from shutil import which
from subprocess import CalledProcessError, list2cmdline

from gittable._utilities import check_output

if TYPE_CHECKING:
    from collections.abc import Iterable


@cache
def _get_env() -> dict[str, str]:
    """
    Get the environment variables
    """
    env: dict[str, str] = os.environ.copy()
    env.pop("PIP_CONSTRAINT", None)
    return env


def _get_hatch_version(
    directory: str | Path = os.path.curdir,
) -> str:
    """
    Get the version of the package using `hatch`, if available
    """
    if isinstance(directory, str):  # pragma: no cover
        directory = Path(directory)
    directory = str(directory.resolve())
    current_directory: str = str(Path.cwd().resolve())
    os.chdir(directory)
    hatch: str = which("hatch") or "hatch"
    output: str = ""
    try:
        # Note: We pass an empty dictionary of environment variables
        # to circumvent configuration issues caused by relative paths
        output = (
            check_output((hatch, "version"), env=_get_env()).strip()
            if hatch
            else ""
        )
    except Exception:  # noqa: S110 BLE001
        pass
    finally:
        os.chdir(current_directory)
    return output


def _get_poetry_version(
    directory: str | Path = os.path.curdir,
) -> str:
    """
    Get the version of the package using `poetry`, if available
    """
    if isinstance(directory, Path):  # pragma: no cover
        directory = str(Path(directory).resolve())
    current_directory: str = str(Path.cwd().resolve())
    os.chdir(directory)
    poetry: str = which("poetry") or "poetry"
    output: str = ""
    try:
        # Note: We pass an empty dictionary of environment variables
        # to prevent configuration issues caused by relative paths
        output = (
            check_output((poetry, "version"), env=_get_env())
            .strip()
            .rpartition(" ")[-1]
            if poetry
            else ""
        )
    except Exception:  # noqa: S110 BLE001
        pass
    finally:
        os.chdir(current_directory)
    return output


def _get_pip_version(
    directory: str | Path = os.path.curdir,
) -> str:
    """
    Get the version of a package using `pip`
    """
    if isinstance(directory, str):  # pragma: no cover
        directory = Path(directory)
    directory = str(directory.resolve())
    command: tuple[str, ...] = ()
    try:
        command = (
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--no-compile",
            "-e",
            directory,
        )
        env: dict[str, str] = os.environ.copy()
        env.pop("PIP_CONSTRAINT", None)
        check_output(command, env=env)
        command = (
            sys.executable,
            "-m",
            "pip",
            "list",
            "--format",
            "json",
            "--path",
            directory,
        )
        return json.loads(check_output(command, env=_get_env()))[0]["version"]
    except Exception as error:  # pragma: no cover
        output: str = ""
        if isinstance(error, CalledProcessError):
            output = (error.output or error.stderr or b"").decode().strip()
            if output:
                output = f"{output}\n"
        current_directory: str = str(Path.cwd().resolve())
        raise RuntimeError(  # noqa: TRY003
            "Unable to determine the project version:\n"  # noqa: EM102
            f"$ cd {quote(current_directory)} && {list2cmdline(command)}\n"
            f"{output}"
        ) from error


def _get_python_project_version(
    directory: str | Path = "",
) -> str:
    """
    Get a python project's version. Currently supports `hatch`, `poetry`, and
    any build tool compatible with `pip`.
    """
    return (
        _get_hatch_version(directory)
        or _get_poetry_version(directory)
        or _get_pip_version(directory)
    )


def tag_version(
    directory: str | Path = os.path.curdir,
    message: str | None = None,
    prefix: str | None = None,
    suffix: str | None = None,
) -> str:
    """
    Tag your project with the package version number *if* no pre-existing
    tag with that version number exists.

    Parameters:
        directory:
        message:
        prefix:
        suffix:

    Returns:
        The version number, including any prefix or suffix.
    """
    if isinstance(directory, str):  # pragma: no cover
        directory = Path(directory)
    directory = str(directory.resolve())
    version: str = _get_python_project_version(directory)
    if prefix:
        version = f"{prefix}{version}"
    if suffix:
        version = f"{version}{suffix}"
    tags: Iterable[str] = map(
        str.strip,
        check_output(("git", "tag"), cwd=directory).strip().split("\n"),
    )
    if version not in tags:  # pragma: no cover
        check_output(
            ("git", "tag", "-a", version, "-m", message or version),
            cwd=directory,
        )
    return version


def main() -> None:  # pragma: no cover
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="gittable tag-version",
        description=(
            "Tag your repo with the package version, if a tag "
            "for that version doesn't already exist."
        ),
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=os.path.curdir,
        type=str,
        help=(
            "Your project directory. If not provided, the current "
            "directory will be used."
        ),
    )
    parser.add_argument(
        "-m",
        "--message",
        default="",
        type=str,
        help=(
            "The tag message. If not provided, the new version number is "
            "used."
        ),
    )
    parser.add_argument(
        "--prefix",
        default="",
        type=str,
        help="A string with which to prefix the version number in the tag.",
    )
    parser.add_argument(
        "--suffix",
        default="",
        type=str,
        help="A string with which to suffix the version number in the tag.",
    )
    arguments: argparse.Namespace = parser.parse_args()
    print(  # noqa: T201
        tag_version(
            directory=arguments.directory,
            message=arguments.message,
            suffix=arguments.suffix,
            prefix=arguments.prefix,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
