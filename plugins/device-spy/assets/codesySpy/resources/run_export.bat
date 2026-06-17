@echo off
REM Launcher for export_project.py (the CODESYS headless export).
REM STATIC + ENV-DRIVEN: /codesySpy sets these env vars before invoking via `cmd /c`;
REM the cmd child and CODESYS.exe inherit them, so the password (CODESYS_PW, read by
REM export_project.py) rides in the environment only -- never a command line, never disk.
REM   CODESYS_EXE      full path to CODESYS.exe   (auto-detected newest install)
REM   CODESYS_PROFILE  installed profile name     (e.g. "CODESYS V3.5 SP21 Patch 4")
REM   CODESYS_SCRIPT   full path to export_project.py
REM
REM --noUI runs CODESYS headless; --profile must match an installed profile name
REM exactly (incl. patch number). The profile name contains spaces, so it must be a
REM quoted value INSIDE the flag. PowerShell strips those inner quotes, so this
REM launcher is a .bat invoked via `cmd /c` to preserve the quoting.

"%CODESYS_EXE%" ^
    --noUI ^
    --profile="%CODESYS_PROFILE%" ^
    --runscript="%CODESYS_SCRIPT%"

echo.
echo Exit code: %ERRORLEVEL%
