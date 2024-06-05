import keyboard
import pygetwindow as gw
import json
import mss
import pyautogui
import cv2 as cv
import numpy as np
import time
from time import sleep
import multiprocessing
import pydirectinput
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import subprocess
import platform
from tkinter import Tk, filedialog
import os

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

recorded_actions = []

def record_actions():
    global recorded_actions

    file_name = input("Enter the filename to save recorded actions (without extension): ")
    file_path = f"assets/recorded/{file_name}.json"

    recorded_actions = []

    #print("Bringing specified window to the front...")
    notepad_window = gw.getWindowsWithTitle("MapleStory")

    if notepad_window:
        notepad_window[0].activate()
    else:
        clear_console()
        print("Window not found.")
        sleep(1.5)
        clear_console()
        return

    clear_console()
    print("Recording... Press 'Home' to stop recording.")

    def on_key_event(e):
        if e.name == "home":
            return False
        recorded_actions.append({"event_type": e.event_type, "name": e.name, "time": e.time})
        return True

    keyboard.hook(on_key_event)
    keyboard.wait("home")
    keyboard.unhook_all()

    clear_console()
    print("Recording stopped.")

    with open(file_path, "w") as file:
        json.dump(recorded_actions, file)
    print(f"Recorded actions saved to '{file_path}'.")
    sleep(1.5)
    clear_console()

def play_actions():
    print("Choose a file to play recorded actions:")
    
    # Create a Tkinter root window (it won't be shown)
    root = Tk()
    root.withdraw()

    # Open a file dialog for selecting the file
    file_path = filedialog.askopenfilename(title="Select Recorded File", filetypes=[("JSON Files", "*.json")])

    try:
        with open(file_path, "r") as file:
            recorded_actions = json.load(file)

        clear_console()
        #print("Bringing specified window to the front...")
        notepad_window = gw.getWindowsWithTitle("MapleStory")

        if not notepad_window:
            clear_console()
            print("Window not found. Make sure the title is correct.")
            sleep(1.5)
            clear_console()
            return

        notepad_window[0].activate()
        time.sleep(1)
        print("Playing recorded actions... Press 'Home' to stop.")

        held_keys = set()

        while True:
            #print("Playing recorded actions... Press '8' to stop.")
            start_time = time.perf_counter()

            for i in range(len(recorded_actions)):
                action = recorded_actions[i]
                elapsed_time = action["time"] - recorded_actions[0]["time"]
                current_time = start_time + elapsed_time

                while time.perf_counter() < current_time:
                    pass  # Wait until the current time is reached

                if action["event_type"] == keyboard.KEY_DOWN:
                    keyboard.press(action["name"])
                    held_keys.add(action["name"])
                elif action["event_type"] == keyboard.KEY_UP:
                    keyboard.release(action["name"])
                    held_keys.discard(action["name"])
                    
                # Check for the stop hotkey
                if keyboard.is_pressed('home'):
                    # Release all held keys when pausing
                    for key in held_keys:
                        keyboard.release(key)
                    clear_console()
                    print("Playback stopped.")
                    sleep(1.5)
                    clear_console()
                    return

    except FileNotFoundError:
        clear_console()
        print("File not found. Please make sure the file path is correct.")
        sleep(1.5)
        clear_console()
    except json.JSONDecodeError:
        clear_console()
        print("Error loading the recorded actions from the file.")
        sleep(1.5)
        clear_console()

