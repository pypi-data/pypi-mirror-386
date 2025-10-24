"""A dataclass to hold file metadata information."""

from __future__ import annotations

from enum import Enum
from functools import cached_property
import hashlib
from pathlib import Path
import sys
from typing import TYPE_CHECKING

from .export.icons import IconManager

if TYPE_CHECKING:
    from os import stat_result

    from .constants import MetaDataChoice

KILOBYTES = 1024
MEGABYTES = KILOBYTES * 1024
IS_BINARY = -1


class OS(Enum):
    """Enum for operating system platforms."""

    WINDOWS = "windows"
    LINUX = "linux"
    DARWIN = "darwin"
    UNKNOWN = "unknown"


def get_file_hash(path: Path) -> str:
    """Get a simple SHA256 hash of a file - fast and good enough for change detection.

    Args:
        path: Path to the file to hash

    Returns:
        str: Hex digest of the file contents, or empty string if file doesn't exist
    """
    try:
        return hashlib.sha256(path.read_bytes(), usedforsecurity=False).hexdigest()
    except Exception:
        return ""  # File read error, treat as "no file"


def get_platform() -> OS:
    """Get the current operating system platform."""
    platform_str: str = sys.platform.lower()
    if platform_str.startswith("win"):
        return OS.WINDOWS
    if platform_str.startswith("linux"):
        return OS.LINUX
    if platform_str.startswith("darwin"):
        return OS.DARWIN
    return OS.UNKNOWN


class FileInfo(Path):
    """Dataclass to hold file metadata information."""

    def __init__(self, path: Path) -> None:
        """Initialize FileInfo with a Path object."""
        self.path: Path = path

    @property
    def _raw_paths(self) -> tuple[str, ...]:
        """Get the raw paths from the underlying Path object."""
        return self.path._raw_paths  # type: ignore[attr-defined]

    @property
    def _str(self) -> str:
        """Get the string representation of the underlying Path object."""
        return str(self.path)

    @_str.setter
    def _str(self, value: str) -> None:
        """Set the string representation of the underlying Path object."""
        self.path = Path(value)

    @property
    def name(self) -> str:
        """Get the file name."""
        return self.path.name

    @property
    def ext(self) -> str:
        """Get the file extension."""
        return self.path.suffix.lstrip(".")

    @cached_property
    def does_exist(self) -> bool:
        """Check if the file exists."""
        return self.exists()

    def exists(self, *, follow_symlinks: bool = False) -> bool:
        """Check if the file exists."""
        return self.path.exists(follow_symlinks=follow_symlinks)

    def is_file(self, *, follow_symlinks: bool = True) -> bool:
        """Check if the path is a file."""
        return self.path.is_file(follow_symlinks=follow_symlinks) if self.does_exist else False

    def is_dir(self, *, follow_symlinks: bool = True) -> bool:
        """Check if the path is a directory."""
        return self.path.is_dir(follow_symlinks=follow_symlinks) if self.does_exist else False

    def resolve(self, strict: bool = False) -> Path:
        """Resolve the path to its absolute form."""
        return self.path.resolve(strict=strict)

    @cached_property
    def file_hash(self) -> str:
        """Get the SHA256 hash of the file."""
        if not self.does_exist or not self.is_file():
            return ""
        return get_file_hash(self.path)

    @cached_property
    def is_binary(self) -> bool:
        """Check if the file is binary by attempting to read it as text."""
        if not self.is_file():
            return False
        try:
            self.path.read_text(encoding="utf-8")
            return False
        except UnicodeDecodeError:
            return True

    def is_symlink(self) -> bool:
        """Check if the path is a symbolic link."""
        return self.path.is_symlink() if self.does_exist else False

    @cached_property
    def get_stat(self) -> stat_result | None:  # type: ignore[override]
        """Get the file's stat result."""
        if not self.does_exist:
            return None
        return self.path.stat()

    @cached_property
    def size(self) -> int:
        """Get the file size in bytes."""
        return self.get_stat.st_size if self.get_stat is not None else 0

    @cached_property
    def length(self) -> int:
        """Get the number of lines in the file."""
        if not self.does_exist or not self.is_file():
            return 0
        if self.is_binary:
            return IS_BINARY
        return len(self.path.read_text(encoding="utf-8").splitlines())

    @cached_property
    def length_str(self) -> str:
        """Get a human-readable string for the number of lines in the file."""
        if self.length == IS_BINARY:
            return "binary"
        return f"{self.length} lines"

    @cached_property
    def size_kb(self) -> float:
        """Get the file size in kilobytes."""
        return (self.size / KILOBYTES) if self.get_stat is not None else 0.0

    @cached_property
    def size_mb(self) -> float:
        """Get the file size in megabytes."""
        return (self.size / MEGABYTES) if self.get_stat is not None else 0.0

    @cached_property
    def size_str(self) -> str:
        """Get a human-readable file size string."""
        if self.size >= MEGABYTES:
            return f"{self.size_mb:.2f} MB"
        if self.size >= KILOBYTES:
            return f"{self.size_kb:.2f} KB"
        return f"{self.size} bytes"

    @cached_property
    def created(self) -> float | None:
        """Get the file creation time as a timestamp."""
        platform: OS = get_platform()

        if platform is OS.DARWIN and hasattr(self.get_stat, "st_birthtime"):
            return getattr(self.get_stat, "st_birthtime", None)
        if platform is OS.WINDOWS and self.get_stat is not None:
            return self.get_stat.st_ctime
        return self.get_stat.st_mtime if self.get_stat is not None else None

    @cached_property
    def modified(self) -> float | None:
        """Get the file modification time as a timestamp."""
        return self.get_stat.st_mtime if self.get_stat is not None else None

    def to_string(self, icon: IconManager, metadata: MetaDataChoice) -> str:
        """Generate a string representation of the file with its metadata.

        Args:
            icon: IconManager to get the file icon
            metadata: Metadata choice to include in the string

        Returns:
            str: String representation of the file
        """
        icon_str: str = icon.get(self.path, is_symlink=self.is_symlink(), is_dir=self.is_dir())
        file_string: str = f"{icon_str} {self.name}"
        if self.is_dir():
            return file_string
        if self.is_symlink():
            target: Path = self.path.resolve()
            file_string += f" -> {target.relative_to(self.path.parent)}"
        if self.is_binary:
            file_string += " (binary)"
            return file_string
        if metadata == "none" or self.is_symlink():
            return file_string
        if metadata in ("size", "all"):
            file_string += f" ({self.size_str})"
        if metadata in ("lines", "all"):
            file_string += f" ({self.length_str})"
        return file_string

    def __bool__(self) -> bool:
        """Boolean representation of FileInfo based on path existence."""
        return self.does_exist


def to_fileinfo_list(paths: list[Path]) -> list[FileInfo]:
    """Convert a list of Path objects to a list of FileInfo objects.

    Args:
        paths: List of Path objects

    Returns:
        list[FileInfo]: List of FileInfo objects
    """
    return [FileInfo(path=p) for p in paths]
