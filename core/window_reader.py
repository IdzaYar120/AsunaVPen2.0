import ctypes

def get_active_window_title():
    try:
        # Get handle of active window
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        
        # Get window title length
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        
        # Create buffer
        buff = ctypes.create_unicode_buffer(length + 1)
        
        # Get window text
        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
        
        return buff.value
    except Exception as e:
        return ""
