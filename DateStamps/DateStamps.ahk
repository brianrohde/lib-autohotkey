#Requires AutoHotkey v2.0
#SingleInstance Force

; =========================================
; CONFIG FILE
; =========================================

iniFile := A_ScriptDir "\settings.ini"

; =========================================
; LOAD SETTINGS
; =========================================

PrimaryStampFmt := IniRead(iniFile, "Date", "Primary", "yyyy_MM_dd")
VariantStampFmt := IniRead(iniFile, "Date", "Variant", "yyyy_MM_dd-HH_mm")

RenameIncludeTime := IniRead(iniFile, "Rename", "IncludeTime", "auto")
RenameTimePrecision := IniRead(iniFile, "Rename", "TimePrecision", "minutes")
RenamePosition := IniRead(iniFile, "Rename", "Position", "preserve")

; =========================================
; HOTKEYS
; =========================================

!d:: {
    global PrimaryStampFmt
    SendText FormatTime(, PrimaryStampFmt)
}

!+d:: {
    global VariantStampFmt
    SendText FormatTime(, VariantStampFmt)
}

!#d:: {
    ShowDateMenu()
}

^+#u:: {
    ApplySmartRename()
}

; =========================================
; MENU
; =========================================

ShowDateMenu() {

    m := Menu()

    ; Insert
    m.Add("1. Insert yyyy_MM_dd", (*) => InsertStamp("yyyy_MM_dd"))
    m.Add("2. Insert yyyy_MM_dd-HH_mm", (*) => InsertStamp("yyyy_MM_dd-HH_mm"))
    m.Add("3. Insert yyyy_MM_dd-HH_mm_ss", (*) => InsertStamp("yyyy_MM_dd-HH_mm_ss"))
    m.Add("4. Insert dd.MM.yyyy", (*) => InsertStamp("dd.MM.yyyy"))

    m.Add()

    ; Copy
    m.Add("5. Copy primary", (*) => CopyStamp("Primary"))
    m.Add("6. Copy variant", (*) => CopyStamp("Variant"))

    m.Add()

    ; Defaults
    m.Add("7. Set PRIMARY → yyyy_MM_dd", (*) => SetPrimary("yyyy_MM_dd"))
    m.Add("8. Set PRIMARY → yyyy_MM_dd-HH_mm", (*) => SetPrimary("yyyy_MM_dd-HH_mm"))
    m.Add("9. Set VARIANT → yyyy_MM_dd-HH_mm", (*) => SetVariant("yyyy_MM_dd-HH_mm"))
    m.Add("10. Set VARIANT → yyyy_MM_dd-HH_mm_ss", (*) => SetVariant("yyyy_MM_dd-HH_mm_ss"))

    m.Add()

    ; Rename
    m.Add("11. Apply rename logic", (*) => ApplySmartRename())

    m.Add()

    ; Rename config
    m.Add("12. Toggle IncludeTime (auto/always/never)", (*) => ToggleIncludeTime())

    m.Show()
}

; =========================================
; BASIC ACTIONS
; =========================================

InsertStamp(fmt) {
    SendText FormatTime(, fmt)
}

CopyStamp(type) {
    global PrimaryStampFmt, VariantStampFmt

    fmt := (type = "Primary") ? PrimaryStampFmt : VariantStampFmt
    A_Clipboard := FormatTime(, fmt)

    ToolTip "Copied: " A_Clipboard
    SetTimer () => ToolTip(), -1000
}

SetPrimary(fmt) {
    global PrimaryStampFmt, iniFile

    PrimaryStampFmt := fmt
    IniWrite(fmt, iniFile, "Date", "Primary")

    ToolTip "Primary set: " fmt
    SetTimer () => ToolTip(), -1000
}

SetVariant(fmt) {
    global VariantStampFmt, iniFile

    VariantStampFmt := fmt
    IniWrite(fmt, iniFile, "Date", "Variant")

    ToolTip "Variant set: " fmt
    SetTimer () => ToolTip(), -1000
}

ToggleIncludeTime() {
    global RenameIncludeTime, iniFile

    if (RenameIncludeTime = "auto")
        RenameIncludeTime := "always"
    else if (RenameIncludeTime = "always")
        RenameIncludeTime := "never"
    else
        RenameIncludeTime := "auto"

    IniWrite(RenameIncludeTime, iniFile, "Rename", "IncludeTime")

    ToolTip "IncludeTime: " RenameIncludeTime
    SetTimer () => ToolTip(), -1000
}

; =========================================
; RENAME ENGINE
; =========================================

ApplySmartRename() {

    global PrimaryStampFmt, RenameIncludeTime, RenameTimePrecision, RenamePosition

    oldClip := A_Clipboard
    A_Clipboard := ""

    Send "^c"
    if !ClipWait(0.6) {
        A_Clipboard := oldClip
        return
    }

    name := A_Clipboard

    ; ------------------------------
    ; Remove Windows "Copy"
    ; ------------------------------
    name := RegExReplace(name, "\s-\s(?:Copy|Kopie)(?:\s\(\d+\))?$")

    ; ------------------------------
    ; Detect existing timestamp
    ; ------------------------------
    hasTime := false

    patterns := [
        "\b\d{4}[-_]\d{2}[-_]\d{2}[-_ ]\d{2}[-_:]\d{2}(?:[-_:]\d{2})?\b",
        "\b\d{4}[-_]\d{2}[-_]\d{2}\b",
        "\b\d{2}\.\d{2}\.\d{4}\b"
    ]

    found := ""
    for p in patterns {
        if RegExMatch(name, p, &m) {
            found := m[0]
            if RegExMatch(found, "\d{2}[:_-]\d{2}")
                hasTime := true
            break
        }
    }

    ; ------------------------------
    ; Decide final format
    ; ------------------------------
    fmt := PrimaryStampFmt

    if (RenameIncludeTime = "always") {
        fmt := "yyyy_MM_dd-HH_mm"
    }
    else if (RenameIncludeTime = "never") {
        fmt := "yyyy_MM_dd"
    }
    else if (RenameIncludeTime = "auto" && hasTime) {
        fmt := "yyyy_MM_dd-HH_mm"
    }

    newStamp := FormatTime(, fmt)

    ; ------------------------------
    ; Replace or prepend
    ; ------------------------------
    if (found != "") {
        name := StrReplace(name, found, newStamp)
    } else {
        name := newStamp "-" name
    }

    ; ------------------------------
    ; Write back
    ; ------------------------------
    Send "^a"
    SendText name

    A_Clipboard := oldClip
}