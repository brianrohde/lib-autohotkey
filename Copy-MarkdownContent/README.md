# Copy-MarkdownContent

Copies selected file contents as Markdown to clipboard with a single hotkey. Supports multiple files from Windows Explorer or file search results.

## Quick Start

1. Run `Copy-MarkdownContent.ahk`
2. Select files in Windows Explorer or file search
3. Press `Ctrl+Shift+Alt+C`
4. Contents are copied to clipboard as Markdown with file headers

## Features

- **Multi-file support**: Select multiple files and copy all at once
- **Automatic fallback**: Uses COM method first, falls back to clipboard if needed
- **Markdown formatting**: Adds file headers (`# filename`) for clarity
- **Error handling**: Skips directories, handles missing files gracefully
- **Execution logging**: Tracks all runs in `testing/logs/execution.jsonl`
- **Debug output**: Shows detailed debug info when clipboard is empty

## Hotkey

- `Ctrl+Shift+Alt+C` - Copy selected files

## Output Format

```markdown
# filename1.txt

[file contents]

# filename2.md

[file contents]
```

## Testing

See `commands.md` for complete testing workflow.

### Quick Test

```powershell
# Generate test case
python test.py generate-case -n "my-test" -d "Test description" -p '["C:\path\to\file1.md"]'

# Validate results
python test.py validate-case -n "my-test"
```

## Logs

- **Execution logs**: `testing/logs/execution.jsonl` - Script run results
- **Process logs**: `testing/process.jsonl` - Test infrastructure operations
- **Parameters**: `testing/parameters.jsonl` - Test case metadata

## Known Issues

See test results in `testing/` directory for current behavior and edge cases.

## Dependencies

- AutoHotkey v2.0+
- Windows Explorer or compatible file manager
- Python 3.8+ (for testing only)
