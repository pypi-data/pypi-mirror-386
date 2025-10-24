#!/usr/bin/env python3
"""
repo-dump.py

Create a Markdown dump of the repository.
Supports two modes:
  1. Full dump: Includes all files except those excluded by .dumpignore and --exclude
  2. Partial dump: Includes only files listed in an input file,
     minus any --exclude patterns

Usage:
  python repo-dump.py full [--exclude PATTERN ...]
  python repo-dump.py partial files-to-dump.txt [--exclude PATTERN ...]

Output:
  repo-dump.md in the current directory

Notes:
- Each section in the Markdown file contains the relative path as a heading and
  the file contents as a code block.
- Binary files are skipped.
- .dumpignore is used for exclusions in full mode (supports basic patterns).
- --exclude patterns are always applied (in addition to .dumpignore in full mode).
"""

import fnmatch
import os
import sys
from pathlib import Path

DUMPIGNORE = ".dumpignore"
OUTPUT_MD = "repo-dump.md"


# Helper: Read .dumpignore patterns
def read_dumpignore():
    patterns = []
    if os.path.exists(DUMPIGNORE):
        with open(DUMPIGNORE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    return patterns


def is_ignored(path, patterns):
    for pat in patterns:
        if fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(os.path.basename(path), pat):
            return True
        # Directory pattern
        if pat.endswith("/") and path.startswith(pat):
            return True
    return False


def is_binary(file_path):
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            if b"\0" in chunk:
                return True
    except Exception:
        return True
    return False


def gather_files_full(patterns):
    files = []
    for root, dirs, filenames in os.walk("."):
        # Skip hidden dirs except .
        dirs[:] = [d for d in dirs if not d.startswith(".") or d == "."]
        for filename in filenames:
            rel_path = os.path.relpath(os.path.join(root, filename), ".")
            if rel_path == OUTPUT_MD or rel_path == DUMPIGNORE:
                continue
            if is_ignored(rel_path, patterns):
                continue
            files.append(rel_path)
    return sorted(files)


def gather_files_partial(list_file):
    files = []
    with open(list_file) as f:
        for line in f:
            rel_path = line.strip()
            if rel_path and os.path.isfile(rel_path):
                files.append(rel_path)
    return files


def write_markdown(files):
    with open(OUTPUT_MD, "w", encoding="utf-8") as out:
        for rel_path in files:
            if is_binary(rel_path):
                print(f"[SKIP] Binary file: {rel_path}")
                continue
            try:
                with open(rel_path, encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                print(f"[SKIP] Could not read {rel_path}: {e}")
                continue
            out.write(f"## {rel_path}\n\n")
            out.write(f"```{Path(rel_path).suffix[1:] if Path(rel_path).suffix else ''}\n")
            out.write(content)
            if not content.endswith("\n"):
                out.write("\n")
            out.write("```\n\n")
    print(f"Markdown dump created: {OUTPUT_MD}")


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description="Markdown repo dump tool with exclude support.")
    parser.add_argument("mode", choices=["full", "partial"], help="Dump mode: full or partial")
    parser.add_argument("filelist", nargs="?", help="File list for partial mode")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Glob pattern to exclude (can be repeated)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.mode == "full":
        patterns = read_dumpignore() + args.exclude
        files = gather_files_full(patterns)
    else:
        if not args.filelist or not os.path.isfile(args.filelist):
            print("Error: Please provide a valid file list for partial mode.")
            sys.exit(1)
        files = gather_files_partial(args.filelist)
        # Exclude patterns
        if args.exclude:
            files = [f for f in files if not is_ignored(f, args.exclude)]
    write_markdown(files)


if __name__ == "__main__":
    main()
