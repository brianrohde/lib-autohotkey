# lib-autohotkey

A collection of AutoHotkey v2.0 scripts and utilities for productivity and automation on Windows.

## Contents

### Copy-MarkdownContent
Copies selected file contents as Markdown to clipboard with a single hotkey. Includes a comprehensive testing framework for validation and debugging.

- **Hotkey**: `Ctrl+Shift+Alt+C`
- **Features**: Multi-file support, fallback to clipboard method, execution logging
- [View README](./Copy-MarkdownContent/README.md)

### DateStamps
Insert, copy, and manage date/time stamps with configurable formats. Includes smart file rename functionality.

- **Hotkeys**: 
  - `Alt+D` - Insert primary stamp
  - `Alt+Shift+D` - Insert variant stamp
  - `Alt+Ctrl+D` - Show menu
  - `Ctrl+Shift+Ctrl+U` - Apply smart rename
- **Features**: Configurable formats, INI settings, smart rename engine
- [View README](./DateStamps/README.md)

## Installation

1. Clone this repository
2. Install [AutoHotkey v2.0](https://www.autohotkey.com/v2/)
3. Run any script directly, or add to startup folder for auto-launch

## Requirements

- Windows 10+
- AutoHotkey v2.0+
- Python 3.8+ (for Copy-MarkdownContent testing)

## Version Control

Each script directory can be developed, tested, and versioned independently. Use the testing framework in Copy-MarkdownContent as a template for your own validation.

## License

Public domain. Free to use and modify.
