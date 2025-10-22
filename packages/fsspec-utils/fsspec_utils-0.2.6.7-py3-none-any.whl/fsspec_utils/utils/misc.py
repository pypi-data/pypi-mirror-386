"""Miscellaneous utility functions for fsspec-utils."""

import importlib
import os
import posixpath
from typing import Any, Callable, Optional, Union

from joblib import Parallel, delayed
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn, track

from fsspec import AbstractFileSystem
from fsspec.implementations.dirfs import DirFileSystem
# from ..utils.logging import get_logger

# logger = get_logger(__name__)


# def run_parallel(
#     func: Callable,
#     *args,
#     n_jobs: int = -1,
#     backend: str = "threading",
#     verbose: bool = True,
#     **kwargs,
# ) -> list[Any]:
#     """Run a function for a list of parameters in parallel.

#     Provides parallel execution with progress tracking and flexible
#     argument handling.

#     Args:
#         func: Function to run in parallel.
#         *args: Positional arguments. Can be single values or iterables.
#         n_jobs: Number of joblib workers. Defaults to -1 (all cores).
#         backend: Joblib backend. Options: 'loky', 'threading',
#                 'multiprocessing', 'sequential'. Defaults to 'threading'.
#         verbose: Show progress bar. Defaults to True.
#         **kwargs: Keyword arguments. Can be single values or iterables.

#     Returns:
#         List of function outputs in the same order as inputs.

#     Raises:
#         ValueError: If no iterable arguments provided or length mismatch.

#     Examples:
#         >>> # Single iterable argument
#         >>> run_parallel(str.upper, ["hello", "world"])
#         ['HELLO', 'WORLD']

#         >>> # Multiple iterables in args and kwargs
#         >>> def add(x, y, offset=0):
#         ...     return x + y + offset
#         >>> run_parallel(add, [1, 2, 3], y=[4, 5, 6], offset=10)
#         [15, 17, 19]

#         >>> # Fixed and iterable arguments
#         >>> run_parallel(pow, [2, 3, 4], exp=2)
#         [4, 9, 16]
#     """
#     parallel_kwargs = {"n_jobs": n_jobs, "backend": backend, "verbose": 0}

#     iterables = []
#     fixed_args = []
#     iterable_kwargs = {}
#     fixed_kwargs = {}

#     first_iterable_len = None

#     # Process positional arguments
#     for arg in args:
#         if isinstance(arg, (list, tuple)) and not isinstance(arg[0], (list, tuple)):
#             iterables.append(arg)
#             if first_iterable_len is None:
#                 first_iterable_len = len(arg)
#             elif len(arg) != first_iterable_len:
#                 raise ValueError(
#                     f"Iterable length mismatch: argument has length {len(arg)}, expected {first_iterable_len}"
#                 )
#         else:
#             fixed_args.append(arg)

#     # Process keyword arguments
#     for key, value in kwargs.items():
#         if isinstance(value, (list, tuple)) and not isinstance(value[0], (list, tuple)):
#             if first_iterable_len is None:
#                 first_iterable_len = len(value)
#             elif len(value) != first_iterable_len:
#                 raise ValueError(
#                     f"Iterable length mismatch: {key} has length {len(value)}, expected {first_iterable_len}"
#                 )
#             iterable_kwargs[key] = value
#         else:
#             fixed_kwargs[key] = value

#     if first_iterable_len is None:
#         raise ValueError("At least one iterable argument is required")

#     # Combine all iterables and create parameter combinations
#     all_iterables = iterables + list(iterable_kwargs.values())
#     param_combinations = list(zip(*all_iterables))

#     # Execute without progress bar
#     if not verbose:
#         return Parallel(**parallel_kwargs)(
#             delayed(func)(
#                 *(list(param_tuple[: len(iterables)]) + fixed_args),
#                 **{
#                     k: v
#                     for k, v in zip(
#                         iterable_kwargs.keys(), param_tuple[len(iterables) :]
#                     )
#                 },
#                 **fixed_kwargs,
#             )
#             for param_tuple in param_combinations
#         )

#     # Execute with progress bar
#     else:
#         results = [None] * len(param_combinations)
#         with Progress(
#             TextColumn("[progress.description]{task.description}"),
#             BarColumn(),
#             "[progress.percentage]{task.percentage:>3.0f}%",
#             TimeElapsedColumn(),
#             transient=True,
#         ) as progress:
#             task = progress.add_task(
#                 "Running in parallel...", total=len(param_combinations)
#             )

