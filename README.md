# Shortcut Launcher

A Windows system-tray launcher that builds menus from the folders and files in `shortcuts/`.

## Requirements

- Windows
- Python 3

Install the Python packages from PowerShell in the project directory:

```powershell
py -m pip install pystray Pillow watchdog comtypes
```

## Run

```powershell
py src/main.py
```

The launcher icon appears in the system tray. Choose **Exit** from its menu to close the launcher.

## Menu behavior

- Subfolders in `shortcuts/` become nested menus. The menu refreshes automatically when files or folders change.
- `.lnk` and `.exe` entries launch directly.
- `.bat` and `.cmd` entries show `[ ]` when unselected and `[x]` when selected. Selections are saved in the user's AppData and restored when the launcher restarts. Each folder has its own **Run selected scripts** action, which runs that folder's selected scripts in alphabetical order.
- Synchronous scripts run one at a time. The next script starts only after the current script exits successfully; a nonzero exit code stops the sequence.
- Mark a batch file asynchronous by putting `:: launcher: async` on one of its first ten lines. The launcher waits five seconds before starting it in a new console, then continues without waiting for its exit code.
- Clicking a batch-file entry directly opens it in a new console; the async marker only affects **Run selected scripts**.

For synchronous batch files, use `exit /b 0` for success and a nonzero `exit /b` code for failure so the launcher can detect the result.

## Configuration

Edit `SHORTCUTS_DIR` and `ICON_PATH` near the top of `src/main.py` to use different locations. The default paths point to this checkout at `C:\dev\launcher`; `src/launcher.ico` is included in the project.