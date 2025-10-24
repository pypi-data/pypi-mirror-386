import pytest
import os
import sys
import subprocess
import pathlib

# --- Test Setup ---

# This points to the fmlpack script that will be tested.
_project_root_dir = pathlib.Path(__file__).resolve().parent.parent
_fmlpack_script_location = _project_root_dir / "src" / "fmlpack.py"
FMLPACK_CMD = [sys.executable, str(_fmlpack_script_location)]

def run_fmlpack(args, cwd, std_input=None):
    """Helper function to run the fmlpack script and capture its output."""
    if not _fmlpack_script_location.exists():
        pytest.skip(f"fmlpack.py not found at: {_fmlpack_script_location}")
    
    result = subprocess.run(
        FMLPACK_CMD + args,
        input=std_input,
        capture_output=True,
        text=True,
        check=False,
        cwd=str(cwd)
    )
    return result

@pytest.fixture
def test_fs(tmp_path: pathlib.Path):
    """Fixture to create a standard file system structure for testing all features."""
    (tmp_path / "src").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "empty_dir").mkdir()

    (tmp_path / "src" / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (tmp_path / "src" / "utils.py").write_text("def helper():\n    pass\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Project Info", encoding="utf-8")
    (tmp_path / "docs" / "guide.md").write_text("## Usage Guide", encoding="utf-8")
    (tmp_path / "data.bin").write_bytes(b"\x01\x02\x00\x03") # Binary file to be ignored
    (tmp_path / "no_newline.txt").write_text("line without newline", encoding="utf-8")

    # For .gitignore tests
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("[core]", encoding="utf-8")
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "output.o").touch()
    (tmp_path / "src" / "main.pyc").touch()
    (tmp_path / ".gitignore").write_text("*.pyc\nbuild/\n.git\n", encoding="utf-8")
    
    return tmp_path


# --- Comprehensive Test Suite ---

def test_cli_help_and_info_commands(test_fs):
    """Tests basic informational commands like --help and --spec-help."""
    # Test --help
    result = run_fmlpack(["--help"], cwd=test_fs)
    assert result.returncode == 0
    assert "usage: fmlpack" in result.stdout
    assert "--create" in result.stdout and "--extract" in result.stdout

    # Test --spec-help
    result = run_fmlpack(["--spec-help"], cwd=test_fs)
    assert result.returncode == 0
    assert "# Filesystem Markup Language (FML)" in result.stdout
    assert "<|||file_start=${filepath}|||>" in result.stdout

    # Test no arguments shows help
    result = run_fmlpack([], cwd=test_fs)
    assert result.returncode == 0
    assert "usage: fmlpack" in result.stdout

def test_create_archive_functionality(test_fs):
    """Tests the core archive creation (-c) functionality."""
    # Test creating from a single file to stdout
    result = run_fmlpack(["-c", "README.md"], cwd=test_fs)
    assert result.returncode == 0
    assert result.stderr == ""
    assert "<|||file_start=README.md|||>\n# Project Info\n<|||file_end|||>\n" in result.stdout

    # Test creating from a directory to stdout
    result = run_fmlpack(["-c", "src"], cwd=test_fs)
    assert result.returncode == 0
    assert "<|||dir=src|||>" in result.stdout
    assert "<|||file_start=src/main.py|||>" in result.stdout
    assert "<|||file_start=src/utils.py|||>" in result.stdout

    # Test creating from '.' and check special file handling
    result = run_fmlpack(["-c", "."], cwd=test_fs)
    assert result.returncode == 0
    assert "<|||file_start=README.md|||>" in result.stdout
    assert "<|||file_start=src/main.py|||>" in result.stdout
    assert "<|||dir=empty_dir|||>" in result.stdout
    assert "data.bin" not in result.stdout  # Binary files should be skipped
    assert "Skipping binary file: data.bin" in result.stderr
    # Check that file without trailing newline gets one
    assert "<|||file_start=no_newline.txt|||>\nline without newline\n<|||file_end|||>\n" in result.stdout

    # Test creating to a file with -f
    archive_path = test_fs / "archive.fml"
    result = run_fmlpack(["-c", "src", "README.md", "-f", str(archive_path)], cwd=test_fs)
    assert result.returncode == 0
    assert f"FML archive created: {archive_path}" in result.stdout
    content = archive_path.read_text()
    assert "<|||file_start=src/main.py|||>" in content
    assert "<|||file_start=README.md|||>" in content

    # Test creating with a different base directory (-C)
    result = run_fmlpack(["-c", "main.py", "-C", "src"], cwd=test_fs)
    assert result.returncode == 0
    assert "<|||file_start=main.py|||>" in result.stdout
    assert "src/main.py" not in result.stdout

