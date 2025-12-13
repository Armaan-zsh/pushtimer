import os
import threading

def play_sound():
    """Play a system beep sound without external dependencies if possible."""
    def _play():
        try:
            # Method 1: echo -e '\a'
            os.system("echo -e '\a'")
            # Method 2: paplay if available (common on linux)
            # os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga")
        except:
            pass
            
    threading.Thread(target=_play, daemon=True).start()
