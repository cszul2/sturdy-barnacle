"""
File hashing and report output utilities.

This module provides helper functions for discovering files by extension
(``.exe`` and ``.txt``), emitting results to the console, and writing results
to CSV or JSON for later analysis.

Output schema
-------------
Rows written by :func:`writeCSV` and :func:`writeJSON` are expected to be a list
of dictionaries with the following keys:

Required keys:
- ``hash``: Hex digest of the file content.
- ``algorithm``: Hash algorithm name (e.g., ``sha256``).
- ``size``: File size in bytes.
- ``modified_time``: Last modification timestamp (epoch seconds).
- ``file_path``: Display or full file path.
- ``filename``: Base filename (optionally without extension).

Optional keys:
- ``status``: Present when producing comparison output between has values (e.g., unchanged/changed).

Notes
-----
- File discovery uses :class:`pathlib.Path` globbing. Pattern matching and case
  sensitivity depend on the host OS/filesystem.
- Console output is intended for human-readable logs; CSV/JSON are intended for
  downstream tooling.
"""

import csv
import sys
import json
from typing import Iterable, Dict, List

from util import Path

def iterateExeFiles(root: Path, recursive: bool) -> Iterable[Path]:
    """
    Return an iterable of ``.exe`` paths under *root*.

    The returned iterable is produced by :meth:`pathlib.Path.glob` or
    :meth:`pathlib.Path.rglob`, and is evaluated lazily as it is consumed.

    :param root: Root directory to search.
    :type root: pathlib.Path
    :param recursive: If ``True``, include subdirectories; otherwise only scan
        the top-level of *root*.
    :type recursive: bool
    :returns: Iterable of paths matching ``*.exe`` under *root*.
    :rtype: typing.Iterable[pathlib.Path]
    """
    pattern = "*.exe"
    if recursive:
        return root.rglob(pattern)
    return root.glob(pattern)

def iterateTextFiles(root: Path, recursive: bool) -> Iterable[Path]:
    """
    Return an iterable of ``.txt`` paths under *root*.

    The returned iterable is produced by :meth:`pathlib.Path.glob` or
    :meth:`pathlib.Path.rglob`, and is evaluated lazily as it is consumed.

    :param root: Root directory to search.
    :type root: pathlib.Path
    :param recursive: If ``True``, include subdirectories; otherwise only scan
        the top-level of *root*.
    :type recursive: bool
    :returns: Iterable of paths matching ``*.txt`` under *root*.
    :rtype: typing.Iterable[pathlib.Path]
    """
    pattern = "*.txt"
    if recursive:
        return root.rglob(pattern)
    return root.glob(pattern)

def emitConsoleLine(row: Dict[str, str], compare: bool=False) -> None:
    """
    Print a formatted hash result row to standard output.

    When *compare* is enabled and the row includes a ``status`` field, the
    status is printed as well.

    Expected keys in *row*:
      - ``file_path``: The file path displayed to the user.
      - ``hash``: The computed hash value.
      - ``status``: Optional; comparison status (e.g., unchanged/changed).

    :param row: Result row containing file metadata and hash information.
    :type row: dict[str, str]
    :param compare: If ``True``, print a comparison status when available.
    :type compare: bool
    :returns: ``None``
    :rtype: None
    """
    if compare and "status" in row:
        print(f"Filepath: {row['file_path']}")
        print(f"Hash: {row['hash']}")
        print(f"Status: {row['status']}")
        print("---")
    else:
        print(f"Filepath: {row['file_path']}")
        print(f"Hash: {row['hash']}")
        print("---")

def emitError(message: str) -> None:
    """
    Print an error message to standard error.

    :param message: Error message to emit.
    :type message: str
    :returns: ``None``
    :rtype: None
    """
    print(message, file=sys.stderr)

def writeCSV(rows: List[Dict[str, str]], out_path: Path, compare: bool) -> None:
    """
    Write hash result rows to a CSV file.

    When *compare* is enabled, this function includes an additional ``status``
    column.

    Expected keys in each row:
      - ``hash``, ``algorithm``, ``size``, ``modified_time``, ``file_path``,
        ``filename``
      - ``status`` (only when *compare* is ``True``)

    :param rows: List of result rows to write.
    :type rows: list[dict[str, str]]
    :param out_path: Output CSV file path.
    :type out_path: pathlib.Path
    :param compare: If ``True``, include the ``status`` column.
    :type compare: bool
    :returns: ``None``
    :rtype: None
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if compare:
        fieldnames = [
                      "hash",
                      "algorithm",
                      "size",
                      "modified_time",
                      "file_path",
                      "filename",
                      "status"]
        
    else:
        fieldnames = [
                      "hash",
                      "algorithm",
                      "size",
                      "modified_time",
                      "file_path",
                      "filename"]
        
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

def writeJSON(rows: List[Dict[str, str]], out_path: Path) -> None:
    """
    Write hash result rows to a JSON file.

    The output is a JSON array of objects, one per row, indented for readability.

    :param rows: List of result rows to write.
    :type rows: list[dict[str, str]]
    :param out_path: Output JSON file path.
    :type out_path: pathlib.Path
    :returns: ``None``
    :rtype: None
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)