#             def wrapper(idx, param_tuple):
#                 res = func(
#                     *(list(param_tuple[: len(iterables)]) + fixed_args),
#                     **{
#                         k: v
#                         for k, v in zip(
#                             iterable_kwargs.keys(), param_tuple[len(iterables) :]
#                         )
#                     },
#                     **fixed_kwargs,
#                 )
#                 progress.update(task, advance=1)
#                 return idx, res

#             for idx, result in Parallel(**parallel_kwargs)(
#                 delayed(wrapper)(i, param_tuple)
#                 for i, param_tuple in enumerate(param_combinations)
#             ):
#                 results[idx] = result
#         return results
if importlib.util.find_spec("joblib"):
    from joblib import Parallel, delayed
    from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn

    def _prepare_parallel_args(
        args: tuple, kwargs: dict
    ) -> tuple[list, list, dict, dict, int]:
        """Prepare and validate arguments for parallel execution.

        Args:
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            tuple: (iterables, fixed_args, iterable_kwargs, fixed_kwargs, first_iterable_len)

        Raises:
            ValueError: If no iterable arguments or length mismatch
        """
        iterables = []
        fixed_args = []
        iterable_kwargs = {}
        fixed_kwargs = {}
        first_iterable_len = None

        # Process positional arguments
        for arg in args:
            if isinstance(arg, (list, tuple)) and not isinstance(arg[0], (list, tuple)):
                iterables.append(arg)
                if first_iterable_len is None:
                    first_iterable_len = len(arg)
                elif len(arg) != first_iterable_len:
                    raise ValueError(
                        f"Iterable length mismatch: argument has length {len(arg)}, expected {first_iterable_len}"
                    )
            else:
                fixed_args.append(arg)

        # Process keyword arguments
        for key, value in kwargs.items():
            if isinstance(value, (list, tuple)) and not isinstance(
                value[0], (list, tuple)
            ):
                if first_iterable_len is None:
                    first_iterable_len = len(value)
                elif len(value) != first_iterable_len:
                    raise ValueError(
                        f"Iterable length mismatch: {key} has length {len(value)}, expected {first_iterable_len}"
                    )
                iterable_kwargs[key] = value
            else:
                fixed_kwargs[key] = value

        if first_iterable_len is None:
            raise ValueError("At least one iterable argument is required")

        return iterables, fixed_args, iterable_kwargs, fixed_kwargs, first_iterable_len

    def _execute_parallel_with_progress(
        func: Callable,
        iterables: list,
        fixed_args: list,
        iterable_kwargs: dict,
        fixed_kwargs: dict,
        param_combinations: list,
        parallel_kwargs: dict,
    ) -> list:
        """Execute parallel tasks with progress tracking.

        Args:
            func: Function to execute
            iterables: List of iterable arguments
            fixed_args: List of fixed arguments
            iterable_kwargs: Dictionary of iterable keyword arguments
            fixed_kwargs: Dictionary of fixed keyword arguments
            param_combinations: List of parameter combinations
            parallel_kwargs: Parallel execution configuration

        Returns:
            list: Results from parallel execution
        """
        results = [None] * len(param_combinations)
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            transient=True,
        ) as progress:
            task = progress.add_task(
                "Running in parallel...", total=len(param_combinations)
            )

            def wrapper(idx, param_tuple):
                res = func(
                    *(list(param_tuple[: len(iterables)]) + fixed_args),
                    **{
                        k: v
                        for k, v in zip(
                            iterable_kwargs.keys(), param_tuple[len(iterables) :]
                        )
                    },
                    **fixed_kwargs,
                )
                progress.update(task, advance=1)
                return idx, res

            for idx, result in Parallel(**parallel_kwargs)(
                delayed(wrapper)(i, param_tuple)
                for i, param_tuple in enumerate(param_combinations)
            ):
                results[idx] = result
        return results

    def _execute_parallel_without_progress(
        func: Callable,
        iterables: list,
        fixed_args: list,
        iterable_kwargs: dict,
        fixed_kwargs: dict,
        param_combinations: list,
        parallel_kwargs: dict,
    ) -> list:
        """Execute parallel tasks without progress tracking.

        Args:
            func: Function to execute
            iterables: List of iterable arguments
            fixed_args: List of fixed arguments
            iterable_kwargs: Dictionary of iterable keyword arguments
            fixed_kwargs: Dictionary of fixed keyword arguments
            param_combinations: List of parameter combinations
            parallel_kwargs: Parallel execution configuration

        Returns:
            list: Results from parallel execution
        """
        return Parallel(**parallel_kwargs)(
            delayed(func)(
                *(list(param_tuple[: len(iterables)]) + fixed_args),
                **{
                    k: v
                    for k, v in zip(
                        iterable_kwargs.keys(), param_tuple[len(iterables) :]
                    )
                },
                **fixed_kwargs,
            )
            for param_tuple in param_combinations
        )

    def run_parallel(
        func: Callable,
        *args,
        n_jobs: int = -1,
        backend: str = "threading",
        verbose: bool = True,
        **kwargs,
    ) -> list[Any]:
        """Runs a function for a list of parameters in parallel.

        Args:
            func (Callable): function to run in parallel
            *args: Positional arguments. Can be single values or iterables
            n_jobs (int, optional): Number of joblib workers. Defaults to -1
            backend (str, optional): joblib backend. Valid options are
                `loky`,`threading`, `mutliprocessing` or `sequential`. Defaults to "threading"
            verbose (bool, optional): Show progress bar. Defaults to True
            **kwargs: Keyword arguments. Can be single values or iterables

        Returns:
            list[any]: Function output

        Examples:
            >>> # Single iterable argument
            >>> run_parallel(func, [1,2,3], fixed_arg=42)

            >>> # Multiple iterables in args and kwargs
            >>> run_parallel(func, [1,2,3], val=[7,8,9], fixed=42)

            >>> # Only kwargs iterables
            >>> run_parallel(func, x=[1,2,3], y=[4,5,6], fixed=42)
        """
        if backend == "threading" and n_jobs == -1:
            n_jobs = min(256, (os.cpu_count() or 1) + 4)

        parallel_kwargs = {"n_jobs": n_jobs, "backend": backend, "verbose": 0}

        # Prepare and validate arguments
        iterables, fixed_args, iterable_kwargs, fixed_kwargs, first_iterable_len = (
            _prepare_parallel_args(args, kwargs)
        )

        # Create parameter combinations
        all_iterables = iterables + list(iterable_kwargs.values())
        param_combinations = list(zip(*all_iterables))

        # Execute with or without progress tracking
        if not verbose:
            return _execute_parallel_without_progress(
                func,
                iterables,
                fixed_args,
                iterable_kwargs,
                fixed_kwargs,
                param_combinations,
                parallel_kwargs,
            )
        else:
            return _execute_parallel_with_progress(
                func,
                iterables,
                fixed_args,
                iterable_kwargs,
                fixed_kwargs,
                param_combinations,
                parallel_kwargs,
            )