pygame.mixer.init()
class ScreenCaptureAgent:
    def __init__(self) -> None:
        self.img = None
        self.img_hp = None
        self.img_mp = None
        self.img_runeandplayer = None
        self.capture_process = None
        self.enable_cv_preview = True

        #HPBarScreenSizeAndPosition
        self.top_left_hp = (831, 743)
        self.bottom_right_hp = (874, 751)

        #MPBarScreenSizeAndPosition
        self.top_left_mp = (831, 759)
        self.bottom_right_mp = (874, 767)

        #WhiteRoomScreenSizeAndPosition
        self.top_left_whiteroom = (12, 87)
        self.bottom_right_whiteroom = (251, 178)

        #EliteBossScreenSizeAndPosition
        self.top_left_eliteboss = (322, 35)
        self.bottom_right_eliteboss = (324, 37)

        #MinimapScreenSizeAndPosition
        self.top_left_minimap = (12, 87)
        self.bottom_right_minimap = (251, 178)

        #ChatScreenSizeAndPosition
        self.top_left_chat = (0, 746)
        self.bottom_right_chat = (31, 754)

        #Load saved coordinates in resize option
        self.load_coordinates()

        self.w, self.h = pyautogui.size()
        #print("Screen Resolution: " + "w: " + str(self.w) + " h:" + str(self.h))
        self.monitor = {"top": 0, "left": 0, "width": self.w, "height": self.h}

        self.last_check_time = time.time()
        self.check_interval = 1  # Check every (insert value here) seconds
        self.last_check_time_autopot = time.time()
        self.check_interval_autopot = 0.1  # Check every (insert value here) seconds
        self.last_check_time_whiteroom = time.time()
        self.check_interval_whiteroom = 0.1  # Check every (insert value here) seconds
        self.mp3_rune = 'assets/audio/rune.mp3' #Rune alert sound
        self.mp3_else = 'assets/audio/else.mp3' #Players in same map and Players' texts alert sound

    def play_audio_rune(self, volume=0.45):
        pygame.mixer.music.load(self.mp3_rune)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play()

    def play_audio_else(self, volume=0.45):
        pygame.mixer.music.load(self.mp3_else)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play()

    def save_coordinates(self):
        # Save the coordinates to a JSON file in the specified location
        file_path = os.path.join("assets", "resize", "coordinates.json")
        data = {
            "top_left_hp": self.top_left_hp,
            "bottom_right_hp": self.bottom_right_hp,

            "top_left_mp": self.top_left_mp,
            "bottom_right_mp": self.bottom_right_mp,

            "top_left_whiteroom": self.top_left_whiteroom,
            "bottom_right_whiteroom": self.bottom_right_whiteroom,

            "top_left_eliteboss": self.top_left_eliteboss,
            "bottom_right_eliteboss": self.bottom_right_eliteboss,
            
            "top_left_minimap": self.top_left_minimap,
            "bottom_right_minimap": self.bottom_right_minimap,
        }
        with open(file_path, "w") as file:
            json.dump(data, file)

    def load_coordinates(self):
        # Load the coordinates from the JSON file if it exists
        file_path = os.path.join("assets", "resize", "coordinates.json")
        try:
            with open(file_path, "r") as file:
                data = json.load(file)
                self.top_left_hp = tuple(data["top_left_hp"])
                self.bottom_right_hp = tuple(data["bottom_right_hp"])

                self.top_left_mp = tuple(data["top_left_mp"])
                self.bottom_right_mp = tuple(data["bottom_right_mp"])

                self.top_left_whiteroom = tuple(data["top_left_whiteroom"])
                self.bottom_right_whiteroom = tuple(data["bottom_right_whiteroom"])

                self.top_left_eliteboss = tuple(data["top_left_eliteboss"])
                self.bottom_right_eliteboss = tuple(data["bottom_right_eliteboss"])
                
                self.top_left_minimap = tuple(data["top_left_minimap"])
                self.bottom_right_minimap = tuple(data["bottom_right_minimap"])
        except FileNotFoundError:
            pass  # File doesn't exist, use default values

    def check_hp(self, img_hp):
        rgb_hp = img_hp[:, :, :3]  # Consider only the RGB channels
        # Target color Format = BGR (BlueGreenRed)
        target_color = np.array([112, 106, 109]) # Gray color aka hp loss color
        
        # Define a threshold for each channel
        channel_threshold = 0
        
        # Check if the difference between each channel is outside the threshold
        color_difference = np.abs(rgb_hp - target_color)
        outside_threshold = np.any(color_difference > channel_threshold, axis=-1)
        
        if np.all(outside_threshold):
            p = 0  # just a placeholder
        else:
            # self.play_audio()
            pydirectinput.press('e')

    def set_hp_bar_coordinates(self):
        # Function to set HP bar coordinates during runtime
        print("Current Value:")
        print("Top-Left - "+ str(self.top_left_hp))
        print("Bottom-Right - "+ str(self.bottom_right_hp))
        print("Enter the coordinates for the Top-Left point of the HP bar (No Comma): ")
        top_left_input = input().split()
        self.top_left_hp = (int(top_left_input[0]), int(top_left_input[1]))

        print("Enter the coordinates for the Bottom-Right point of the HP bar (No Comma): ")
        bottom_right_input = input().split()
        self.bottom_right_hp = (int(bottom_right_input[0]), int(bottom_right_input[1]))

        self.save_coordinates()

    def capture_screen_hp(self):
        # Get the MapleStory window
        maplestory_window = gw.getWindowsWithTitle('MapleStory')  # Replace 'MapleStory' with the actual window title
        if not maplestory_window:
            print("MapleStory not found. Make sure the game is running.")
            
        maplestory_window = maplestory_window[0]  # Assuming there's only one MapleStory window

        with mss.mss() as sct:
            while True:
                # Get the coordinates of the MapleStory window
                left, top, width, height = maplestory_window.left, maplestory_window.top, maplestory_window.width, maplestory_window.height
                self.monitor = {"left": left, "top": top, "width": width, "height": height}

                # Capture the specified window
                self.img = sct.grab(self.monitor)
                self.img = np.array(self.img)

                self.img_hp = self.img[
                    self.top_left_hp[1]:self.bottom_right_hp[1],
                    self.top_left_hp[0]:self.bottom_right_hp[0]
                ]

                # Check HP
                current_time = time.time()
                if current_time - self.last_check_time_autopot >= self.check_interval_autopot:
                    self.check_hp(self.img_hp)
                    self.last_check_time_autopot = current_time

                # Initialize Screen
                if self.enable_cv_preview:
                    cv.imshow("HP", self.img_hp)

                cv.waitKey(1)

    def check_mp(self, img_mp):
        rgb_mp = img_mp[:, :, :3]  # Consider only the RGB channels
        # Target color Format = BGR (BlueGreenRed)
        target_color = np.array([112, 106, 109]) # Gray color aka hp loss color
        
        # Define a threshold for each channel
        channel_threshold = 0
        
        # Check if the difference between each channel is outside the threshold
        color_difference = np.abs(rgb_mp - target_color)
        outside_threshold = np.any(color_difference > channel_threshold, axis=-1)
        
        if np.all(outside_threshold):
            p = 0  # just a placeholder
        else:
            # self.play_audio()
            pydirectinput.press('e')

    def set_mp_bar_coordinates(self):
        # Function to set mp bar coordinates during runtime
        print("Current Value:")
        print("Top-Left - "+ str(self.top_left_mp))
        print("Bottom-Right - "+ str(self.bottom_right_mp))
        print("Enter the coordinates for the Top-Left point of the MP bar (No Comma): ")
        top_left_input = input().split()
        self.top_left_mp = (int(top_left_input[0]), int(top_left_input[1]))

        print("Enter the coordinates for the Bottom-Right point of the MP bar (No Comma): ")
        bottom_right_input = input().split()
        self.bottom_right_mp = (int(bottom_right_input[0]), int(bottom_right_input[1]))

        self.save_coordinates()

    def capture_screen_mp(self):
        # Get the MapleStory window
        maplestory_window = gw.getWindowsWithTitle('MapleStory')  # Replace 'MapleStory' with the actual window title
        if not maplestory_window:
            print("MapleStory not found. Make sure the game is running.")
            return

        maplestory_window = maplestory_window[0]  # Assuming there's only one MapleStory window

        with mss.mss() as sct:
            while True:
                # Get the coordinates of the MapleStory window
                left, top, width, height = maplestory_window.left, maplestory_window.top, maplestory_window.width, maplestory_window.height
                self.monitor = {"left": left, "top": top, "width": width, "height": height}

                # Capture the specified window
                self.img = sct.grab(self.monitor)
                self.img = np.array(self.img)

                self.img_mp = self.img[
                    self.top_left_mp[1]:self.bottom_right_mp[1],
                    self.top_left_mp[0]:self.bottom_right_mp[0]
                ]

                # Check MP
                current_time = time.time()
                if current_time - self.last_check_time_autopot >= self.check_interval_autopot:
                    self.check_mp(self.img_mp)
                    self.last_check_time_autopot = current_time

                # Initialize Screen
                if self.enable_cv_preview:
                    cv.imshow("MP", self.img_mp)

                cv.waitKey(1)

    def check_whiteroom(self, img_whiteroom):
        rgb_whiteroom = img_whiteroom[:, :, :3]  # Consider only the RGB channels
        # Target color Format = BGR (BlueGreenRed)
        target_color = np.array([255, 255, 255]) # White Room
        
        # Define a threshold for each channel
        channel_threshold = 0
        
        # Check if the difference between each channel is outside the threshold
        color_difference = np.abs(rgb_whiteroom - target_color)
        outside_threshold = np.any(color_difference > channel_threshold, axis=-1)
        
        if np.all(outside_threshold):
            p = 0  # just a placeholder
        else:
            self.play_audio_else()
            pydirectinput.press('home')

    def set_whiteroom_bar_coordinates(self):
        # Function to set whiteroom bar coordinates during runtime
        print("Current Value:")
        print("Top-Left - "+ str(self.top_left_whiteroom))
        print("Bottom-Right - "+ str(self.bottom_right_whiteroom))
        print("Enter the coordinates for the Top-Left point of the White Room (No Comma): ")
        top_left_input = input().split()
        self.top_left_whiteroom = (int(top_left_input[0]), int(top_left_input[1]))

        print("Enter the coordinates for the Bottom-Right point of the White Room (No Comma): ")
        bottom_right_input = input().split()
        self.bottom_right_whiteroom = (int(bottom_right_input[0]), int(bottom_right_input[1]))

        self.save_coordinates()

    def capture_screen_whiteroom(self):
        # Get the MapleStory window
        maplestory_window = gw.getWindowsWithTitle('MapleStory')  # Replace 'MapleStory' with the actual window title
        if not maplestory_window:
            print("MapleStory not found. Make sure the game is running.")
            return

        maplestory_window = maplestory_window[0]  # Assuming there's only one MapleStory window

        with mss.mss() as sct:
            while True:
                # Get the coordinates of the MapleStory window
                left, top, width, height = maplestory_window.left, maplestory_window.top, maplestory_window.width, maplestory_window.height
                self.monitor = {"left": left, "top": top, "width": width, "height": height}

                # Capture the specified window
                self.img = sct.grab(self.monitor)
                self.img = np.array(self.img)

                self.img_whiteroom = self.img[
                    self.top_left_whiteroom[1]:self.bottom_right_whiteroom[1],
                    self.top_left_whiteroom[0]:self.bottom_right_whiteroom[0]
                ]

                # Check whiteroom
                current_time = time.time()
                if current_time - self.last_check_time_whiteroom >= self.check_interval_whiteroom:
                    self.check_whiteroom(self.img_whiteroom)
                    self.last_check_time_whiteroom = current_time

                # Initialize Screen
                if self.enable_cv_preview:
                    cv.imshow("White Room", self.img_whiteroom)

                cv.waitKey(1)

    def check_eliteboss(self, img_eliteboss):
        rgb_eliteboss = img_eliteboss[:, :, :3]  # Consider only the RGB channels
        # Target color Format = BGR (BlueGreenRed)
        target_color = np.array([0, 34, 255]) # Elite Boss
        
        # Define a threshold for each channel
        channel_threshold = 0
        
        # Check if the difference between each channel is outside the threshold
        color_difference = np.abs(rgb_eliteboss - target_color)
        outside_threshold = np.any(color_difference > channel_threshold, axis=-1)
        
        if np.all(outside_threshold):
            p = 0  # just a placeholder
        else:
            self.play_audio_else()
            
    def set_eliteboss_bar_coordinates(self):
        # Function to set eliteboss bar coordinates during runtime
        print("Current Value:")
        print("Top-Left - "+ str(self.top_left_eliteboss))
        print("Bottom-Right - "+ str(self.bottom_right_eliteboss))
        print("Enter the coordinates for the Top-Left point of the Elite Boss (No Comma): ")
        top_left_input = input().split()
        self.top_left_eliteboss = (int(top_left_input[0]), int(top_left_input[1]))

        print("Enter the coordinates for the Bottom-Right point of the Elite Boss (No Comma): ")
        bottom_right_input = input().split()
        self.bottom_right_eliteboss = (int(bottom_right_input[0]), int(bottom_right_input[1]))

        self.save_coordinates()

    def capture_screen_eliteboss(self):
        # Get the MapleStory window
        maplestory_window = gw.getWindowsWithTitle('MapleStory')  # Replace 'MapleStory' with the actual window title
        if not maplestory_window:
            print("MapleStory not found. Make sure the game is running.")
            return

        maplestory_window = maplestory_window[0]  # Assuming there's only one MapleStory window

        with mss.mss() as sct:
            while True:
                # Get the coordinates of the MapleStory window
                left, top, width, height = maplestory_window.left, maplestory_window.top, maplestory_window.width, maplestory_window.height
                self.monitor = {"left": left, "top": top, "width": width, "height": height}

                # Capture the specified window
                self.img = sct.grab(self.monitor)
                self.img = np.array(self.img)

                self.img_eliteboss = self.img[
                    self.top_left_eliteboss[1]:self.bottom_right_eliteboss[1],
                    self.top_left_eliteboss[0]:self.bottom_right_eliteboss[0]
                ]

                # Check eliteboss
                current_time = time.time()
                if current_time - self.last_check_time >= self.check_interval:
                    self.check_eliteboss(self.img_eliteboss)
                    self.last_check_time = current_time

                # Initialize Screen
                if self.enable_cv_preview:
                    cv.imshow("Elite Boss", self.img_eliteboss)

                cv.waitKey(1)

    def check_minimap(self, img_minimap):
        rgb_minimap = img_minimap[:, :, :3]  # Consider only the RGB channels
        # Target color Format = BGR (BlueGreenRed)
        target_color1 = np.array([0, 0, 255]) # Player
        target_color2 = np.array([255, 102, 221]) # Rune
        #target_color1 = np.array([0, 0, 255]) # Player
        #target_color2 = np.array([0, 255, 0]) # NPC
        
        # Define a threshold for each channel
        channel_threshold = 0
        
        # Check if the difference between each channel is outside the threshold
        color_difference1 = np.abs(rgb_minimap - target_color1)
        outside_threshold1 = np.any(color_difference1 > channel_threshold, axis=-1)

        # Check if the difference between each channel is outside the threshold
        color_difference2 = np.abs(rgb_minimap - target_color2)
        outside_threshold2 = np.any(color_difference2 > channel_threshold, axis=-1)
        
        if not np.all(outside_threshold1):
            self.play_audio_else() # Player Alert
        elif not np.all(outside_threshold2):
            self.play_audio_rune() # Rune Alert (Also NPC Alert for Debugging)
        else:
            p = 0
            #pydirectinput.press('r')

    def set_minimap_bar_coordinates(self):
        # Function to set minimap bar coordinates during runtime
        print("Current Value:")
        print("Top-Left - "+ str(self.top_left_minimap))
        print("Bottom-Right - "+ str(self.bottom_right_minimap))
        print("Enter the coordinates for the Top-Left point of the Minimap (No Comma): ")
        top_left_input = input().split()
        self.top_left_minimap = (int(top_left_input[0]), int(top_left_input[1]))

        print("Enter the coordinates for the Bottom-Right point of the Minimap (No Comma): ")
        bottom_right_input = input().split()
        self.bottom_right_minimap = (int(bottom_right_input[0]), int(bottom_right_input[1]))

        self.save_coordinates()

    def capture_screen_minimap(self):
        # Get the MapleStory window
        maplestory_window = gw.getWindowsWithTitle('MapleStory')  # Replace 'MapleStory' with the actual window title
        if not maplestory_window:
            print("MapleStory not found. Make sure the game is running.")
            return

        maplestory_window = maplestory_window[0]  # Assuming there's only one MapleStory window

        with mss.mss() as sct:
            while True:
                # Get the coordinates of the MapleStory window
                left, top, width, height = maplestory_window.left, maplestory_window.top, maplestory_window.width, maplestory_window.height
                self.monitor = {"left": left, "top": top, "width": width, "height": height}

                # Capture the specified window
                self.img = sct.grab(self.monitor)
                self.img = np.array(self.img)

                self.img_minimap = self.img[
                    self.top_left_minimap[1]:self.bottom_right_minimap[1],
                    self.top_left_minimap[0]:self.bottom_right_minimap[0]
                ]

                # Check Minimap
                current_time = time.time()
                if current_time - self.last_check_time >= self.check_interval:
                    self.check_minimap(self.img_minimap)
                    self.last_check_time = current_time

                # Initialize Screen
                if self.enable_cv_preview:
                    cv.imshow("Minimap", self.img_minimap)

                cv.waitKey(1)

