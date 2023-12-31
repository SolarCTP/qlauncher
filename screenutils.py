from screeninfo import get_monitors
from typing import Any
import win32api
import pygetwindow as pgw
    
def get_primary_monitor_refreshrate() -> int:
    device = win32api.EnumDisplayDevices()
    settings = win32api.EnumDisplaySettings(device.DeviceName, -1)
    return settings.DisplayFrequency

def get_primary_monitor_info() -> dict[str, Any]:
    """Returns a dict with the following information about the primary monitor: width,
    height, resolution, pygame id"""
    monitors = get_monitors()
    for monitor in monitors:
        if monitor.is_primary:
            monitor_info = {
                'width': monitor.width,
                'height': monitor.height,
                'resolution': (monitor.width, monitor.height),
                'id': int(monitor.name[11::]) - 1,
                'refreshrate': get_primary_monitor_refreshrate()
            }
            return monitor_info


def calc_window_resolution(window_scale: float) -> tuple[int, int]:
    """returns the window resolution, which is the monitor's resolution multiplied
    by the window_scale factor"""
    monitor_info = get_primary_monitor_info()
    window_resolution = (monitor_info['width'] * window_scale, monitor_info['height'] * window_scale)
    return window_resolution