else:

    def run_parallel(*args, **kwargs):
        raise ImportError("joblib not installed")


def get_partitions_from_path(
    path: str, partitioning: Union[str, list[str], None] = None
) -> list[tuple]:
    """Extract dataset partitions from a file path.

    Parses file paths to extract partition information based on
    different partitioning schemes.

    Args:
        path: File path potentially containing partition information.
        partitioning: Partitioning scheme:
            - "hive": Hive-style partitioning (key=value)
            - str: Single partition column name
            - list[str]: Multiple partition column names
            - None: Return empty list

    Returns:
        List of tuples containing (column, value) pairs.

    Examples:
        >>> # Hive-style partitioning
        >>> get_partitions_from_path("data/year=2023/month=01/file.parquet", "hive")
        [('year', '2023'), ('month', '01')]

        >>> # Single partition column
        >>> get_partitions_from_path("data/2023/01/file.parquet", "year")
        [('year', '2023')]

        >>> # Multiple partition columns
        >>> get_partitions_from_path("data/2023/01/file.parquet", ["year", "month"])
        [('year', '2023'), ('month', '01')]
    """
    if "." in path:
        path = os.path.dirname(path)

    parts = path.split("/")

    if isinstance(partitioning, str):
        if partitioning == "hive":
            return [tuple(p.split("=")) for p in parts if "=" in p]
        else:
            return [(partitioning, parts[0])]
    elif isinstance(partitioning, list):
        return list(zip(partitioning, parts[-len(partitioning) :]))
    else:
        return []


