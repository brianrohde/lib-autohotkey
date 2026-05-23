# DateStamps

Insert, copy, and manage date/time stamps with configurable formats. Includes smart file rename functionality that preserves existing timestamps or adds new ones intelligently.

## Quick Start

1. Run `DateStamps.ahk`
2. Use hotkeys to insert or manage timestamps
3. Configure formats in `settings.ini`

## Hotkeys

- `Alt+D` - Insert primary timestamp
- `Alt+Shift+D` - Insert variant timestamp
- `Alt+Ctrl+D` - Show menu with all options
- `Ctrl+Shift+Ctrl+U` - Apply smart rename to selected file

## Menu Options

When you press `Alt+Ctrl+D`, a menu appears with:

### Insert Stamps (1-4)
- `yyyy_MM_dd` (e.g., 2026_05_23)
- `yyyy_MM_dd-HH_mm` (e.g., 2026_05_23-20_15)
- `yyyy_MM_dd-HH_mm_ss` (e.g., 2026_05_23-20_15_47)
- `dd.MM.yyyy` (e.g., 23.05.2026)

### Copy Stamps (5-6)
- Copy primary stamp to clipboard
- Copy variant stamp to clipboard

### Set Defaults (7-10)
- Set PRIMARY format
- Set VARIANT format

### Rename (11-12)
- Apply smart rename logic to selected file
- Toggle IncludeTime setting (auto/always/never)

## Configuration

Edit `settings.ini` to customize behavior:

```ini
[Date]
Primary=yyyy_MM_dd
Variant=yyyy_MM_dd-HH_mm

[Rename]
IncludeTime=auto
TimePrecision=minutes
Position=preserve
```

### Settings Explained

- **Primary/Variant**: Format strings for primary and variant timestamps
- **IncludeTime**: 
  - `auto` - Include time only if file already has timestamp with time
  - `always` - Always include time (HH_mm)
  - `never` - Never include time
- **TimePrecision**: `minutes` or `seconds` for time format
- **Position**: `preserve` keeps timestamp in original position, or `prepend` to add at start

## Smart Rename Logic

The rename engine:
1. Detects existing timestamps in filename
2. Removes Windows "Copy" suffix if present
3. Replaces or adds timestamp based on settings
4. Preserves file extension

### Examples

```
Original: document.txt
Result:   2026_05_23-document.txt

Original: 2026_05_20-old.txt (with IncludeTime=always)
Result:   2026_05_23-20_15-old.txt

Original: Project - Copy.xlsx
Result:   2026_05_23-Project.xlsx
```

## Dependencies

- AutoHotkey v2.0+
- `settings.ini` in same directory as script