def test_filtering_and_ignore_functionality(test_fs):
    """Tests --exclude and --gitignore filtering."""
    # Test --exclude with a pattern
    result = run_fmlpack(["-c", ".", "--exclude", "*.md"], cwd=test_fs)
    assert result.returncode == 0
    assert "README.md" not in result.stdout
    assert "docs/guide.md" not in result.stdout
    assert "main.py" in result.stdout  # Other files should be present
    assert "Excluding: README.md" in result.stderr

    # Test --exclude with a directory
    result = run_fmlpack(["-c", ".", "--exclude", "src*"], cwd=test_fs)
    assert result.returncode == 0
    assert "src/main.py" not in result.stdout
    assert "README.md" in result.stdout

    # Test --gitignore functionality
    result = run_fmlpack(["-c", ".", "--gitignore"], cwd=test_fs)
    assert result.returncode == 0
    assert ".git/config" not in result.stdout
    assert "build/output.o" not in result.stdout
    assert "src/main.pyc" not in result.stdout
    assert "main.py" in result.stdout  # Non-ignored files should be present
    assert "Excluding: .git/config" in result.stderr
    assert "Excluding: build/output.o" in result.stderr
    assert "Excluding: src/main.pyc" in result.stderr

def test_list_and_extract_functionality(test_fs):
    """Tests archive listing (-t) and extraction (-x) from file and stdin."""
    fml_content = (
        "<|||dir=project|||>\n"
        "<|||file_start=project/app.py|||>\n# Main app\n<|||file_end|||>\n"
        "<|||dir=project/data|||>\n"
        "<|||dir=empty|||>\n"
    )
    archive_file = test_fs / "test.fml"
    archive_file.write_text(fml_content)
    
    # Test listing (-t) from file
    result_list_file = run_fmlpack(["-t", "-f", str(archive_file)], cwd=test_fs)
    assert result_list_file.returncode == 0
    expected_list = sorted(['project', 'project/app.py', 'project/data', 'empty'])
    assert sorted(result_list_file.stdout.strip().split('\n')) == expected_list

    # Test listing (-t) from stdin
    result_list_stdin = run_fmlpack(["-t"], cwd=test_fs, std_input=fml_content)
    assert result_list_stdin.returncode == 0
    assert sorted(result_list_stdin.stdout.strip().split('\n')) == expected_list

    # Test extraction (-x) from file into a target directory (-C)
    extract_dir = test_fs / "output"
    result_extract = run_fmlpack(["-x", "-f", str(archive_file), "-C", str(extract_dir)], cwd=test_fs)
    assert result_extract.returncode == 0
    assert "Extracted: project/app.py" in result_extract.stdout
    assert (extract_dir / "project" / "app.py").is_file()
    assert (extract_dir / "project" / "app.py").read_text() == "# Main app\n"
    assert (extract_dir / "project" / "data").is_dir()
    assert (extract_dir / "empty").is_dir()
    
    # Test extraction (-x) from stdin
    result_extract_stdin = run_fmlpack(["-x"], cwd=test_fs, std_input=fml_content)
    assert result_extract_stdin.returncode == 0
    assert (test_fs / "project" / "app.py").is_file()

def test_special_features(test_fs):
    """Tests special features like --include-spec."""
    result = run_fmlpack(["-c", "README.md", "-s"], cwd=test_fs)
    assert result.returncode == 0
    assert "<|||file_start=fmlpack-spec.md|||>" in result.stdout
    assert "# Filesystem Markup Language (FML)" in result.stdout
    assert "<|||file_start=README.md|||>" in result.stdout

def test_error_handling(test_fs):
    """Tests expected failure modes and error reporting."""
    # Error on mutually exclusive modes
    result = run_fmlpack(["-c", "-x", "input"], cwd=test_fs)
    assert result.returncode != 0
    assert "not allowed with" in result.stderr

    # Error on create with no input files
    result = run_fmlpack(["-c"], cwd=test_fs)
    assert result.returncode != 0
    assert "required for --create" in result.stderr

    # Error on extract with a non-existent archive file
    result = run_fmlpack(["-x", "-f", "nonexistent.fml"], cwd=test_fs)
    assert result.returncode != 0
    assert "Archive file not found" in result.stderr

    # Warning on create with a non-existent input path
    result = run_fmlpack(["-c", "nonexistent.txt"], cwd=test_fs)
    assert result.returncode == 0
    assert result.stdout == ""
    assert "Warning: Input item not found: nonexistent.txt" in result.stderr
