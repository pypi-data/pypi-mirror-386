# File: tests/test_ProjectRoot.py

import pytest
from seSql.dbc.ProjectRoot import ProjectRootFinder

from pathlib import Path
from unittest.mock import patch, Mock


@pytest.fixture
def project_root_finder():
    """Fixture for initializing ProjectRootFinder."""
    return ProjectRootFinder()


def test_default_project_markers(project_root_finder):
    """Test that default project markers are initialized properly."""
    expected_markers = [
        ".git", ".idea", ".vscode",
        "pyproject.toml", "requirements.txt", "setup.py"
    ]
    assert project_root_finder.project_markers == expected_markers


@patch("seSql.dbc.ProjectRoot.Path.cwd")
def test_find_project_root_no_markers(mock_cwd, project_root_finder):
    """Test find_project_root raises RuntimeError if no markers are found."""
    mock_cwd.return_value = Path("/some/path")
    with pytest.raises(RuntimeError):
        project_root_finder.find_project_root()


@patch("seSql.dbc.ProjectRoot.ProjectRootFinder._find_root_directory")
def test_find_project_root_with_relative_path(mock_find_root, project_root_finder):
    """Test find_project_root returns the correct relative path."""
    mock_find_root.return_value = (Path("/some/path"), "Matched criterion")
    relative_path = "subdir/file.txt"
    result = project_root_finder.find_project_root(relative_path=relative_path)
    expected = Path("/some/path/subdir/file.txt")
    assert result == expected


@patch("seSql.dbc.ProjectRoot.ProjectRootFinder._find_root_directory")
def test_find_project_root_warn_missing(mock_find_root, project_root_finder):
    """Test find_project_root issues a warning for a missing file."""
    mock_find_root.return_value = (Path("/some/path"), "Matched criterion")
    relative_path = "missing_file.txt"

    with pytest.warns(UserWarning, match="Path doesn't exist:"):
        project_root_finder.find_project_root(relative_path=relative_path, warn_missing=True)


@patch("seSql.dbc.ProjectRoot.Path.exists", return_value=False)
@patch("seSql.dbc.ProjectRoot.ProjectRootFinder._resolve_start_path")
def test_find_root_directory_no_match(mock_resolve_path, mock_exists, project_root_finder):
    """Test _find_root_directory raises RuntimeError if no root directory is found."""
    mock_resolve_path.return_value = Path("/invalid/path")
    mock_exists.return_value = False

    with pytest.raises(RuntimeError, match="Project root not found."):
        project_root_finder._find_root_directory()


@patch("seSql.dbc.ProjectRoot.ProjectRootFinder._resolve_start_path")
def test_resolve_start_path(mock_resolve_path, project_root_finder):
    """Test _resolve_start_path method."""
    mock_resolve_path.return_value = Path("/resolved/path")
    result = project_root_finder._resolve_start_path("/start/path")
    assert result == Path("/resolved/path")


def test_iterate_parents(project_root_finder):
    """Test _iterate_parents method."""
    start_path = Path("/project/root/subdir")
    result = list(project_root_finder._iterate_parents(start_path))
    expected = [
        Path("/project/root/subdir"),
        Path("/project/root"),
        Path("/project"),
        Path("/")
    ]
    assert result == expected


def test_create_root_criterion_with_callable(project_root_finder):
    """Test _create_root_criterion when provided with a callable."""
    mock_criterion = Mock(return_value=True)
    root_criterion = project_root_finder._create_root_criterion(mock_criterion)

    test_path = Path("/test/path")
    assert root_criterion(test_path) is True
    mock_criterion.assert_called_once_with(test_path)


def test_matches_path_criterion_with_wildcard_match_existing(project_root_finder, tmp_path):
    """Test _matches_path_criterion with a wildcard that matches existing files."""
    (tmp_path / "file1_test.txt").touch()
    (tmp_path / "file2_test.txt").touch()

    result = project_root_finder._matches_path_criterion(tmp_path, "*.txt")
    assert result is True


def test_matches_path_criterion_with_wildcard_no_match(project_root_finder, tmp_path):
    """Test _matches_path_criterion with a wildcard that matches no files."""
    (tmp_path / "file1_test.log").touch()
    result = project_root_finder._matches_path_criterion(tmp_path, "*.txt")
    assert result is False
