from contextlib import suppress
from dataclasses import field
from importlib.metadata import PackageNotFoundError, distribution, version
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator
from pydantic.dataclasses import dataclass

from lazy_bear._internal._version import __commit_id__, __version__, __version_tuple__


@dataclass(slots=True)
class _Package:
    """Dataclass to store package information."""

    name: str
    """Package name."""
    version: str = "0.0.0"
    """Package version."""
    description: str = "No description available."
    """Package description."""

    def __str__(self) -> str:  # pragma: no cover
        """String representation of the package information."""
        return f"{self.name} v{self.version}: {self.description}"


def _get_package_info(dist: str) -> _Package:  # pragma: no cover
    """Get package information for the given distribution.

    Parameters:
        dist: A distribution name.

    Returns:
        Package information with version, name, and description.
    """
    return _Package(name=dist, version=_get_version(dist), description=_get_description(dist))


def _get_version(dist: str = "lazy-bear") -> str:  # pragma: no cover
    """Get version of the given distribution or the current package.

    Parameters:
        dist: A distribution name.

    Returns:
        A version number.
    """
    try:
        return version(dist)
    except PackageNotFoundError:
        return "0.0.0"


def _get_description(dist: str = "lazy-bear") -> str:  # pragma: no cover
    """Get description of the given distribution or the current package.

    Parameters:
        dist: A distribution name.

    Returns:
        A description string.
    """
    try:
        return distribution(dist).metadata.get("summary", "No description available.")
    except PackageNotFoundError:
        return "No description available."


# fmt: off
@dataclass(slots=True, frozen=True)
class _ProjectName:# pragma: no cover
    """A class to represent the project name and its metadata as literals for type safety.

    This is done this way to make it easier to see the values in the IDE and to ensure that the values are consistent throughout the codebase.
    """

    package_distribution: Literal["lazy-bear"] = "lazy-bear"
    project: Literal["lazy_bear"] = "lazy_bear"
    project_upper: Literal["LAZY_BEAR"] = "LAZY_BEAR"
    env_variable: Literal["LAZY_BEAR_ENV"] = ("LAZY_BEAR_ENV")
# fmt: on


class _ProjectVersion(BaseModel):  # pragma: no cover
    """A class to represent the project version."""

    string: str = Field(default=..., description="Project version.")
    ver_tuple: tuple[int, int, int] = Field(default=..., description="Project version as a tuple.")
    commit_id: str = Field(default=__commit_id__, description="Commit ID of the current version.")

    @field_validator("string", mode="before")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate the version string."""
        if not isinstance(v, str) or "0.0.0" in v:
            with suppress(PackageNotFoundError):
                return _get_version("lazy-bear")
            return "0.0.0"
        return v

    @field_validator("ver_tuple", mode="before")
    @classmethod
    def validate_version_tuple(cls, v: Any) -> tuple[int, int, int]:
        """Validate the version tuple."""
        parts = 3
        if not isinstance(v, tuple) or v == (0, 0, 0):
            with suppress(Exception):
                value: str = _get_version("lazy-bear")
                v = tuple(int(x) for x in value.split(".") if x.isdigit())
                if len(v) == parts:
                    return v
            return (0, 0, 0)
        return v


@dataclass(slots=True, frozen=True)
class _ModulePaths:  # pragma: no cover
    """A class to hold the module import paths, mostly for the CLI."""

    _internal: str = "lazy_bear._internal"
    _commands: str = f"{_internal}._cmds"


@dataclass(slots=True)
class _ProjectMetadata:  # pragma: no cover
    """Dataclass to store the current project metadata."""

    _version: _ProjectVersion
    _name: _ProjectName = field(default_factory=_ProjectName)
    _paths: _ModulePaths = field(default_factory=_ModulePaths)

    def __str__(self) -> str:
        """String representation of the project metadata."""
        return f"{self.full_version}: {self.description}"

    @property
    def cmds(self) -> str:
        """Get the commands module path."""
        return self._paths._commands

    @property
    def version(self) -> str:
        """Get the project version as a string."""
        return self._version.string

    @property
    def version_tuple(self) -> tuple[int, int, int]:
        """Get the project version as a tuple."""
        return self._version.ver_tuple

    @property
    def commit_id(self) -> str:
        """Get the Git commit ID of the current version."""
        return self._version.commit_id

    @property
    def full_version(self) -> str:
        """Get the full version string."""
        return f"{self.name} v{self._version.string}"

    @property
    def description(self) -> str:
        """Get the project description from the distribution metadata."""
        return _get_description(self.name)

    @property
    def name(self) -> Literal["lazy-bear"]:
        """Get the package distribution name."""
        return self._name.package_distribution

    @property
    def name_upper(self) -> Literal["LAZY_BEAR"]:
        """Get the project name in uppercase with underscores."""
        return self._name.project_upper

    @property
    def project_name(self) -> Literal["lazy_bear"]:
        """Get the project name."""
        return self._name.project

    @property
    def env_variable(self) -> Literal["LAZY_BEAR_ENV"]:
        """Get the environment variable name for the project.

        Used to check if the project is running in a specific environment.
        """
        return self._name.env_variable


_version = _ProjectVersion(
    string=__version__ if __version__ != "0.0.0" else _get_version("lazy-bear"),
    commit_id=__commit_id__,
    ver_tuple=__version_tuple__,
)

METADATA = _ProjectMetadata(_version=_version)


__all__ = ["METADATA"]
