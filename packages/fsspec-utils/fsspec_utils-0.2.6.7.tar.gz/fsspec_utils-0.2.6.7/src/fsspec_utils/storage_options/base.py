from typing import Any

import msgspec
import yaml
from fsspec import AbstractFileSystem
from fsspec import filesystem as fsspec_filesystem


class BaseStorageOptions(msgspec.Struct):
    """Base class for filesystem storage configuration options.

    Provides common functionality for all storage option classes including:
    - YAML serialization/deserialization
    - Dictionary conversion
    - Filesystem instance creation
    - Configuration updates

    Attributes:
        protocol (str): Storage protocol identifier (e.g., "s3", "gs", "file")

    Example:
        >>> # Create and save options
        >>> options = BaseStorageOptions(protocol="s3")
        >>> options.to_yaml("config.yml")
        >>>
        >>> # Load from YAML
        >>> loaded = BaseStorageOptions.from_yaml("config.yml")
        >>> print(loaded.protocol)
        's3'
    """

    protocol: str

    def to_dict(self, with_protocol: bool = False) -> dict:
        """Convert storage options to dictionary.

        Args:
            with_protocol: Whether to include protocol in output dictionary

        Returns:
            dict: Dictionary of storage options with non-None values

        Example:
            >>> options = BaseStorageOptions(protocol="s3")
            >>> print(options.to_dict())
            {}
            >>> print(options.to_dict(with_protocol=True))
            {'protocol': 's3'}
        """
        data = msgspec.structs.asdict(self)
        result = {}
        for key, value in data.items():
            if value is None:
                continue

            if key == "protocol":
                if with_protocol:
                    result[key] = value
            else:
                result[key] = value
        return result

    @classmethod
    def from_yaml(
        cls, path: str, fs: AbstractFileSystem = None
    ) -> "BaseStorageOptions":
        """Load storage options from YAML file.

        Args:
            path: Path to YAML configuration file
            fs: Filesystem to use for reading file

        Returns:
            BaseStorageOptions: Loaded storage options instance

        Example:
            >>> # Load from local file
            >>> options = BaseStorageOptions.from_yaml("config.yml")
            >>> print(options.protocol)
            's3'
        """
        if fs is None:
            fs = fsspec_filesystem("file")
        with fs.open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: str, fs: AbstractFileSystem = None) -> None:
        """Save storage options to YAML file.

        Args:
            path: Path where to save configuration
            fs: Filesystem to use for writing

        Example:
            >>> options = BaseStorageOptions(protocol="s3")
            >>> options.to_yaml("config.yml")
        """
        if fs is None:
            fs = fsspec_filesystem("file")
        data = self.to_dict()
        with fs.open(path, "w") as f:
            yaml.safe_dump(data, f)

    def to_filesystem(self) -> AbstractFileSystem:
        """Create fsspec filesystem instance from options.

        Returns:
            AbstractFileSystem: Configured filesystem instance

        Example:
            >>> options = BaseStorageOptions(protocol="file")
            >>> fs = options.to_filesystem()
            >>> files = fs.ls("/path/to/data")
        """
        return fsspec_filesystem(**self.to_dict(with_protocol=True))

    def update(self, **kwargs: Any) -> "BaseStorageOptions":
        """Update storage options with new values.

        Args:
            **kwargs: New option values to set

        Returns:
            BaseStorageOptions: Updated instance

        Example:
            >>> options = BaseStorageOptions(protocol="s3")
            >>> options = options.update(region="us-east-1")
            >>> print(options.region)
            'us-east-1'
        """
        return msgspec.structs.replace(self, **kwargs)
