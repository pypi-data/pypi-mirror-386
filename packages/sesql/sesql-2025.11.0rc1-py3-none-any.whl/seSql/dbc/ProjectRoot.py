import warnings
from pathlib import Path
from typing import Tuple, Callable, Iterable, Union, Optional
from os import PathLike

# Type aliases for improved clarity
PathType = Union[PathLike, str]
CriterionType = Union[
    Callable[[Path], bool],
    PathType,
    Iterable[PathType],
]
RootSearchResult = Tuple[Path, str]


class ProjectRootFinder:
    """Class responsible for finding the project root directory based on markers."""

    # Class-level constants
    DEFAULT_PROJECT_MARKERS = [
        # Common configuration suffixes or directories
        ".git", ".idea", ".vscode",
        # Python project configuration and metadata files
        "pyproject.toml", "requirements.txt", "setup.py",
    ]

    def __init__(self, project_markers: Optional[list[str]] = None):
        """Initialize with custom project markers or use defaults."""
        self.project_markers = project_markers or self.DEFAULT_PROJECT_MARKERS

    def find_project_root(self, relative_path: PathType = "",
                          warn_missing: bool = False) -> Path:
        """Returns the project root or resolves a path relative to it."""
        root, _ = self._find_root_directory()
        result_path = root / relative_path

        if warn_missing and not result_path.exists():
            warnings.warn(f"Path doesn't exist: {result_path}")
        return result_path

    def _find_root_directory(self, start: Optional[PathType] = None) -> RootSearchResult:
        """Find the project root directory based on markers."""
        criterion_func = self._create_root_criterion(self.project_markers)
        start_path = self._resolve_start_path(start)

        for directory in self._iterate_parents(start_path):
            if directory.is_dir() and criterion_func(directory):
                return directory, "Matched criterion"   # pragma: no cover

        raise RuntimeError("Project root not found.")

    @staticmethod
    def _resolve_start_path(start: Optional[PathType]) -> Path:
        """Convert the start parameter to a Path object."""
        return Path(start).resolve() if start else Path.cwd()

    @staticmethod
    def _iterate_parents(start_path: Path) -> Iterable[Path]:
        """Generate a sequence of path and its parent directories."""
        return [start_path, *start_path.parents]

    def _create_root_criterion(self, criterion: CriterionType) -> Callable[[Path], bool]:
        """Create a callable criterion for root directory checking."""
        if callable(criterion):
            return criterion
        if isinstance(criterion, (PathLike, str)):
            return lambda path: self._matches_path_criterion(path, criterion)
        return lambda path: any(self._create_root_criterion(c)(path) for c in criterion)

    @staticmethod
    def _matches_path_criterion(path: Path, criterion: PathType) -> bool:
        """Check if a path matches a given criterion."""
        target = path / criterion
        if isinstance(criterion, str) and "*" in criterion:
            return any(target.parent.glob(criterion))
        return target.exists()


# Create a global instance for backward compatibility
_finder = ProjectRootFinder()
project_root = _finder.find_project_root
