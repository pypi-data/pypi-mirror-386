#!/bin/python3
"""
Created on Fri Oct 27 13:36:28 2023
@author: fedenunez and tulp
"""

import argparse
import os
import fnmatch
import pathlib
import sys
import glob

# Optional dependency for proper .gitignore-style matching
try:
    import pathspec  # type: ignore
except ImportError:
    pathspec = None


class IgnoreMatcher:
    """A wrapper for pathspec or fnmatch to check if a path should be ignored."""
    def __init__(self, patterns, use_pathspec=False):
        self.use_pathspec = use_pathspec and pathspec is not None
        if self.use_pathspec:
            self.spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns)
        else:
            self.patterns = patterns

    def match(self, file_path):
        """Check if the given file_path matches any of the ignore patterns."""
        if self.use_pathspec:
            return self.spec.match_file(file_path)
        else:
            # Basic fnmatch logic. fnmatch is not directory-aware like git,
            # so this is a simplification. It checks against the full path and basename.
            for pattern in self.patterns:
                if fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(os.path.basename(file_path), pattern):
                    return True
            return False


def get_fml_spec():
    return """
# Filesystem Markup Language (FML)

The Filesystem Markup Language (FML) is a simple format to represent a file system's structure and content using markup tags.

## Structure Overview

### Tags

- **File Tag:**
  - **Start Tag:** `<|||file_start=${filepath}|||>`
  - **End Tag:** `<|||file_end|||>`
  - **Content:** The file content is placed between the start and end tags.
  - **Rules:**
    - Start and End tags must occupy a full line.
    - The content is placed between the start and end lines.
    - Start and END Tags must start at the beginning of the line with no leading spaces or tabs.

- **Directory Tag:**
  - **Tag:** `<|||dir=${dirpath}|||>`

### Description

- **Files:**
  - Represented by start and end tags indicating their relative path.
  - Content is written between these tags.
  - Only supports UTF8/ASCII text files; binary files are ignored.

- **Directories:**
  - Represented using the directory tag.
  - Useful for specifying empty directories.
  - If a file mentions a directory, it is assumed that the directory already exists.

### Important Notes

- All directories mentioned in a file path will be automatically created.
- All paths are relative to the starting point, which is the folder containing all files with the fewest levels possible.

## Examples

    ```fml
    <|||dir=projects|||>

    <|||file_start=projects/plan.txt|||>
    Project plan details go here.
    <|||file_end|||>`
    ```

This example creates a directory `projects` and a file `plan.txt` within it, containing the specified text.

    ```fml
    <|||file_start=documents/reports/summary.txt|||>
    Summary of the quarterly report.
    <|||file_end|||>
    ```

This example creates a directory `documents` with a subdirectory `reports`, and a file `summary.txt` within `reports`, containing the specified text.
"""


def process_arguments():
    """
    Process command line arguments and return an object with the values
    """
    parser = argparse.ArgumentParser(
        description="fmlpack: Convert a file tree to/from a Filesystem Markup Language (FML) document.",
        add_help=False # We add our own help handling
    )

    # Custom help action
    parser.add_argument(
        '-h', '--help',
        action='help',
        default=argparse.SUPPRESS,
        help='Show this help message and exit'
    )

    # Modes of operation
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-c", "--create", action="store_true", help="Create a new archive")
    group.add_argument("-x", "--extract", action="store_true", help="Extract files from an archive")
    group.add_argument("-t", "--list", action="store_true", help="List the contents of an archive")

    # Options
    parser.add_argument("-f", "--file", metavar="ARCHIVE", help="Use archive file or device ARCHIVE. Use '-' for stdin/stdout.")
    parser.add_argument("--spec-help", action="store_true", help="Print the FML specification and exit.")
    parser.add_argument("-s", "--include-spec", action="store_true", help="Include FML specification (as fmlpack-spec.md) in the created archive")
    parser.add_argument(
        "-C",
        "--directory",
        metavar="DIR",
        help="Change to directory DIR before performing operations (for extraction) or use DIR as base for relative paths (for creation)",
    )

    # Filtering options for creation
    parser.add_argument(
        "--exclude",
        metavar="PATTERN",
        action="append",
        default=[],
        help="Exclude files matching PATTERN",
    )
    parser.add_argument(
        "--gitignore",
        action="store_true",
        help="Use .gitignore rules from the base directory when creating an archive",
    )

    # Positional arguments for input files/folders
    parser.add_argument("input", nargs="*", help="Input files or folders for archive creation")

    return parser.parse_args(), parser


def get_relative_path(base_dir, file_path):
    """Calculate the relative path, ensuring it's in POSIX format."""
    return pathlib.Path(file_path).relative_to(base_dir).as_posix()


def is_binary_file(file_path):
    """
    Heuristically determine if a file is binary.
    Returns True if it contains a null byte or fails UTF-8 decoding.
    """
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            if b'\0' in chunk:
                return True
            chunk.decode('utf-8')
    except UnicodeDecodeError:
        return True
    except Exception: # Fallback for read errors
        return True
    return False


