# Copy-MarkdownContent Test Commands

Quick reference for managing and validating test cases.

## Generate a New Test Case

Create a new test case with optional file inputs to track.

```powershell
python test.py generate-case -n "case_name" -d "Case description"
```

With test input files:

```powershell
python test.py generate-case -n "case_name" -d "Case description" -p '["C:\path\to\file1.md","C:\path\to\file2.md"]'
```

**Example:**

```powershell
python test.py generate-case -n "clipboard_issues" -d "Testing clipboard handling with multiple file types" -p '["C:\Local Documents\test1.md","C:\Local Documents\test2.pdf"]'
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

Validate outputs against inputs and check if files were processed correctly. Analyzes execution logs and output files.

```powershell
python test.py validate-case -n "case_name"
```

**What it checks:**
- Input files exist and file sizes
- Output files were generated
- Whether input filenames appear in outputs
- Output content length and readability

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
