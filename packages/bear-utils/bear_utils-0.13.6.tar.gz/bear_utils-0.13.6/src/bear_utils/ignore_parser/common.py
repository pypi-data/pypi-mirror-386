"""Schemas for file operations."""

from __future__ import annotations

from bisect import insort
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Self

from pathspec import PathSpec
from pydantic import BaseModel, Field, field_validator

from bear_dereth.files.file_info import FileInfo

if TYPE_CHECKING:
    from pathspec import PathSpec

IGNORE_PATTERNS: list[str] = [
    "**/__pycache__",
    ".git",
    "**/.venv",
    ".env",
    ".vscode",
    ".idea",
    "*.DS_Store*",
    "__pypackages__",
    ".pytest_cache",
    ".coverage",
    ".*.swp",
    ".*.swo",
    "*.lock",
    "dist/",
    "**/.nox",
    "**/.pytest_cache",
    "**/.ruff_cache",
]


class IgnoreConfig(BaseModel):
    """Configuration for the IgnoreHandler."""

    # model_config = {"extra": "ignore"}

    directory: Path = Path().cwd()
    verbose: bool = False
    ignore_count: int = 100
    ignore_files: list[Path] = Field(default_factory=list)
    patterns: list[str] = Field(default_factory=list)
    output_as_absolute: bool = False

    def model_post_init(self, context: dict) -> None:
        """Post-initialization to set default patterns if none are provided."""
        self.patterns = [*IGNORE_PATTERNS, *self.patterns]
        if self.ignore_files is None:
            self.ignore_files = [self.directory / ".gitignore"]
        super().model_post_init(context)

    @field_validator("directory", mode="before")
    @classmethod
    def force_path(cls, v: Path | str) -> Path:
        """Ensure the directory is a Path object."""
        return Path(v).expanduser().resolve()

    def update(self, **kwargs) -> Self:
        """Update the configuration with new values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self


@dataclass(slots=True)
class PathObject:
    """Container for a path, a string representation, and an ignore status."""

    info: FileInfo
    str_path: str = field(init=False)
    created: int = 0
    modified: int = 0
    ignored: bool = False

    @property
    def path(self) -> Path:
        """Get the Path object."""
        return self.info.path

    def __post_init__(self) -> None:
        self.str_path = str(self.path)
        self.created = int(self.info.created) if self.info.created else 0
        self.modified = int(self.info.modified) if self.info.modified else 0


def key_by(x: PathObject, key: str = "modified") -> int:
    """Key function to sort PathObjects by modified time.

    Args:
        x: The PathObject to extract the key from
        key: The attribute name to use as the key (default is "modified")
    """
    return getattr(x, key)


@dataclass
class PathsContainer:
    """Container for multiple PathContainer objects."""

    root: Path = Path(".")
    ignored: list[PathObject] = field(default_factory=list)
    non_ignored: list[PathObject] = field(default_factory=list)
    output_as_absolute: bool = False

    @property
    def count(self) -> int:
        """Number of files that were processed."""
        return len(self.ignored) + len(self.non_ignored)

    @property
    def ignored_count(self) -> int:
        """Number of ignored files."""
        return len(self.ignored)

    @property
    def non_ignored_count(self) -> int:
        """Number of non-ignored files."""
        return len(self.non_ignored)

    @property
    def ignored_paths(self) -> list[Path]:
        """List of ignored file paths."""
        if self.output_as_absolute:
            return [self.root / obj.path for obj in self.ignored]
        return [obj.path for obj in self.ignored]

    @property
    def non_ignored_paths(self) -> list[Path]:
        """List of non-ignored file paths."""
        if self.output_as_absolute:
            return [self.root / obj.path for obj in self.non_ignored]
        return [obj.path for obj in self.non_ignored]

    @property
    def first_created(self) -> FileInfo | None:
        """Get the first created PathObject, or None if there are no files."""
        if not self.non_ignored:
            return None
        return min(self.non_ignored, key=lambda obj: obj.created).info

    @classmethod
    def create(cls, directory: Path | str, spec: PathSpec, absolute: bool, sort_by: str = "modified") -> PathsContainer:
        """Create a PathsContainer from a directory and a PathSpec."""
        new: Self = cls(output_as_absolute=absolute)
        new.root = Path(directory).expanduser().resolve()
        for path in new.root.rglob("*"):
            rel_path: Path = path.relative_to(new.root)
            obj = PathObject(FileInfo(rel_path))
            if path.is_file():
                obj.ignored = spec.match_file(obj.str_path)
            elif path.is_dir():
                obj.ignored = (
                    spec.match_file(obj.str_path + "/")
                    if not obj.str_path.endswith("/")
                    else spec.match_file(obj.str_path)
                )
            key: partial[int] = partial(key_by, key=sort_by)
            insort(new.ignored, obj, key=key) if obj.ignored else insort(new.non_ignored, obj, key=key)
        return new
