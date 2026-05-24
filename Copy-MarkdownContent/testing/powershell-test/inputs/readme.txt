README - Test Fixtures
======================

This directory contains sample files used by Copy-MarkdownContent tests.

Files included:
- small.md: Minimal markdown for quick tests
- large.txt: Large text content for performance testing
- code.py: Python source code to test code file handling
- readme.txt: This file - a simple text document

Usage:
These files are copied into test case directories during test setup.
The script processes them and outputs formatted markdown to clipboard.

Expected behavior:
- Script should read all files successfully
- Output should contain markdown headers with filenames
- File contents should be preserved in output
- Clipboard should contain properly formatted markdown

Testing notes:
- Files are intentionally diverse (markdown, text, code)
- Sizes range from small (quick tests) to large (performance tests)
- All files use different encodings/formats to catch edge cases
