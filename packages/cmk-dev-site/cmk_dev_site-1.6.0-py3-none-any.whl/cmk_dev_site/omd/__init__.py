import difflib
import functools
import subprocess
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Any, Literal
from typing_extensions import override


class Edition(StrEnum):
    """Represents the Checkmk editions."""

    RAW = "cre"
    ENTERPRISE = "cee"
    MANAGED = "cme"
    CLOUD = "cce"
    SAAS = "cse"


@functools.total_ordering
class BaseVersion:
    def __init__(self, major: int, minor: int, patch: int = 0):
        self.major = major
        self.minor = minor
        self.patch = patch

    @classmethod
    def from_str(cls, version_str: str) -> "BaseVersion":
        """Create a Version object from a string.
        This method expects the version string to be in the format 'd.d[.d]'.
        """
        match version_str.split("."):
            case (major_str, minor_str):
                return cls(major=int(major_str), minor=int(minor_str))
            case (major_str, minor_str, patch_str):
                return cls(major=int(major_str), minor=int(minor_str), patch=int(patch_str))
            case _:
                raise ValueError("Version must be in 'd.d[.d]' format")

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __eq__(self, other: Any):
        if isinstance(other, BaseVersion):
            return (self.major, self.minor, self.patch) == (
                other.major,
                other.minor,
                other.patch,
            )
        return NotImplemented

    def __lt__(self, other: Any):
        if isinstance(other, BaseVersion):
            return (self.major, self.minor, self.patch) < (
                other.major,
                other.minor,
                other.patch,
            )

    def iso_format(self) -> str:
        """Return the version in ISO format."""
        return self.__str__()

    @property
    def download_folder_name(self) -> str:
        """Get the download folder name for this version."""
        return self.__str__()


class VersionWithPatch(BaseVersion):
    def __init__(self, base_version: BaseVersion, patch_type: Literal["p", "b"], patch: int):
        self.base_version = base_version
        self.patch_type = patch_type
        self.patch = patch

    def __str__(self) -> str:
        return f"{self.base_version}{self.patch_type}{self.patch}"

    def iso_format(self) -> str:
        return self.__str__()


class VersionWithReleaseCandidate(BaseVersion):
    def __init__(
        self, base_version: BaseVersion, patch_type: Literal["p", "b"], patch: int, rc: int
    ):
        self.base_version = base_version
        self.patch_type = patch_type
        self.patch = patch
        self.rc = rc

    def __str__(self) -> str:
        return f"{self.base_version}{self.patch_type}{self.patch}"

    def iso_format(self) -> str:
        return self.__str__()

    @property
    @override
    def download_folder_name(self) -> str:
        return f"{self.base_version}{self.patch_type}{self.patch}-rc{self.rc}"


class VersionWithReleaseDate(BaseVersion):
    def __init__(self, base_version: BaseVersion, release_date: date):
        self.base_version = base_version
        self.release_date = release_date

    def __str__(self) -> str:
        return f"{self.base_version}-{self.release_date.strftime('%Y.%m.%d')}"

    def __repr__(self) -> str:
        return self.__str__()

    def iso_format(self) -> str:
        return f"{self.base_version}-{self.release_date.isoformat()}"


class PartialVersion(BaseVersion):
    """Represents a version that release date is not known."""

    pass


class GitVersion:
    def __init__(self, branch: str, commit_hash: str):
        self.branch = branch
        self.commit_hash = commit_hash

    def __str__(self) -> str:
        return f"git:{self.branch}:{self.commit_hash}"


Version = (
    BaseVersion
    | VersionWithPatch
    | VersionWithReleaseDate
    | PartialVersion
    | GitVersion
    | VersionWithReleaseCandidate
)


class CMKPackage:
    """Represents a Checkmk package."""

    def __init__(
        self,
        version: VersionWithPatch
        | VersionWithReleaseDate
        | BaseVersion
        | VersionWithReleaseCandidate,
        edition: Edition,
        distro_codename: str = "noble",
        arch: str = "amd64",
    ):
        self.version = version
        self.edition = edition
        self.distro_codename = distro_codename
        self.arch = arch

    @property
    def omd_version(self) -> str:
        """Get the OMD version string."""
        return f"{self.version}.{self.edition.value}"

    @property
    def package_raw_name(self) -> str:
        """Get the package name."""
        base = f"check-mk-{self.edition.name.lower()}-"
        if isinstance(self.version, VersionWithReleaseCandidate):
            return f"{base}{self.version.base_version}{self.version.patch_type}{self.version.patch}"
        else:
            return f"{base}{self.version}"

    @property
    def package_name(self) -> str:
        """Get the package name."""
        return f"{self.package_raw_name}_0.{self.distro_codename}_{self.arch}.deb"

    @property
    def base_version(self) -> BaseVersion:
        """Get the base version."""
        match self.version:
            case VersionWithPatch(base_version=base_version, patch_type=_, patch=_):
                return base_version
            case VersionWithReleaseDate(base_version=base_version, release_date=_):
                return base_version
            case VersionWithReleaseCandidate(
                base_version=base_version, patch_type=_, patch=_, rc=_
            ):
                return base_version
            case BaseVersion():
                return self.version

    def __str__(self) -> str:
        return f"{self.version}.{self.edition.value}"

    def __repr__(self) -> str:
        return self.__str__()


@dataclass
class PartialCMKPackage:
    version: str

    def similarity(self, other: str) -> float:
        return difflib.SequenceMatcher(None, self.version, other).ratio()


def omd_config_set(site_name: str, config_key: str, config_value: str) -> None:
    try:
        result = subprocess.run(
            [
                "sudo",
                "omd",
                "config",
                site_name,
                "set",
                config_key,
                config_value,
            ],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Could not set configuration {config_key} to {config_value} "
            f"for site {site_name}\n{e.stderr}"
        ) from e

    if result.stderr:
        raise RuntimeError(result.stderr.decode("utf-8").strip())


def omd_config_get(site_name: str, param: str) -> str | None:
    try:
        return subprocess.run(
            [
                "sudo",
                "su",
                site_name,
                "-c",
                f"omd config show {param}",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.split("\n")[0]

    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Could not get configuration {param} for site {site_name}\n{e.stderr}"
        ) from e