def main():
    hp_process = None
    mp_process = None
    minimap_process = None
    eliteboss_process = None
    whiteroom_process = None
    #chat_process = None
    while True:
        print("MapleStory Bot by witchhunted\n")
        print("Q - Record")
        print("W - Playback")
        print("1 - Toggle Auto HP Pot")
        print("2 - Toggle Auto MP Pot")
        print("3 - Toggle White Room Alert (Force stop playback)")
        print("4 - Toggle Elite Boss Alert")
        print("5 - Toggle Minimap Alert: Players & Runes & White Room")
        print("6 - Resize")
        print("R - Quit\n")

        choice = input("Enter your choice: ")

        if choice == "q" or choice == "Q":
            clear_console()
            record_actions()
        elif choice == "w" or choice == "W":
            clear_console()
            play_actions()
        elif choice == "1":
            if hp_process is None or not hp_process.is_alive():
                hp_process = multiprocessing.Process(
                    target=screen_agent.capture_screen_hp,
                    args=(),
                    name="HP")
                hp_process.start()
                clear_console()
                print("Auto HP Pot - On")
                sleep(1)
                clear_console()
            else:
                clear_console()
                print("Auto HP Pot - Off")
                sleep(1)
                hp_process.terminate()
                clear_console()
        elif choice == "2":
            if mp_process is None or not mp_process.is_alive():
                mp_process = multiprocessing.Process(
                    target=screen_agent.capture_screen_mp,
                    args=(),
                    name="MP")
                mp_process.start()
                clear_console()
                print("Auto MP Pot - On")
                sleep(1)
                clear_console()
            else:
                clear_console()
                print("Auto MP Pot - Off")
                sleep(1)
                mp_process.terminate()
                clear_console()
        elif choice == "3":
            if whiteroom_process is None or not whiteroom_process.is_alive():
                whiteroom_process = multiprocessing.Process(
                    target=screen_agent.capture_screen_whiteroom,
                    args=(),
                    name="White Room")
                whiteroom_process.start()
                clear_console()
                print("White Room Alert - On")
                sleep(1)
                clear_console()
            else:
                clear_console()
                print("White Room Alert - Off")
                sleep(1)
                whiteroom_process.terminate()
                clear_console()
        elif choice == "4":
            if eliteboss_process is None or not eliteboss_process.is_alive():
                eliteboss_process = multiprocessing.Process(
                    target=screen_agent.capture_screen_eliteboss,
                    args=(),
                    name="Elite Boss")
                eliteboss_process.start()
                clear_console()
                print("Elite Boss Alert - On")
                sleep(1)
                clear_console()
            else:
                clear_console()
                print("Elite Boss Alert - Off")
                sleep(1)
                eliteboss_process.terminate()
                clear_console()
        elif choice == "5":
            if minimap_process is None or not minimap_process.is_alive():
                minimap_process = multiprocessing.Process(
                    target=screen_agent.capture_screen_minimap,
                    args=(),
                    name="Minimap")
                minimap_process.start()
                clear_console()
                print("Minimap Alert - On")
                sleep(1)
                clear_console()
            else:
                clear_console()
                print("Minimap Alert - Off")
                sleep(1)
                minimap_process.terminate()
                clear_console()
        elif choice == "6":
            while True:
                clear_console()
                print("Resize - Initialize any screen you want to resize first and run mousepos.py to grab correct coordination.\n")
                print("Q - Run mousepos.py (Recommended)")
                print("1 - HP")
                print("2 - MP")
                print("3 - White Room")
                print("4 - Elite Boss")
                print("5 - Minimap")
                print("R - Back\n")
                choice = input("Enter your choice: ")
                if choice == "q" or choice == "Q":
                    if platform.system() == "Windows":
                        subprocess.run(["start", "cmd", "/c", "python", "assets/script/mousepos.py"], shell=True)
                    elif platform.system() == "Linux":
                        subprocess.run(["x-terminal-emulator", "-e", "python", "mousepos.py"])
                    else:
                        print("Unsupported platform")
                elif choice == "1":
                    if hp_process is None or not hp_process.is_alive():
                        clear_console()
                        print("Auto HP Pot is currently not running, run it first.")
                        sleep(1.5)
                        clear_console()
                    else:
                        clear_console()
                        screen_agent.set_hp_bar_coordinates()  # Allow user to set HP bar coordinates
                        hp_process.terminate()
                        clear_console()
                        hp_process = multiprocessing.Process(
                            target=screen_agent.capture_screen_hp,
                            args=(),
                            name="HP"
                        )
                        hp_process.start()
                        clear_console()
                elif choice == "2":
                    if mp_process is None or not mp_process.is_alive():
                        clear_console()
                        print("Auto MP Pot is currently not running, run it first.")
                        sleep(1.5)
                        clear_console()
                    else:
                        clear_console()
                        screen_agent.set_mp_bar_coordinates()  # Allow user to set MP bar coordinates
                        mp_process.terminate()
                        clear_console()
                        mp_process = multiprocessing.Process(
                            target=screen_agent.capture_screen_mp,
                            args=(),
                            name="MP"
                        )
                        mp_process.start()
                        clear_console()
                elif choice == "3":
                    if whiteroom_process is None or not whiteroom_process.is_alive():
                        clear_console()
                        print("White Room Alert is currently not running, run it first.")
                        sleep(1.5)
                        clear_console()
                    else:
                        clear_console()
                        screen_agent.set_whiteroom_bar_coordinates()  # Allow user to set whiteroom bar coordinates
                        whiteroom_process.terminate()
                        clear_console()
                        whiteroom_process = multiprocessing.Process(
                            target=screen_agent.capture_screen_whiteroom,
                            args=(),
                            name="White Room"
                        )
                        whiteroom_process.start()
                        clear_console()
                elif choice == "4":
                    if eliteboss_process is None or not eliteboss_process.is_alive():
                        clear_console()
                        print("Elite Boss Alert is currently not running, run it first.")
                        sleep(1.5)
                        clear_console()
                    else:
                        clear_console()
                        screen_agent.set_eliteboss_bar_coordinates()  # Allow user to set eliteboss bar coordinates
                        eliteboss_process.terminate()
                        clear_console()
                        eliteboss_process = multiprocessing.Process(
                            target=screen_agent.capture_screen_eliteboss,
                            args=(),
                            name="Elite Boss"
                        )
                        eliteboss_process.start()
                        clear_console()
                elif choice == "5":
                    if minimap_process is None or not minimap_process.is_alive():
                        clear_console()
                        print("Minimap Alert is currently not running, run it first.")
                        sleep(1.5)
                        clear_console()
                    else:
                        clear_console()
                        screen_agent.set_minimap_bar_coordinates()  # Allow user to set minimap bar coordinates
                        minimap_process.terminate()
                        clear_console()
                        minimap_process = multiprocessing.Process(
                            target=screen_agent.capture_screen_minimap,
                            args=(),
                            name="Minimap"
                        )
                        minimap_process.start()
                        clear_console()
                elif choice == "r" or choice == "R":
                    clear_console()
                    break
                else:
                    clear_console()
                    print("Invalid choice.")
                    sleep(1.5)
                    clear_console()
        #elif choice == "6":
        #    print("placeholder")
        elif choice == "r" or choice == "R" :
            if hp_process is not None:
                hp_process.terminate()
            if mp_process is not None:
                mp_process.terminate()
            if minimap_process is not None:
                minimap_process.terminate()
            if eliteboss_process is not None:
                eliteboss_process.terminate()                
            if whiteroom_process is not None:
                whiteroom_process.terminate()            
            # if chat_process is not None:
            #     chat_process.terminate()
            break
        else:
            clear_console()
            print("Invalid choice.")
            sleep(1.5)
            clear_console()

if __name__ == "__main__":
    screen_agent = ScreenCaptureAgent()
    main()