def expand_and_collect_paths(inputs, base_dir):
    """Expand input paths (globs, directories) into a list of absolute paths."""
    collected_paths = set()
    for item in inputs:
        # Handle glob patterns by searching within base_dir
        path_to_glob = os.path.join(base_dir, item)
        found_paths = glob.glob(path_to_glob, recursive=True)

        if not found_paths:
             sys.stderr.write(f"Warning: Input item not found: {item}\n")
             continue

        for path in found_paths:
            abs_path = os.path.abspath(path)
            collected_paths.add(abs_path)
            if os.path.isdir(abs_path):
                for root, dirs, files in os.walk(abs_path, topdown=True):
                    for name in files:
                        collected_paths.add(os.path.join(root, name))
                    for name in dirs:
                        collected_paths.add(os.path.join(root, name))
    return sorted(list(collected_paths))


def get_common_base_dir(paths):
    """Find the common base directory for a list of paths."""
    if not paths:
        return os.getcwd()
    # Use os.path.commonpath, which is robust
    return os.path.commonpath(paths)


def load_ignore_matcher(root_dir, use_gitignore_flag):
    """
    Load ignore patterns from .fmlpackignore and .gitignore files.
    """
    all_patterns = []

    if pathspec is None and use_gitignore_flag:
        sys.stderr.write(
            "Warning: 'pathspec' module not found. .gitignore parsing will be basic. "
            "Install with: pip install pathspec\n"
        )
        for ignore_filename in [".fmlpackignore", ".gitignore"]:
            if not use_gitignore_flag and ignore_filename == ".gitignore":
                continue
            ignore_path = os.path.join(root_dir, ignore_filename)
            if os.path.isfile(ignore_path):
                try:
                    with open(ignore_path, "r", encoding="utf-8") as f:
                        all_patterns.extend(f.read().splitlines())
                except Exception:
                    pass
        if use_gitignore_flag:
            all_patterns.insert(0, ".git/")
        all_patterns = [p.strip() for p in all_patterns if p.strip() and not p.strip().startswith("#")]
        return IgnoreMatcher(all_patterns, use_pathspec=False) if all_patterns else None

    root_path = pathlib.Path(root_dir).resolve()
    ignore_files_to_process = []
    ignore_files_to_process.extend(root_path.rglob(".fmlpackignore"))

    if use_gitignore_flag:
        ignore_files_to_process.extend(root_path.rglob(".gitignore"))
        all_patterns.append('/.git/')

    for ignore_file in sorted(ignore_files_to_process):
        try:
            relative_dir_path = ignore_file.parent.relative_to(root_path)
            with ignore_file.open("r", encoding="utf-8") as f:
                for line in f:
                    pattern = line.strip()
                    if not pattern or pattern.startswith("#"):
                        continue
                    if "/" in pattern:
                        is_negated = pattern.startswith("!")
                        pattern_body = pattern[1:] if is_negated else pattern
                        if str(relative_dir_path) == ".":
                             final_pattern = f"/{pattern_body.lstrip('/')}"
                        else:
                             final_pattern = f"/{relative_dir_path.as_posix()}/{pattern_body.lstrip('/')}"
                        if is_negated:
                            final_pattern = "!" + final_pattern
                        all_patterns.append(final_pattern)
                    else:
                        all_patterns.append(pattern)
        except Exception:
            pass
    return IgnoreMatcher(all_patterns, use_pathspec=True) if all_patterns else None


def generate_fml(output_stream, base_dir, paths, ignore_matcher, include_spec):
    """Generate FML content from a list of paths and write to a stream."""
    processed_dirs = set()

    if include_spec:
        output_stream.write("<|||file_start=fmlpack-spec.md|||>\n")
        output_stream.write(get_fml_spec())
        output_stream.write("\n<|||file_end|||>\n")

    for abs_path in paths:
        rel_path = get_relative_path(base_dir, abs_path)

        if ignore_matcher and ignore_matcher(rel_path):
            sys.stderr.write(f"Excluding: {rel_path}\n")
            continue

        if os.path.isdir(abs_path):
            if not any(os.scandir(abs_path)): # Empty directory
                if rel_path != "." and rel_path not in processed_dirs:
                    output_stream.write(f"<|||dir={rel_path}|||>\n")
                    processed_dirs.add(rel_path)
        elif os.path.isfile(abs_path):
            if is_binary_file(abs_path):
                sys.stderr.write(f"Skipping binary file: {rel_path}\n")
                continue

            # Ensure parent directories are declared
            parent_dir = os.path.dirname(rel_path)
            if parent_dir and parent_dir not in processed_dirs:
                 # Add all parent components
                parts = pathlib.Path(parent_dir).parts
                for i in range(1, len(parts) + 1):
                    sub_dir = pathlib.Path(*parts[:i]).as_posix()
                    if sub_dir not in processed_dirs:
                        output_stream.write(f"<|||dir={sub_dir}|||>\n")
                        processed_dirs.add(sub_dir)

            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                output_stream.write(f"<|||file_start={rel_path}|||>\n")
                output_stream.write(content)
                if not content.endswith('\n'):
                    output_stream.write('\n')
                output_stream.write("<|||file_end|||>\n")
            except Exception as e:
                sys.stderr.write(f"Error reading file {rel_path}: {e}\n")