def path_to_glob(path: str, format: str | None = None) -> str:
    """Convert a path to a glob pattern for file matching.

    Intelligently converts paths to glob patterns that match files of the specified
    format, handling various directory and wildcard patterns.

    Args:
        path: Base path to convert. Can include wildcards (* or **).
            Examples: "data/", "data/*.json", "data/**"
        format: File format to match (without dot). If None, inferred from path.
            Examples: "json", "csv", "parquet"

    Returns:
        str: Glob pattern that matches files of specified format.
            Examples: "data/**/*.json", "data/*.csv"

    Example:
        >>> # Basic directory
        >>> path_to_glob("data", "json")
        'data/**/*.json'
        >>>
        >>> # With wildcards
        >>> path_to_glob("data/**", "csv")
        'data/**/*.csv'
        >>>
        >>> # Format inference
        >>> path_to_glob("data/file.parquet")
        'data/file.parquet'
    """
    path = path.rstrip("/")
    if format is None:
        if ".json" in path:
            format = "json"
        elif ".csv" in path:
            format = "csv"
        elif ".parquet" in path:
            format = "parquet"

    if format in path:
        return path
    else:
        if path.endswith("**"):
            return posixpath.join(path, f"*.{format}")
        elif path.endswith("*"):
            if path.endswith("*/*"):
                return path + f".{format}"
            return posixpath.join(path.rstrip("/*"), f"*.{format}")
        return posixpath.join(path, f"**/*.{format}")


def check_optional_dependency(package_name: str, feature_name: str) -> None:
    """Check if an optional dependency is available.

    Args:
        package_name: Name of the package to check
        feature_name: Name of the feature that requires this package

    Raises:
        ImportError: If the package is not available
    """
    if not importlib.util.find_spec(package_name):
        raise ImportError(
            f"{package_name} is required for {feature_name}. "
            f"Install with: pip install fsspec-utils[full]"
        )


def check_fs_identical(fs1: AbstractFileSystem, fs2: AbstractFileSystem) -> bool:
    """Check if two fsspec filesystems are identical.

    Args:
        fs1: First filesystem (fsspec AbstractFileSystem)
        fs2: Second filesystem (fsspec AbstractFileSystem)

    Returns:
        bool: True if filesystems are identical, False otherwise
    """

    def _get_root_fs(fs: AbstractFileSystem) -> AbstractFileSystem:
        while hasattr(fs, "fs"):
            fs = fs.fs
        return fs

    fs1 = _get_root_fs(fs1)
    fs2 = _get_root_fs(fs2)
    return fs1 == fs2


