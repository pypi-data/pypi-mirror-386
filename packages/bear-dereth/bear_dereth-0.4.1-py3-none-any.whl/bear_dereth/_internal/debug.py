from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lazy_bear import LazyLoader as Lazy

from bear_dereth._internal._info import METADATA, _get_package_info, _Package  # type: ignore[import]

if TYPE_CHECKING:
    from importlib.metadata import distributions
    from os import environ, getenv
    import platform
    import sys
    from sys import _version_info as version_info  # type: ignore[import]

    from rich.console import Console
else:
    sys = Lazy("sys")
    platform = Lazy("platform")
    environ, getenv = Lazy("os").to_many("environ", "getenv")
    Console = Lazy("rich.console").to("Console")
    distributions = Lazy("importlib.metadata").to("distributions")


@dataclass(slots=True, frozen=True)
class _Variable:
    """Dataclass describing an environment variable."""

    name: str
    """Variable name."""
    value: str
    """Variable value."""


@dataclass(slots=True)
class _Environment:
    """Dataclass to store environment information."""

    interpreter_name: str
    """Python interpreter name."""
    interpreter_version: str
    """Python interpreter version."""
    interpreter_path: str
    """Path to Python executable."""
    platform: str
    """Operating System."""
    packages: list[_Package]
    """Installed packages."""
    variables: list[_Variable]
    """Environment variables."""


def _interpreter_name_version() -> tuple[str, str]:
    if hasattr(sys, "implementation"):
        impl: version_info = sys.implementation.version
        version: str = f"{impl.major}.{impl.minor}.{impl.micro}"
        kind = impl.releaselevel
        if kind != "final":
            version += kind[0] + str(impl.serial)
        return sys.implementation.name, version
    return "", "0.0.0"


def _get_debug_info() -> _Environment:
    """Get debug/environment information.

    Returns:
        Environment information.
    """
    py_name, py_version = _interpreter_name_version()
    environ[f"{METADATA.name_upper}_DEBUG"] = "1"
    variables: list[str] = [
        "PYTHONPATH",
        *[var for var in environ if var.startswith(METADATA.name_upper)],
    ]
    return _Environment(
        interpreter_name=py_name,
        interpreter_version=py_version,
        interpreter_path=sys.executable,
        platform=platform.platform(),
        variables=[_Variable(var, val) for var in variables if (val := getenv(var))],
        packages=_get_installed_packages(),
    )


def _get_installed_packages() -> list[_Package]:
    """Get all installed packages in current environment"""
    packages: list[_Package] = []
    for dist in distributions():
        packages.append(_get_package_info(dist.metadata["Name"]))
    return packages


def _print_debug_info(no_color: bool = False) -> None:
    """Print debug/environment information with minimal clean formatting."""
    info: _Environment = _get_debug_info()
    sections: list[tuple[str, list[tuple[str, str]]]] = [
        (
            "SYSTEM",
            [
                ("Platform", info.platform),
                ("Python", f"{info.interpreter_name} {info.interpreter_version}"),
                ("Location", info.interpreter_path),
            ],
        ),
        ("ENVIRONMENT", [(var.name, var.value) for var in info.variables]),
        ("PACKAGES", [(pkg.name, f"v{pkg.version}") for pkg in info.packages]),
    ]
    console = Console(highlight=not no_color, markup=True, force_terminal=not no_color)

    for i, (section_name, items) in enumerate(sections):
        if items:
            console.print(f"{section_name}", style="bold red")
            for key, value in items:
                console.print(key, style="bold blue", end=": ")
                console.print(value, style="bold green")
            if i != len(sections) - 1:
                console.print()


if __name__ == "__main__":
    _print_debug_info()
