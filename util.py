"""
Path and hashing utility helpers.

This module contains small, reusable helper functions used by the hashing
workflow, including path normalization/formatting, hash algorithm validation,
and construction of result rows for downstream output (CSV/JSON).

Notes
-----
- Path normalization relies on :meth:`pathlib.Path.expanduser` and
  :meth:`pathlib.Path.resolve`. Behavior may differ slightly across operating
  systems and Python versions when resolving symlinks or non-existent paths.
- Hash algorithm availability depends on the Python build and underlying
  OpenSSL configuration.
"""
import hashlib
from pathlib import Path
from typing import Dict

def safeRelativePath(path: Path, root: Path) -> str:
    """
    Return *path* relative to *root* when possible.

    If *path* is not located under *root*, this function returns the string form
    of *path* unchanged.

    :param path: Path to convert to a relative path.
    :type path: pathlib.Path
    :param root: Root directory used as the base for relative paths.
    :type root: pathlib.Path
    :returns: Relative path string when possible; otherwise the original path
        string.
    :rtype: str
    """
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)

def normalizeRoot(directory: str) -> Path:
    """
    Normalize a directory string into an absolute :class:`~pathlib.Path`.

    This expands a leading ``~`` to the user home directory (when present) and
    resolves the resulting path to an absolute path.

    :param directory: Directory path as provided by the caller.
    :type directory: str
    :returns: Normalized absolute path.
    :rtype: pathlib.Path
    """
    return Path(directory).expanduser().resolve()

def filePathForOutput(path: Path, root: Path, absolutePaths: bool) -> str:
    """
    Format a file path for display or report output.

    If *absolutePaths* is enabled, this returns the absolute string form of
    *path*. Otherwise it returns a path relative to *root* when possible.

    :param path: File path to format.
    :type path: pathlib.Path
    :param root: Root directory used as the base for relative paths.
    :type root: pathlib.Path
    :param absolutePaths: If ``True``, output absolute paths.
    :type absolutePaths: bool
    :returns: A formatted file path string.
    :rtype: str
    """
    if absolutePaths:
        return str(path)
    return safeRelativePath(path, root) 

def getHasher(algorithm: str)-> "hashlib._Hash":
    """
    Create a new hasher instance for *algorithm*.

    This validates that the requested algorithm is supported by the current
    Python/OpenSSL environment.

    :param algorithm: Hash algorithm name (e.g., ``sha256``, ``sha512``).
    :type algorithm: str
    :raises ValueError: If *algorithm* is not supported.
    :returns: A hashlib hasher instance.
    :rtype: hashlib._Hash
    """
    try:
        return hashlib.new(algorithm)
    except ValueError:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

def makeResultRow(hashValue: str, *, algorithm: str, size: int, epochTime: int, filePath: str) -> Dict[str, str]:
    """
    Construct a result row dictionary for reporting.

    The returned mapping is intended to be serialized to CSV/JSON by an output
    layer.

    Row keys:
      - ``hash``: Hex digest of the file content.
      - ``algorithm``: Hash algorithm name.
      - ``size``: File size in bytes (as a string).
      - ``modified_time``: Modification time (epoch seconds as a string).
      - ``file_path``: Display/full file path.
      - ``filename``: File path with the final extension removed.

    :param hashValue: Hex digest string for the file content.
    :type hashValue: str
    :param algorithm: Hash algorithm name (e.g., ``sha256``).
    :type algorithm: str
    :param size: File size in bytes.
    :type size: int
    :param epochTime: File modification time in epoch seconds.
    :type epochTime: int
    :param filePath: File path to store in the row (display or absolute).
    :type filePath: str
    :returns: Result row mapping suitable for CSV/JSON serialization.
    :rtype: dict[str, str]
    """
    return {
        "hash": hashValue,
        "algorithm": algorithm,
        "size": str(size),
        "modified_time": str(epochTime),
        "file_path": filePath,
        "filename": filePath.rsplit(".", 1)[0]
    }