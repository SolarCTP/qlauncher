from tkinter.filedialog import askopenfilename
import pygetwindow as pgw
import traceback as tb
from state import State

DEFAULT_WINDOW_TITLE: str = "QLauncher"

def filedialog_executable(cell_id: int):
    """cell_id only need for info on the dialog title. File select dialog for exe, com,
    bat, py, ps1 and url executable files. Returns a string with the absolute path
    of selected executable."""
    executable_filetypes = (
                            ("Supported executables",
                             ["*.lnk",
                              "*.exe",
                              "*.url"]),
                        )
    return askopenfilename(filetypes=executable_filetypes,
                           title=f"Please choose the program for button ID {cell_id}")

def filedialog_image(cell_id: int):
    image_filetypes = (
        ("JPG image", "*.jpg"),
        ("JPEG image", "*.jpeg"),
        ("PNG image", "*.png"),
        ("Windows icon file", "*.ico")
    )
    return askopenfilename(filetypes=image_filetypes,
                           title=f"Please choose the image for button ID {cell_id}")

def get_window_by_title(window_title: str) -> pgw.Win32Window:
    matching_window_list = pgw.getWindowsWithTitle(title=window_title) # gets windows containing that string in their title
    for win in matching_window_list:
        win: pgw.Win32Window
        if win.title == window_title: # gets only the exact match
            return win

def restore_window() -> bool:
    """restores a minimized a window, will return true if it was succesfully restored.
    the title must be an EXACT MATCH"""
    try:
        get_window_by_title(DEFAULT_WINDOW_TITLE).restore()
    except Exception as e:
        print(str(e))
        return False

_minimize_triggered = 0
def minimize_if_unfocused() -> int:
    """minimizes the window if it is not focused. we don't want the window to hang around if
    it is not active.

    Return codes:

    - 0 = succesfully minimized;
    - 1 = failed;
    - 2 = nothing done, not needed
    """
    global _minimize_triggered
    try:
        win = get_window_by_title(DEFAULT_WINDOW_TITLE)
        if not win.isActive and _minimize_triggered == 0:
            win.minimize()
            _minimize_triggered += 1
            return 0
        else:
            return 2
    except Exception:
        tb.print_exc()
        return 1