def extract_fml_archive(input_stream, target_dir):
    """Extract files and directories from an FML stream."""
    in_file_block = False
    current_file_path = None
    current_file_content = []

    os.makedirs(target_dir, exist_ok=True)

    def write_file():
        if current_file_path:
            full_path = os.path.join(target_dir, current_file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            try:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.writelines(current_file_content)
                sys.stdout.write(f"Extracted: {current_file_path}\n")
            except Exception as e:
                sys.stderr.write(f"Error writing file {current_file_path}: {e}\n")

    for line in input_stream:
        stripped_line = line.strip()
        if stripped_line.startswith("<|||file_start=") and stripped_line.endswith("|||>"):
            if in_file_block: # Malformed FML: new file starts before old one ends
                write_file()
            
            path_part = stripped_line[len("<|||file_start="):-len("|||>")]
            current_file_path = path_part
            current_file_content = []
            in_file_block = True
        elif stripped_line == "<|||file_end|||>":
            if in_file_block:
                write_file()
                in_file_block = False
                current_file_path = None
                current_file_content = []
        elif stripped_line.startswith("<|||dir=") and stripped_line.endswith("|||>"):
            path_part = stripped_line[len("<|||dir="):-len("|||>")]
            full_path = os.path.join(target_dir, path_part)
            os.makedirs(full_path, exist_ok=True)
            sys.stdout.write(f"Created directory: {path_part}\n")
        elif in_file_block:
            current_file_content.append(line)

    if in_file_block: # Handle file block not closed at EOF
        sys.stderr.write(f"Warning: FML ended with unclosed file block for '{current_file_path}'. Writing anyway.\n")
        write_file()


def list_fml_archive(input_stream):
    """List the contents of an FML archive."""
    for line in input_stream:
        stripped_line = line.strip()
        if stripped_line.startswith("<|||file_start=") and stripped_line.endswith("|||>"):
            path_part = stripped_line[len("<|||file_start="):-len("|||>")]
            sys.stdout.write(f"{path_part}\n")
        elif stripped_line.startswith("<|||dir=") and stripped_line.endswith("|||>"):
            path_part = stripped_line[len("<|||dir="):-len("|||>")]
            sys.stdout.write(f"{path_part}\n")


def main():
    """Main function to run the fmlpack tool."""
    args, parser = process_arguments()

    if args.spec_help:
        sys.stdout.write(get_fml_spec())
        sys.exit(0)

    # Determine mode of operation
    mode_selected = args.create or args.extract or args.list
    if not mode_selected:
        if args.input:
            args.create = True
        else:
            parser.print_help()
            sys.exit(0)

    # --- CREATE MODE ---
    if args.create:
        if not args.input:
            parser.error("At least one input file or folder is required for --create")
        
        base_dir = os.path.abspath(args.directory) if args.directory else os.getcwd()
        paths_to_process = expand_and_collect_paths(args.input, base_dir)

        if args.directory is None and len(args.input) > 1:
            abs_inputs = [os.path.abspath(os.path.join(base_dir, p)) for p in args.input]
            base_dir = get_common_base_dir(abs_inputs)

        ignore_matcher_manual = IgnoreMatcher(args.exclude) if args.exclude else None
        ignore_matcher_auto = load_ignore_matcher(base_dir, args.gitignore)
        
        # Combine matchers
        def combined_matcher(path):
            if ignore_matcher_manual and ignore_matcher_manual.match(path):
                return True
            if ignore_matcher_auto and ignore_matcher_auto.match(path):
                return True
            return False

        output_file = None
        try:
            if args.file and args.file != '-':
                output_file = open(args.file, "w", encoding="utf-8")
                output_stream = output_file
                sys.stdout.write(f"FML archive created: {args.file}\n")
            else:
                output_stream = sys.stdout

            generate_fml(output_stream, base_dir, paths_to_process, combined_matcher, args.include_spec)
        
        finally:
            if output_file:
                output_file.close()

    # --- EXTRACT or LIST MODE ---
    elif args.extract or args.list:
        input_file = None
        try:
            if args.file and args.file != '-':
                if not os.path.exists(args.file):
                     parser.error(f"Archive file not found: {args.file}")
                input_file = open(args.file, "r", encoding="utf-8")
                input_stream = input_file
            else:
                 if sys.stdin.isatty():
                     parser.error("-f/--file or piped input is required for --extract or --list")
                 input_stream = sys.stdin

            if args.extract:
                target_dir = args.directory or os.getcwd()
                extract_fml_archive(input_stream, target_dir)
            else: # list
                list_fml_archive(input_stream)
        
        finally:
            if input_file:
                input_file.close()

if __name__ == "__main__":
    main()
