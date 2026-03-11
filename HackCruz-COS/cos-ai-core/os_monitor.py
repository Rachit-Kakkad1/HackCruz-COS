"""
COS AI Core — OS Context Monitor
Tracks the active window title and executable name periodically on Windows.
"""
import time
import psutil
try:
    import win32gui
    import win32process
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False


def get_active_window_info():
    """Returns the title and executable name of the currently active window."""
    if not WINDOWS_AVAILABLE:
        return {"app": "Unknown OS", "title": "Requires Windows", "pid": 0}

    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        
        try:
            process = psutil.Process(pid)
            exe_name = process.name()
            
            # Workspace detection for automation
            workspace = None
            if exe_name == "Code.exe":
                cmdline = process.cmdline()
                # VSCode usually passes the folder path as an argument
                for arg in cmdline:
                    if ":" in arg and "\\" in arg and not arg.startswith("-"):
                        workspace = arg
                        break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            exe_name = "Unknown"
            workspace = None
            
        # Ignore empty or desktop processes
        if not title or exe_name in ["explorer.exe", "Idle"]:
            return None
            
        return {
            "app": exe_name,
            "title": title,
            "pid": pid,
            "workspace": workspace
        }
    except Exception as e:
        print(f"[OS Monitor] Error retrieving window info: {e}")
        return None

if __name__ == "__main__":
    # Quick test
    while True:
        info = get_active_window_info()
        print(info)
        time.sleep(2)
