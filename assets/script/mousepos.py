import pyautogui
import pygetwindow as gw
from tendo import singleton

me = singleton.SingleInstance()  # will sys.exit(-1) if another instance is running

# Specify the title of the application window you want to monitor
app_window_title = "MapleStory"

print('Press Ctrl-C to quit.')

try:
    while True:
        # Get the active window
        active_window = gw.getWindowsWithTitle(app_window_title)[0]

        # Get the relative mouse position within the application window
        rel_x, rel_y = pyautogui.position()
        rel_x -= active_window.left
        rel_y -= active_window.top

        position_str = 'X: ' + str(rel_x).rjust(4) + ' Y: ' + str(rel_y).rjust(4)
        print(position_str, end='')
        print('\b' * len(position_str), end='', flush=True)
except KeyboardInterrupt:
    print('\n')
