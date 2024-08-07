import ctypes
import os
import sys


def is_number(s):
    """
    判断一个字符串是否为数字（整数或浮点数）。
    包含正负号和小数点的情况。
    """
    try:
        float(s)
        return True
    except ValueError:
        return False


def format_to_two_places(value):
    return float(f"{value:.2f}")


def format_to_integer(value):
    return int(value)

def format_currency(value):
    try:
        # 确保传递给该函数的值是整数
        value = int(value)
        formatted_value = "{:,}".format(value)
        return formatted_value
    except Exception as e:
        print(f"Error formatting currency: {e}")
        return str(value)  # 返回原始值，以防止显示问题#

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def set_num_lock(state):
    # Get the current state of the Num Lock key
    hllDll = ctypes.WinDLL("User32.dll")
    VK_NUMLOCK = 0x90
    if state:
        if (hllDll.GetKeyState(VK_NUMLOCK) & 0x0001) == 0:
            hllDll.keybd_event(VK_NUMLOCK, 0x45, 0x1, 0)
            hllDll.keybd_event(VK_NUMLOCK, 0x45, 0x1 | 0x2, 0)
    else:
        if (hllDll.GetKeyState(VK_NUMLOCK) & 0x0001) != 0:
            hllDll.keybd_event(VK_NUMLOCK, 0x45, 0x1, 0)
            hllDll.keybd_event(VK_NUMLOCK, 0x45, 0x1 | 0x2, 0)

