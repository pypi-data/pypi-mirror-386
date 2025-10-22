"""Basic tests for fsspec-utils package."""

import posixpath
from pathlib import Path

import pytest

def test_imports():
    """Test that basic imports work."""
    from fsspec_utils import filesystem, DirFileSystem, AbstractFileSystem
    from fsspec_utils.storage_options import AwsStorageOptions, LocalStorageOptions
    from fsspec_utils.utils import setup_logging
    
    assert filesystem is not None
    assert DirFileSystem is not None
    assert AbstractFileSystem is not None
    assert AwsStorageOptions is not None
    assert LocalStorageOptions is not None
    assert setup_logging is not None


def test_local_filesystem():
    """Test local filesystem creation."""
    from fsspec_utils import filesystem
    
    fs = filesystem("file")
    assert fs is not None
    assert hasattr(fs, "ls")
    assert hasattr(fs, "open")


def test_storage_options():
    """Test storage options creation."""
    from fsspec_utils.storage_options import LocalStorageOptions, AwsStorageOptions
    
    # Local options
    local_opts = LocalStorageOptions()
    assert local_opts.protocol == "file"
    
    # AWS options
    aws_opts = AwsStorageOptions(region="us-east-1")
    assert aws_opts.protocol == "s3"
    assert aws_opts.region == "us-east-1"


def test_logging_setup():
    """Test logging setup."""
    from fsspec_utils.utils import setup_logging

    # Should not raise any errors
    setup_logging(level="INFO", disable=False)


def test_filesystem_preserves_directory_without_trailing_slash(tmp_path):
    """Ensure filesystem() keeps the last directory component by default."""
    from fsspec_utils import DirFileSystem, filesystem

    root = tmp_path / "path" / "to" / "root"
    root.mkdir(parents=True)

    fs = filesystem(root.as_posix())

    assert isinstance(fs, DirFileSystem)
    assert Path(fs.path).resolve() == root.resolve()


def test_filesystem_infers_directory_from_file_path(tmp_path):
    """Ensure filesystem() detects file inputs and returns the parent directory."""
    from fsspec_utils import DirFileSystem, filesystem

    root = tmp_path / "data"
    root.mkdir()
    file_path = root / "file.csv"
    file_path.write_text("content", encoding="utf-8")

    fs = filesystem(file_path.as_posix())

    assert isinstance(fs, DirFileSystem)
    assert Path(fs.path).resolve() == root.resolve()


def test_filesystem_directory_with_dotted_parent(tmp_path):
    """Directories with dots in parent names should be preserved."""
    from fsspec_utils import DirFileSystem, filesystem

    root = tmp_path / "dataset.v1" / "partition"
    root.mkdir(parents=True)

    fs = filesystem(root.as_posix())

    assert isinstance(fs, DirFileSystem)
    assert Path(fs.path).resolve() == root.resolve()


def test_filesystem_preserves_trailing_dot_directory(tmp_path):
    """Directories ending with a dot should not be treated as files."""
    from fsspec_utils import DirFileSystem, filesystem

    root = tmp_path / "abc" / "efg."
    root.mkdir(parents=True)

    fs = filesystem(root.as_posix())

    assert isinstance(fs, DirFileSystem)
    assert Path(fs.path).resolve() == root.resolve()


def test_filesystem_dirfs_child_with_trailing_dot(tmp_path):
    """Relative child directories ending with a dot should be resolved safely."""
    from fsspec_utils import DirFileSystem, filesystem

    root = tmp_path / "abc"
    child = root / "efg."
    child.mkdir(parents=True)

    base_fs = filesystem(root.as_posix())
    child_fs = filesystem(child.name, base_fs=base_fs)

    assert isinstance(child_fs, DirFileSystem)
    assert Path(child_fs.path).resolve() == child.resolve()


def test_filesystem_dirfs_with_partial_overlap(tmp_path):
    """Relative child partially overlapping with base should not duplicate segments."""
    from fsspec_utils import DirFileSystem, filesystem

    root = tmp_path / "ewn" / "mms2" / "stage1"
    nested = root / "SC"
    nested.mkdir(parents=True)

    base_fs = filesystem(root.as_posix())

    # Provide only the overlapping tail of the path
    child_fs = filesystem("mms2/stage1/SC", base_fs=base_fs)

    assert isinstance(child_fs, DirFileSystem)
    assert Path(child_fs.path).resolve() == nested.resolve()

    # Provide a shorter overlapping tail
    child_fs2 = filesystem("stage1/SC", base_fs=base_fs)

    assert isinstance(child_fs2, DirFileSystem)
    assert Path(child_fs2.path).resolve() == nested.resolve()

def test_filesystem_dirfs_with_relative_path(tmp_path):
    """Relative paths should be resolved against the base DirFileSystem root."""
    from fsspec_utils import DirFileSystem, filesystem

    root = tmp_path / "root"
    (root / "nested").mkdir(parents=True)

    base_fs = filesystem(root.as_posix())
    child_fs = filesystem("nested", base_fs=base_fs)

    assert isinstance(child_fs, DirFileSystem)
    assert child_fs.fs is base_fs.fs
    expected_path = posixpath.normpath(posixpath.join(base_fs.path, "nested"))
    assert posixpath.normpath(child_fs.path) == expected_path


def test_filesystem_dirfs_with_explicit_same_path(tmp_path):
    """Explicitly targeting the same directory should reuse the base filesystem."""
    from fsspec_utils import filesystem

    root = tmp_path / "root"
    root.mkdir()

    base_fs = filesystem(root.as_posix())
    fs_with_base = filesystem(f"file://{root.as_posix()}", base_fs=base_fs)

    assert fs_with_base is base_fs


def test_filesystem_dirfs_with_explicit_subpath(tmp_path):
    """Explicit child paths should produce a new DirFileSystem anchored within the base."""
    from fsspec_utils import DirFileSystem, filesystem

    root = tmp_path / "root"
    sub = root / "nested"
    sub.mkdir(parents=True)

    base_fs = filesystem(root.as_posix())
    child_fs = filesystem(f"file://{sub.as_posix()}", base_fs=base_fs)

    assert isinstance(child_fs, DirFileSystem)
    assert Path(child_fs.path).resolve() == sub.resolve()


def test_filesystem_dirfs_with_mismatched_path_raises(tmp_path):
    """Paths outside the base DirFileSystem should raise a clear error."""
    from fsspec_utils import filesystem

    root = tmp_path / "root"
    other = tmp_path / "other"
    root.mkdir()
    other.mkdir()

    base_fs = filesystem(root.as_posix())

    with pytest.raises(ValueError):
        filesystem(f"file://{other.as_posix()}", base_fs=base_fs)


def test_filesystem_dirfs_with_protocol_mismatch(tmp_path):
    """Using an incompatible protocol with base_fs should fail fast."""
    from fsspec_utils import filesystem

    root = tmp_path / "root"
    root.mkdir()

    base_fs = filesystem(root.as_posix())

    with pytest.raises(ValueError):
        filesystem("s3://bucket/path", base_fs=base_fs)


def test_filesystem_dirfs_disallows_parent_escape(tmp_path):
    """Relative paths must not escape the base DirFileSystem root."""
    from fsspec_utils import filesystem

    root = tmp_path / "root"
    root.mkdir()

    base_fs = filesystem(root.as_posix())

    with pytest.raises(ValueError):
        filesystem("../escape", base_fs=base_fs)
