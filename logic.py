"""
Hash computation, row building, and comparison helpers.

This module implements the core hashing and comparison logic used by a CLI or
higher-level orchestration layer. It depends on:

- ``util``: shared utilities for path handling, algorithm validation, and row
  construction.
- ``custom_io`` (imported as ``io``): filesystem iteration helpers and error
  emission utilities.

The main responsibilities are:
- Compute a file's hash using a selected algorithm and chunked reads.
- Build a list of hash result rows for executable files.
- Build a mapping of known hashes (or other text content) from ``.txt`` files.
- Compare computed hashes to a known set and annotate rows with a status field.

Status values produced by :func:`checkHashes`:
- ``MATCH``: The filename exists in *knownHashes* and the hash matches.
- ``MISMATCH``: The filename exists in *knownHashes* but the hash differs.
- ``UNKNOWN``: The filename does not exist in *knownHashes*.
"""
from typing import List, Dict

import util
import custom_io as io

def computeFileHash(path: util.Path, algorithm: str, chunkSize: int=1024*1024) -> str:
    """
    Compute a file hash for *path* using *algorithm*.

    The file is read in chunks to avoid loading the entire file into memory.

    :param path: File path to hash.
    :type path: util.Path
    :param algorithm: Hash algorithm name (e.g., ``sha256``, ``sha512``).
    :type algorithm: str
    :param chunkSize: Number of bytes to read per iteration.
    :type chunkSize: int
    :returns: Hex digest string for the file.
    :rtype: str
    :raises ValueError: If the hash algorithm is not supported.
    :raises OSError: If the file cannot be opened or read.
    """
    hasher = util.getHasher(algorithm)
    with path.open("rb") as file:
        while True:
            chunk = file.read(chunkSize)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def buildFileHashRows(root: util.Path, *, recursive: bool, algorithm: str, absolutePaths: bool) -> List[Dict[str, str]]:
    """
    Build hash result rows for ``.exe`` files under *root*.

    This function iterates over executable files, hashes each file, and returns
    a list of row dictionaries suitable for CSV/JSON serialization.

    Row keys are created via :func:`util.makeResultRow`.

    :param root: Root directory to search for ``.exe`` files.
    :type root: util.Path
    :param recursive: If ``True``, include subdirectories.
    :type recursive: bool
    :param algorithm: Hash algorithm name (e.g., ``sha256``).
    :type algorithm: str
    :param absolutePaths: If ``True``, store absolute file paths in rows.
    :type absolutePaths: bool
    :returns: List of hash result rows.
    :rtype: list[dict[str, str]]
    """
    rows = list()
    for path in sorted(io.iterateExeFiles(root, recursive)):
        if not path.is_file():
            continue
        pathString = util.filePathForOutput(path, root, absolutePaths)
        try:
            hashValue = computeFileHash(path, algorithm)
            stats = path.stat()
            row = util.makeResultRow(hashValue,
                                     algorithm=algorithm,
                                     size=stats.st_size,
                                     epochTime=int(stats.st_mtime),
                                     filePath=pathString)
            rows.append(row)
        except Exception as error:
            io.emitError(f"Error hashing '{pathString}': {error}")
    return rows

def buildHashRows(root:util.Path, *, recursive: bool, absolutePaths: bool) -> Dict[str, str]:
    """
    Build a mapping from text file base names to file contents.

    This function iterates over ``.txt`` files under *root* and reads each file
    as UTF-8. The returned dictionary maps the file path with the final
    extension removed to the full text content.

    This assumes each text file contains reference hash data keyed by its filename.

    :param root: Root directory to search for ``.txt`` files.
    :type root: util.Path
    :param recursive: If ``True``, include subdirectories.
    :type recursive: bool
    :param absolutePaths: If ``True``, use absolute paths as keys.
    :type absolutePaths: bool
    :returns: Mapping from path-without-extension to file content.
    :rtype: dict[str, str]
    """
    rows = dict()
    for path in sorted(io.iterateTextFiles(root, recursive)):
        if not path.is_file():
            continue
        pathString = util.filePathForOutput(path, root, absolutePaths)
        try:
            with path.open("r", encoding="utf-8") as file:
                content = file.read()
            rows[pathString.rsplit(".", 1)[0]] = content
        except Exception as error:
            io.emitError(f"Error reading '{pathString}': {error}")
    return rows

def checkHashes(rows:List[Dict[str, str]], knownHashes: Dict[str, str]) -> None:
    """
    Annotate computed hash rows by comparing them to known hashes.

    This function modifies *rows* in-place by adding a ``status`` field to each
    row. The comparison key is the ``filename`` field in each row (as produced
    by :func:`util.makeResultRow`), which is expected to match keys in
    *knownHashes*.

    Status values:
    - ``MATCH``: Filename exists in *knownHashes* and hashes match.
    - ``MISMATCH``: Filename exists in *knownHashes* and hashes differ.
    - ``UNKNOWN``: Filename is not present in *knownHashes*.

    :param rows: List of computed hash rows to annotate.
    :type rows: list[dict[str, str]]
    :param knownHashes: Mapping of filenames to expected hash values.
    :type knownHashes: dict[str, str]
    :returns: ``None``
    :rtype: None
    """
    for row in rows:
        filename = row["filename"]
        fileHash = row["hash"]
        if filename in knownHashes:
            if knownHashes[filename] == fileHash:
                row["status"] = "MATCH"
            else:
                row["status"] = "MISMATCH"
        else:
            row["status"] = "UNKNOWN"