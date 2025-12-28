# Sturdy-Barnacle
A small, modular Python toolchain for hashing Windows executables (.exe) in a directory, exporting results to CSV/JSON, and optionally validating hashes against a set of known values loaded from .txt files.

## Features
- Hash all .exe files in a directory (non-recursive by default; enable with --recursive)
- Select hash algorithm (default sha256)
- Output:
  - Console (human-readable)
  - CSV (--csv)
  - JSON (--json)
- Optional compare mode (--compare)
  - Loads known values from .txt files under the same root
  - Annotates each row with MATCH, MISMATCH, or UNKNOWN

## Compare mode expectations
In --compare mode, known values are loaded from .txt files using the “path without extension” as the key. Each computed executable row is compared using the row’s filename field (also derived as “path without final extension”).

The script sets:
- MATCH if expected hash exists and matches
- MISMATCH if expected hash exists but differs
- UNKNOWN if no expected hash exists

## Output Schema
This tool produces output in three places:
1) **CLI output (stdout)** for humans
2) **CLI errors (stderr)** for failures/warnings
3) **Report files** (CSV/JSON) for machine-readable results

### CLI
The CLI prints one “record” per `.exe` file, separated by a line containing `---`.

#### Normal Mode (no `--compare`)
Each record includes:

- `Filepath`: the displayed path (relative to root by default, absolute if `--absolute-paths`)
- `Hash`: the computed hex digest

Format:
```text
Filepath: <file_path>
Hash: <hex_digest>
---
```

#### Compare Mode (`--compare`)
Each record includes:

- `Filepath`: the displayed path (relative to root by default, absolute if `--absolute-paths`)
- `Hash`: the computed hex digest
- `Status`: if the computed hex digest matches a known record

Format:
```
Filepath: <file_path>
Hash: <hex_digest>
Status: <status>
---
```

### CSV (`--csv`)
The CSV file will include a header row. The csv format will be:

| Column          | Type   | Description                                           |
| --------------- | ------ | ----------------------------------------------------- |
| `hash`          | string | Hex digest                                            |
| `algorithm`     | string | Hash algorithm name (e.g., `sha256`)                  |
| `size`          | string | File size in bytes (stored as string)                 |
| `modified_time` | string | File mtime as epoch seconds (stored as string)        |
| `file_path`     | string | Displayed path (relative/absolute depending on flags) |
| `filename`      | string | `file_path` with the final extension removed          |

#### Compare-mode CSV (`--compare`)
Same as above, plus:
| Column   | Type   | Description                      |
| -------- | ------ | -------------------------------- |
| `status` | string | `MATCH` / `MISMATCH` / `UNKNOWN` |


### JSON (`--json`)
The JSON is an array of objects. Each object corresponds to one .exe result row. The JSON format will be:
```
{
  "hash": "string",
  "algorithm": "string",
  "size": "string",
  "modified_time": "string",
  "file_path": "string",
  "filename": "string"
}
```

#### Compare-mode JSON (`--compare`)
Same as above, plus:
```
{
  "status": "MATCH | MISMATCH | UNKNOWN"
}
```

## Notes
- filename is derived as file_path.rsplit(".", 1)[0] (removes only the final extension).
- Compare mode uses row["filename"] as the lookup key into the known-hash mapping.
