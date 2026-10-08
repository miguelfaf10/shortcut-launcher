import os
import subprocess
import threading
import time
import comtypes.client
from pathlib import Path
import pystray
from pystray import MenuItem as Item, Menu
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

SHORTCUTS_DIR = Path(r"C:\dev\launcher\shortcuts")  # change this
ICON_PATH = Path(r"C:\dev\launcher\src\launcher.ico")
SELECTED_SCRIPTS = {}


def open_shortcut(path: Path):
    """Open a shortcut, exe, or batch file."""
    ext = path.suffix.lower()
    print(f"Starting: {path}")

    try:
        if ext == ".bat" or ext == ".cmd":
            # Run through cmd.exe
            subprocess.Popen(["cmd.exe", "/c", str(path)],
                             #shell=True)
                             creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen(['explorer', str(path)])
            #subprocess.call(path, shell=True)
    except Exception as e:
        print(f"Error opening {path}: {e}")


def make_shortcut_item(name: str, path: Path, folder: Path):
    """Return a menu item that opens a shortcut or selects a script."""
    if path.suffix.lower() in (".bat", ".cmd"):
        def toggle_selection(icon, item):
            selected = SELECTED_SCRIPTS.setdefault(folder, set())
            if path in selected:
                selected.remove(path)
            else:
                selected.add(path)
            update_menu(icon)

        return Item(
            lambda item: f"[{'x' if path in SELECTED_SCRIPTS.get(folder, set()) else ' '}] {name}",
            toggle_selection,
        )

    def action(icon, item):
        open_shortcut(path)
    return Item(name, action)


def is_async_script(path: Path) -> bool:
    """Check the first ten lines for the launcher async directive."""
    try:
        with path.open("rb") as script:
            for _ in range(10):
                line = script.readline()
                if not line:
                    break
                if line.strip().lower() == b":: launcher: async":
                    return True
    except OSError as e:
        print(f"Could not inspect {path}: {e}")
    return False


def build_menu_from_folder(folder: Path):
    """Recursively build a pystray Menu for a given folder."""
    script_items = []
    shortcut_items = []
    has_shortcut_entry = False
    items = []
    for entry in sorted(folder.iterdir()):
        if entry.is_dir():
            subitems = build_menu_from_folder(entry)
            if subitems:  # only add non-empty folders
                shortcut_items.append(Item(entry.name, Menu(*subitems)))
        elif entry.suffix.lower() in [".lnk", ".exe", ".bat", ".cmd"]:
            item = make_shortcut_item(entry.stem, entry, folder)
            if entry.suffix.lower() in (".bat", ".cmd"):
                script_items.append(item)
            else:
                shortcut_items.append(item)
                has_shortcut_entry = True

    if script_items:
        items.append(Item(
            "Run selected scripts",
            lambda icon, item: run_selected_scripts(icon, item, folder),
            enabled=lambda item: bool(SELECTED_SCRIPTS.get(folder)),
        ))
        items.append(Menu.SEPARATOR)
        items.extend(script_items)
    if script_items and has_shortcut_entry:
        items.append(Menu.SEPARATOR)
    items.extend(shortcut_items)
    return items


def run_selected_scripts(icon, item, folder: Path):
    """Run this folder's selected batch files one at a time."""
    scripts = sorted(SELECTED_SCRIPTS.get(folder, set()), key=lambda path: str(path).casefold())

    def run_scripts():
        for path in scripts:
            print(f"Running selected script: {path}")
            try:
                command = ["cmd.exe", "/c", str(path)]
                if is_async_script(path):
                    time.sleep(5)
                    subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    result = subprocess.run(
                        command,
                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                        check=False,
                    )
                    if result.returncode != 0:
                        print(f"Script failed with exit code {result.returncode}; stopping sequence.")
                        break
            except Exception as e:
                print(f"Error running {path}: {e}")
                break

    if scripts:
        threading.Thread(target=run_scripts).start()


def build_menu():
    items = build_menu_from_folder(SHORTCUTS_DIR)
    items.append(Item("Exit", lambda icon, item: icon.stop()))
    return Menu(*items)


def update_menu(icon):
    """Rebuild the tray menu dynamically."""
    icon.menu = build_menu()
    icon.update_menu()


class FolderChangeHandler(FileSystemEventHandler):
    """Handler that triggers menu update on folder changes."""
    def __init__(self, icon):
        super().__init__()
        self.icon = icon

    def on_any_event(self, event):
        update_menu(self.icon)


def create_tray_icon():
    image = Image.open(ICON_PATH)
    icon = pystray.Icon("ShortcutLauncher", image, "Shortcut Launcher", build_menu())
    return icon


if __name__ == "__main__":
    print("######## Shortcut Launcher ########")
    tray_icon = create_tray_icon()

    # Start watchdog observer
    observer = Observer()
    event_handler = FolderChangeHandler(tray_icon)
    observer.schedule(event_handler, str(SHORTCUTS_DIR), recursive=True)
    observer.start()

    try:
        tray_icon.run()
    finally:
        observer.stop()
        observer.join()
