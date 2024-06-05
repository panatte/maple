import pydirectinput
import time

def home():
    while True:
        time.sleep(1)
        print("pressing home key")
        pydirectinput.press("home")
home()