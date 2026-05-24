# Copy-MarkdownContent Test Commands

Quick reference for managing and validating test cases.

## New: Run Cases with Fixtures (Agent-Ready)

These commands enable automated testing loops with fixture files and clipboard output capture.

### Quick Start: Create & Run Test with Fixtures

No JSON needed - just use comma-separated fixture names or preset names:

```powershell
# 1. Create test case with preset
python test.py generate-case -n "my-test" -d "Test description" -f "quick"

# 2. Or with multiple individual fixtures
python test.py generate-case -n "my-test" -d "Test description" -f "small,code"

# 3. Run the test (guides manual trigger)
python test.py run-case -n "my-test"

# 4. Validate results
python test.py validate-case -n "my-test"

# 5. Run all cases in a loop (agent-friendly)
python test.py loop-cases -j
```

### Available Fixtures & Presets

**Presets** (easiest):
- `quick` - Just small.md (fastest for initial testing)
- `multi-format` - small.md, code.py, readme.txt
- `all` - All fixtures (small, large, code, readme)
- `performance` - Just large.txt (for stress testing)

**Individual fixtures:**
- `small` - Simple markdown (259 bytes)
- `large` - Large text content (1.8 KB)
- `code` - Python source code (44 lines)
- `readme` - Plain text document (25 lines)

Fixtures are automatically copied to `testing/{case}/inputs/` when you create a case with `-f` flag.

## Run Test Case (Agent-Friendly)

Orchestrates a complete test: checks fixture files, guides script trigger, captures output, validates.

```powershell
python test.py run-case -n "my-test"
```

**With scenarios:**
```powershell
python test.py run-case -n "my-test" -s single,multi,large
```

**What it does:**
1. Verifies fixture files exist
2. Displays file selection instructions
3. Waits for manual script trigger (Ctrl+Shift+Alt+C)
4. Reads execution logs
5. Validates captured clipboard outputs

## Loop All Cases (For Agents)

Run all test cases in sequence, output structured results for agent parsing.

```powershell
python test.py loop-cases
```

**With JSON output (machine-friendly):**
```powershell
python test.py loop-cases -j
```

**JSON output includes:**
- Case names and descriptions
- Fixture file counts
- Execution status from logs
- Count of captured clipboard outputs
- Summary statistics (success/partial/failed/no_files)

**Example output:**
```json
{
  "timestamp": "2026-05-23T21:38:27",
  "total_cases": 2,
  "cases": [...],
  "summary": {
    "success_count": 1,
    "partial_count": 0,
    "failed_count": 0,
    "no_files_count": 1
  }
}
```

## Generate a New Test Case

Create a new test case with optional file inputs and fixtures to track.

```powershell
python test.py generate-case -n "case_name" -d "Case description"
```

**With fixtures (copies sample files):**

```powershell
python test.py generate-case -n "case_name" -d "Case description" -f "small,large,code"
```

**With preset names (no quotes needed):**

```powershell
python test.py generate-case -n "case_name" -d "Case description" -f "quick"
python test.py generate-case -n "case_name" -d "Case description" -f "multi-format"
python test.py generate-case -n "case_name" -d "Case description" -f "all"
```

**With external test input files:**

```powershell
python test.py generate-case -n "case_name" -d "Case description" -p '["C:\path\to\file1.md","C:\path\to\file2.md"]'
```

**With both fixtures and external files:**

```powershell
python test.py generate-case -n "case_name" -d "Case description" -f "small" -p '["C:\file1.md"]'
```

**Available fixtures and presets:**

Fixtures (use individually or in presets):
- `small` - small.md
- `large` - large.txt
- `code` - code.py
- `readme` - readme.txt

Presets (shorthand for common combinations):
- `quick` - small only (fastest)
- `multi-format` - small, code, readme
- `all` - all fixtures
- `performance` - large only

**Examples:**

Quick test with smallest file:
```powershell
python test.py generate-case -n "quick-test" -d "Fast test" -f "quick"
```

Multi-format test:
```powershell
python test.py generate-case -n "formats-test" -d "Testing multiple file formats" -f "multi-format"
```

With external files:
```powershell
python test.py generate-case -n "mixed-test" -d "Fixtures + external" -f "small" -p '["C:\Documents\external.md"]'
```

## Update Case (Create New Iteration)

Create a new timestamped iteration for an existing case. Useful for re-running tests after code changes.

```powershell
python test.py update-case -n "case_name"
```

**Example:**

```powershell
python test.py update-case -n "clipboard_issues"
```

## Update File Paths

Dynamically refresh relative file paths for a case based on current directory structure.

```powershell
python test.py update-paths -n "case_name"
```

**Example:**

```powershell
python test.py update-paths -n "clipboard_issues"
```

## Validate Case

Validate outputs against inputs and check if files were processed correctly. Analyzes execution logs, fixture files, and **captured clipboard outputs**.

```powershell
python test.py validate-case -n "case_name"
```

**What it checks:**
- Input files exist and file sizes
- Fixture files were copied correctly
- Output files were generated
- Whether input filenames appear in outputs
- Markdown formatting in captured outputs (headers, structure)
- Captured clipboard outputs from `script-output-*.txt` files
- Fixture file references in captured content

**Example:**

```powershell
python test.py validate-case -n "clipboard_issues"
```

## View Test Structure

Check what's been created for a case:

```powershell
Get-ChildItem -Path "testing\clipboard_issues" -Recurse | Select-Object FullName
```

## View Logs

**Parameters (case metadata):**

```powershell
Get-Content testing\parameters.jsonl | ConvertFrom-Json
```

**Process logs (test infrastructure operations):**

```powershell
Get-Content testing\process.jsonl | ConvertFrom-Json
```

**Execution logs (script run results):**

```powershell
Get-Content testing\logs\execution.jsonl | ConvertFrom-Json
```

## Workflow Example

Complete workflow for testing and validation:

```powershell
# 1. Create test case with specific files
python test.py generate-case -n "my-test" -d "My test case" -p '["C:\file1.md","C:\file2.md"]'

# 2. Run the script hotkey (Ctrl+Shift+Alt+C in Explorer with files selected)
# Script writes output files and execution logs

# 3. Create new iteration (for re-testing after changes)
python test.py update-case -n "my-test"

# 4. Validate results
python test.py validate-case -n "my-test"

# 5. Check logs for detailed analysis
Get-Content testing\logs\execution.jsonl
Get-Content testing\process.jsonl
```

## Parameters Reference

All test data is stored as JSON-Lines (`.jsonl`) format, one JSON object per line.

### parameters.jsonl

```json
{
  "case_name": "string",
  "case_description": "string",
  "relative_file_paths": ["path1", "path2"],
  "test_input_paths": ["C:\full\path\file1.md", "C:\full\path\file2.md"],
  "created_at": "2026_05_23-20_07",
  "updated_at": "2026_05_23-20_15"
}
```

### process.jsonl

```json
{
  "timestamp": "2026-05-23T20:35:47",
  "action": "generate-case|update-case|update-paths|validate-case",
  "status": "success|failed|error",
  "case_name": "string",
  "details": {...},
  "error": "error message if applicable"
}
```

### execution.jsonl

```json
{
  "timestamp": "2026-05-23T20:39:00",
  "status": "success|partial|failed|no_files",
  "files_requested": 3,
  "files_processed": 3,
  "files_failed": 0,
  "files_skipped": 0
}
```
