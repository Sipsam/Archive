"""Validate source and documentation encoding and reject common mojibake."""

from __future__ import annotations

import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INCLUDED_SUFFIXES = {".py", ".md"}
EXCLUDED_DIRECTORIES = {
    ".git",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "venv",
}

# These patterns cover replacement characters, C1 control characters, common
# UTF-8-as-Latin-1 fragments, and Latin-1 characters produced when Korean
# CP949 bytes are decoded with the wrong codec.  Multiplication signs and
# middle dots are intentionally not included because the project uses them.
SUSPICIOUS_PATTERNS = (
    ("Unicode replacement character", re.compile("\ufffd")),
    ("C1 control character", re.compile("[\u0080-\u009f]")),
    ("UTF-8 mojibake marker", re.compile("[\u00c0-\u00d6\u00d8-\u00f6\u00f8-\u00ff]")),
    (
        "damaged Korean marker",
        re.compile("\\?(?:쒕|곗|꾩|먮|섎|덈|댁|좏|몃|ㅼ)"),
    ),
)


def source_files(root: Path):
    """Yield project source/doc files included in the encoding check."""
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in INCLUDED_SUFFIXES:
            continue
        if any(part in EXCLUDED_DIRECTORIES for part in path.relative_to(root).parts):
            continue
        yield path


def check_file(path: Path) -> list[tuple[int, str]]:
    """Return suspicious encoding findings for one UTF-8 text file."""
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        line_number = raw[: error.start].count(b"\n") + 1
        return [(line_number, f"UTF-8 decode error at byte {error.start}")]

    findings: list[tuple[int, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for label, pattern in SUSPICIOUS_PATTERNS:
            if pattern.search(line):
                findings.append((line_number, label))
    return findings


def main() -> int:
    """Run the encoding check and return a process exit code."""
    findings: list[tuple[Path, int, str]] = []
    checked = 0
    for path in source_files(PROJECT_ROOT):
        checked += 1
        findings.extend((path, line, message) for line, message in check_file(path))

    if findings:
        for path, line, message in findings:
            relative = path.relative_to(PROJECT_ROOT)
            print(f"{relative}:{line}: {message}")
        print(f"Encoding check failed: {len(findings)} issue(s) in {checked} file(s).")
        return 1

    print(f"Encoding check passed: {checked} UTF-8 .py/.md file(s), no mojibake found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
