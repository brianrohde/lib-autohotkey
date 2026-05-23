#Requires AutoHotkey v2.0
#SingleInstance Force

; Copy selected file contents as Markdown to clipboard
; Hotkey: Ctrl+Shift+Alt+C
; Works by reading selected files from Windows Explorer

scriptDir := A_ScriptDir
logsDir := scriptDir . "\testing\logs"
logsFile := logsDir . "\execution.jsonl"

^+!c:: {
    result := CopyMarkdownContent()
    LogExecution(result)
    ToolTip
}

CopyMarkdownContent() {
    debug := ""
    result := Map()
    result["status"] := "error"
    result["files_requested"] := 0
    result["files_processed"] := 0
    result["debug"] := ""

    ; Get the active window
    hwnd := WinGetID("A")

    ; Try to get selected files from Explorer
    files := GetSelectedFilesFromExplorer(&debug)
    result["files_requested"] := files.Length

    if (files.Length = 0) {
        debug .= "DEBUG: No files selected in Explorer`n"
        result["status"] := "no_files"
        result["debug"] := debug
        A_Clipboard := debug
        ToolTip "No files selected"
        SetTimer () => ToolTip(), -2000
        return result
    }

    output := ""
    processedCount := 0
    failedCount := 0
    skippedCount := 0

    for filePath in files {
        debug .= "DEBUG: Processing: " filePath "`n"

        ; Check if file exists
        if (!FileExist(filePath)) {
            debug .= "DEBUG:   -> File does not exist`n"
            failedCount++
            continue
        }

        ; Skip directories
        if (InStr(FileGetAttrib(filePath), "D")) {
            debug .= "DEBUG:   -> Is directory, skipping`n"
            skippedCount++
            continue
        }

        try {
            ; Get filename (last part after last backslash)
            lastBackslash := 0
            loop {
                pos := InStr(filePath, "\", , lastBackslash + 1)
                if (pos = 0)
                    break
                lastBackslash := pos
            }
            fileName := SubStr(filePath, lastBackslash + 1)

            ; Read file content
            content := FileRead(filePath)

            ; Add to output
            output .= "# " . fileName . "`n`n" . content . "`n`n"
            processedCount++
            debug .= "DEBUG:   -> Successfully processed`n"
        }
        catch as err {
            debug .= "DEBUG:   -> Error reading: " err.What "`n"
            failedCount++
        }
    }

    result["files_failed"] := failedCount
    result["files_skipped"] := skippedCount

    result["files_processed"] := processedCount
    result["debug"] := debug

    ; Clear clipboard first, then set new content
    A_Clipboard := ""

    if (output != "") {
        A_Clipboard := output
        if (processedCount > 0 && failedCount = 0) {
            result["status"] := "success"
        } else {
            result["status"] := "partial"
        }
        ToolTip "✓ Copied " processedCount " file(s)"
        SetTimer () => ToolTip(), -2000
        LogClipboardOutput(result, output)
    } else {
        A_Clipboard := debug
        result["status"] := "failed"
        ToolTip "⚠ No files processed (failed: " failedCount ", skipped: " skippedCount ")"
        SetTimer () => ToolTip(), -2000
        LogClipboardOutput(result, debug)
    }

    return result
}

GetSelectedFilesFromExplorer(&debugOut := "") {
    files := []

    try {
        ; Get all Explorer windows
        shell := ComObject("Shell.Application")
        debugOut .= "DEBUG: Checking " shell.Windows.Count " explorer windows`n"

        for window in shell.Windows {
            try {
                ; Get the document (folder view)
                doc := window.Document
                if !IsObject(doc) {
                    debugOut .= "DEBUG:   Window has no document`n"
                    continue
                }

                ; Get selected items
                selectedItems := doc.SelectedItems
                if !IsObject(selectedItems) {
                    debugOut .= "DEBUG:   Window has no selected items`n"
                    continue
                }

                itemCount := selectedItems.Count
                debugOut .= "DEBUG: Found " itemCount " selected items in window`n"

                ; Extract file paths from selected items
                for item in selectedItems {
                    try {
                        ; Try multiple methods to get the path
                        filePath := ""

                        if (item.IsFolder) {
                            filePath := item.Self.Path
                            debugOut .= "DEBUG:   Item is folder, path: " filePath "`n"
                        } else {
                            filePath := item.Path
                            if (filePath = "") {
                                filePath := item.GetLink.Path
                            }
                            if (filePath = "") {
                                filePath := item.Self.Path
                            }
                            debugOut .= "DEBUG:   Item is file, path: " filePath "`n"
                        }

                        if (filePath != "") {
                            files.Push(filePath)
                        }
                    }
                    catch as err {
                        debugOut .= "DEBUG:   Error extracting path: " err.What "`n"
                        continue
                    }
                }
            }
            catch as err {
                debugOut .= "DEBUG:   Window error: " err.What "`n"
                continue
            }
        }
    }
    catch as err {
        debugOut .= "DEBUG: COM Error: " err.What ". Trying clipboard...`n"
        ; If COM method fails, fall back to clipboard method
        return GetSelectedFilesFromClipboard(&debugOut)
    }

    return files
}

GetSelectedFilesFromClipboard(&debugOut := "") {
    files := []

    ; Fallback: Copy selected files to clipboard, parse paths
    oldClip := A_Clipboard
    A_Clipboard := ""
    Sleep(100)

    debugOut .= "DEBUG: Trying clipboard method...`n"

    ; Send Ctrl+C to copy selected files
    Send "^c"

    ; Wait for clipboard to populate (max 1 second)
    if (!ClipWait(1)) {
        debugOut .= "DEBUG: Clipboard wait timeout`n"
        A_Clipboard := oldClip
        return files
    }

    ; Parse clipboard content
    rawData := A_Clipboard
    debugOut .= "DEBUG: Clipboard content (raw): " rawData "`n"
    rawData := StrReplace(rawData, "`r`n", "`n")

    ; Split into lines and filter
    lines := StrSplit(rawData, "`n")
    debugOut .= "DEBUG: Split into " lines.Length " lines`n"

    for line in lines {
        line := Trim(line)
        if (line != "" && FileExist(line)) {
            files.Push(line)
            debugOut .= "DEBUG:   Added: " line "`n"
        } else if (line != "") {
            debugOut .= "DEBUG:   Skipped (not found): " line "`n"
        }
    }

    ; Restore clipboard
    Sleep(100)
    A_Clipboard := oldClip
    Sleep(100)

    return files
}

LogClipboardOutput(result, output) {
    global scriptDir

    ; Determine scenario based on file count
    fileCount := result["files_processed"]
    if (fileCount = 0)
        return

    scenario := ""
    if (fileCount = 1)
        scenario := "single_file"
    else if (fileCount <= 5)
        scenario := "multi_file"
    else
        scenario := "many_files"

    ; Check if output is large
    outputSize := StrLen(output)
    if (outputSize > 100000)
        scenario := scenario . "_large"

    ; Create output filename
    timestamp := FormatTime(A_Now, "yyyy_MM_dd-HH_mm_ss")
    outputFileName := "script-output-" . scenario . "-" . timestamp . ".txt"

    ; Write to testing directory
    testingDir := scriptDir . "\testing"
    outputFilePath := testingDir . "\" . outputFileName

    try {
        fileHandle := FileOpen(outputFilePath, "w")
        fileHandle.Write(output)
        fileHandle.Close()
    }
    catch as err {
        ; Silently fail if testing directory doesn't exist
        return
    }
}

LogExecution(result) {
    global logsDir, logsFile

    ; Create logs directory if it doesn't exist
    if (!DirExist(logsDir)) {
        DirCreate(logsDir)
    }

    ; Create JSON log entry with proper escaping
    timestamp := FormatTime(A_Now, "yyyy-MM-dd'T'HH:mm:ss")
    jsonEntry := "{""timestamp"":""" . timestamp . """,""status"":""" . result["status"] . """,""files_requested"":" . result["files_requested"] . ",""files_processed"":" . result["files_processed"] . ",""files_failed"":" . result["files_failed"] . ",""files_skipped"":" . result["files_skipped"] . "}"

    ; Append to execution.jsonl
    fileHandle := FileOpen(logsFile, "a")
    fileHandle.Write(jsonEntry . "`n")
    fileHandle.Close()
}
