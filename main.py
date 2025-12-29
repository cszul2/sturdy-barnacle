"""
Command-line interface for hashing executable files.

This script scans a directory for ``.exe`` files, computes a cryptographic hash
for each file, and emits results to standard output. Results can also be
written to CSV and/or JSON for later analysis.

Optionally, the script can compare computed hashes against a set of known
values. Known values are loaded from ``.txt`` files under the same root
directory (using :func:`logic.buildHashRows`). When comparison is enabled, each
result row is annotated with a ``status`` field.

Defaults
--------
- Algorithm: ``sha256``
- Recursive scan: disabled (top-level only)
- Compare mode: disabled
- Output: prints to console; optionally writes CSV or JSON

Comparison behavior
-------------------
When ``--compare`` is provided, the script compares each computed hash row
against the known hash mapping and sets ``status`` to one of:

- ``MATCH``: expected hash exists and matches
- ``MISMATCH``: expected hash exists but differs
- ``UNKNOWN``: no expected hash exists for that filename key

Exit codes
----------
- ``0``: Success
- ``2``: Invalid input or argument error (e.g., root not a directory or
  unsupported hash algorithm)

Usage examples
--------------
- ``python hash_exes.py <path-to-dir>``
- ``python hash_exes.py <path-to-dir> --algo sha512 --recursive --compare``
- ``python hash_exes.py . --csv hashes.csv``
- ``python hash_exes.py . --json hashes.json``
"""
import argparse
from typing import List, Optional

import util
import logic
import custom_io as io

def parseArguments(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments for the CLI.

    :param argv: Optional argument list (defaults to ``sys.argv`` when omitted).
    :type argv: list[str] | None
    :returns: Parsed arguments namespace.
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(description="Hash all .exe files in a directory.")
    parser.add_argument("directory", help="Root directory to scan")
    parser.add_argument("--algo", default="sha256", help="Hash algorithm (default: sha256)")
    parser.add_argument("--recursive", action="store_true", 
                        help="Scan the subdirectories (default: top-level only)")
    parser.add_argument("--csv", help="Write results to CSV file path")
    parser.add_argument("--json", help="Write results to JSON file path")
    parser.add_argument("--absolute-paths", action="store_true",
                        help="Print/write absolute file paths (default: relative to root when possible)")
    parser.add_argument("--compare", action="store_true", 
                        help="Check hash against a provided file of known hash")
    return parser.parse_args(argv)

def main(argv: Optional[List[str]] = None) -> int:
    """
    Run the CLI hashing workflow.

    This function validates inputs, builds hash rows for executables, optionally
    loads known hash values and compares them, prints results, and writes CSV or
    JSON outputs when requested.

    :param argv: Optional argument list (defaults to ``sys.argv`` when omitted).
    :type argv: list[str] | None
    :returns: Process exit code (``0`` success, non-zero error).
    :rtype: int
    """
    arguments = parseArguments(argv)
    root = util.normalizeRoot(arguments.directory)
    if not root.exists() or not root.is_dir():
        io.emitError(f"Error: '{root}' is not a directory.")
        return 2
    try:
        util.getHasher(arguments.algo)
    except ValueError as error:
        io.emitError(str(error))
        return 2
    fileHashRows = logic.buildFileHashRows(root, recursive=arguments.recursive, algorithm=arguments.algo,
                                   absolutePaths=arguments.absolute_paths)
    hashRows = logic.buildHashRows(root, recursive=arguments.recursive,
                                   absolutePaths=arguments.absolute_paths)
    if arguments.compare:
        logic.checkHashes(fileHashRows,hashRows)

    for row in fileHashRows:
        io.emitConsoleLine(row, arguments.compare)

    if not fileHashRows:
        print("No .exe files found.")
        return 0

    if arguments.csv:
        io.writeCSV(fileHashRows, util.Path(arguments.csv).expanduser().resolve(), arguments.compare)

    if arguments.json:
        io.writeJSON(fileHashRows, util.Path(arguments.json).expanduser().resolve())
    return 0

if __name__ == "__main__":
    raise SystemExit(main())