def sync_files(
    add_files: list[str],
    delete_files: list[str],
    src_fs: AbstractFileSystem,
    dst_fs: AbstractFileSystem,
    src_path: str = "",
    dst_path: str = "",
    server_side: bool = False,
    chunk_size: int = 8 * 1024 * 1024,
    parallel: bool = False,
    n_jobs: int = -1,
    verbose: bool = True,
) -> dict[str, list[str]]:
    """Sync files between two filesystems by copying new files and deleting old ones.

    Args:
        add_files: List of file paths to add (copy from source to destination)
        delete_files: List of file paths to delete from destination
        src_fs: Source filesystem (fsspec AbstractFileSystem)
        dst_fs: Destination filesystem (fsspec AbstractFileSystem)
        src_path: Base path in source filesystem. Default is root ('').
        dst_path: Base path in destination filesystem. Default is root ('').
        server_side: Whether to use server-side copy if supported. Default is False.
        chunk_size: Size of chunks to read/write files (in bytes). Default is 8MB.
        parallel: Whether to perform copy/delete operations in parallel. Default is False.
        n_jobs: Number of parallel jobs if parallel=True. Default is -1 (all cores).
        verbose: Whether to show progress bars. Default is True.

    Returns:
        dict: Summary of added and deleted files
    """
    CHUNK = chunk_size
    RETRIES = 3

    server_side = check_fs_identical(src_fs, dst_fs) and server_side

    src_mapper = src_fs.get_mapper(src_path)
    dst_mapper = dst_fs.get_mapper(dst_path)

    def server_side_copy_file(key, src_mapper, dst_mapper, RETRIES):
        last_exc = None
        for attempt in range(1, RETRIES + 1):
            try:
                dst_mapper[key] = src_mapper[key]
                break
            except Exception as e:
                last_exc = e

    def copy_file(key, src_fs, dst_fs, src_path, dst_path, CHUNK, RETRIES):
        last_exc = None
        for attempt in range(1, RETRIES + 1):
            try:
                with (
                    src_fs.open(posixpath.join(src_path, key), "rb") as r,
                    dst_fs.open(posixpath.join(dst_path, key), "wb") as w,
                ):
                    while True:
                        chunk = r.read(CHUNK)
                        if not chunk:
                            break
                        w.write(chunk)
                break
            except Exception as e:
                last_exc = e

    def delete_file(key, dst_fs, dst_path, RETRIES):
        last_exc = None
        for attempt in range(1, RETRIES + 1):
            try:
                dst_fs.rm(posixpath.join(dst_path, key))
                break
            except Exception as e:
                last_exc = e

    if len(add_files):
        # Copy new files
        if parallel:
            if server_side:
                try:
                    run_parallel(
                        server_side_copy_file,
                        add_files,
                        src_mapper=src_mapper,
                        dst_mapper=dst_mapper,
                        RETRIES=RETRIES,
                        n_jobs=n_jobs,
                        verbose=verbose,
                    )
                except Exception:
                    # Fallback to client-side copy if server-side fails
                    run_parallel(
                        copy_file,
                        add_files,
                        src_fs=src_fs,
                        dst_fs=dst_fs,
                        src_path=src_path,
                        dst_path=dst_path,
                        CHUNK=CHUNK,
                        RETRIES=RETRIES,
                        n_jobs=n_jobs,
                        verbose=verbose,
                    )
            else:
                run_parallel(
                    copy_file,
                    add_files,
                    src_fs=src_fs,
                    dst_fs=dst_fs,
                    src_path=src_path,
                    dst_path=dst_path,
                    CHUNK=CHUNK,
                    RETRIES=RETRIES,
                    n_jobs=n_jobs,
                    verbose=verbose,
                )
        else:
            if verbose:
                for key in track(
                    add_files,
                    description="Copying new files...",
                    total=len(add_files),
                ):
                    if server_side:
                        try:
                            server_side_copy_file(key, src_mapper, dst_mapper, RETRIES)
                        except Exception:
                            copy_file(
                                key, src_fs, dst_fs, src_path, dst_path, CHUNK, RETRIES
                            )
                    else:
                        copy_file(
                            key, src_fs, dst_fs, src_path, dst_path, CHUNK, RETRIES
                        )
            else:
                for key in add_files:
                    if server_side:
                        try:
                            server_side_copy_file(key, src_mapper, dst_mapper, RETRIES)
                        except Exception:
                            copy_file(
                                key, src_fs, dst_fs, src_path, dst_path, CHUNK, RETRIES
                            )
                    else:
                        copy_file(
                            key, src_fs, dst_fs, src_path, dst_path, CHUNK, RETRIES
                        )

    if len(delete_files):
        # Delete old files from destination
        if parallel:
            run_parallel(
                delete_file,
                delete_files,
                dst_fs=dst_fs,
                dst_path=dst_path,
                RETRIES=RETRIES,
                n_jobs=n_jobs,
                verbose=verbose,
            )
        else:
            if verbose:
                for key in track(
                    delete_files,
                    description="Deleting stale files...",
                    total=len(delete_files),
                ):
                    delete_file(key, dst_fs, dst_path, RETRIES)
            else:
                for key in delete_files:
                    delete_file(key, dst_fs, dst_path, RETRIES)

    return {"added_files": add_files, "deleted_files": delete_files}


def sync_dir(
    src_fs: AbstractFileSystem,
    dst_fs: AbstractFileSystem,
    src_path: str = "",
    dst_path: str = "",
    server_side: bool = True,
    chunk_size: int = 8 * 1024 * 1024,
    parallel: bool = False,
    n_jobs: int = -1,
    verbose: bool = True,
) -> dict[str, list[str]]:
    """Sync two directories between different filesystems.

    Compares files in the source and destination directories, copies new or updated files from source to destination,
    and deletes stale files from destination.

    Args:
        src_fs: Source filesystem (fsspec AbstractFileSystem)
        dst_fs: Destination filesystem (fsspec AbstractFileSystem)
        src_path: Path in source filesystem to sync. Default is root ('').
        dst_path: Path in destination filesystem to sync. Default is root ('').
        chunk_size: Size of chunks to read/write files (in bytes). Default is 8MB.
        parallel: Whether to perform copy/delete operations in parallel. Default is False.
        n_jobs: Number of parallel jobs if parallel=True. Default is -1 (all cores).
        verbose: Whether to show progress bars. Default is True.

    Returns:
        dict: Summary of added and deleted files
    """

    src_mapper = src_fs.get_mapper(src_path)
    dst_mapper = dst_fs.get_mapper(dst_path)

    add_files = sorted(src_mapper.keys() - dst_mapper.keys())
    delete_files = sorted(dst_mapper.keys() - src_mapper.keys())

    return sync_files(
        add_files=add_files,
        delete_files=delete_files,
        src_fs=src_fs,
        dst_fs=dst_fs,
        src_path=src_path,
        dst_path=dst_path,
        chunk_size=chunk_size,
        server_side=server_side,
        parallel=parallel,
        n_jobs=n_jobs,
        verbose=verbose,
    )
