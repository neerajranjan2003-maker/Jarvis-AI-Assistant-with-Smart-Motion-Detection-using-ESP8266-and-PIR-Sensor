import sys
import os
import webbrowser
import re
import datetime
import requests
import speedtest
import pyautogui
import pyttsx3
from time import sleep
import random
import pywhatkit as kt
import threading
import speech_recognition as sr
import time
import subprocess
import pygame
import numpy as np
import wikipedia
import psutil
import GPUtil
import platform
import json 
from queue import Queue

speech_queue = Queue()

# Initialize pygame for sound effects
pygame.mixer.init()

# Sound files
startup_sound = "C:/Users/email/Desktop/Jarvis1/startup.mp3"
listening_sound = "C:/Users/email/Desktop/Jarvis1/iron-man-repulsor.mp3"

# Global variables
sleep_mode = False
name = None
door_state = "unlocked"   # default
ESP_IP = "http://10.139.224.224/"   # 🔴 replace with your IP

def control_esp(endpoint):
    try:
        url = f"{ESP_IP}/{endpoint}"
        requests.get(url, timeout=2)
        print(f"Sent request: {url}")
    except Exception as e:
        print("ESP Error:", e)
        TTS("Sir, I am unable to connect to the device.")

def play_sound(sound_file, volume=0.5):
    """Play a sound effect at a specified volume."""
    try:
        pygame.mixer.music.load(sound_file)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play()
        time.sleep(0.1)
    except Exception as e:
        print(f"Sound Error: {e}")

# Initialize TTS
engine = pyttsx3.init()
engine.setProperty('rate', 140)
engine.setProperty('volume', 1.0)

# Select Mark voice if available
voices = engine.getProperty('voices')
for voice in voices:
    if "mark" in voice.name.lower():
        engine.setProperty('voice', voice.id)
        print(f"✅ Using voice: {voice.name}")
        break

def TTS(text):
    """Text to Speech function"""
    engine.say(text)
    engine.runAndWait()

def improved_STT():
    """
    Improved Speech-to-Text with better performance and less lag
    """
    global sleep_mode
    r = sr.Recognizer()
    
    # Optimize for faster recognition
    r.energy_threshold = 3500  # Adjust based on your environment
    r.dynamic_energy_threshold = True
    r.dynamic_energy_adjustment_damping = 0.18
    r.dynamic_energy_ratio = 1.5
    r.pause_threshold = 0.8  # Reduced for faster response
    r.phrase_threshold = 0.3
    r.non_speaking_duration = 0.8
    
    with sr.Microphone() as source:
        # Quick ambient noise adjustment
        r.adjust_for_ambient_noise(source, duration=0.5)
        
        while True:
            if sleep_mode:
                listen_for_wake_command()
                continue
            
            try:
                # Play listening sound
                play_sound(listening_sound, volume=0.3)
                
                # Listen with shorter timeout for better responsiveness
                print("Listening...")
                audio = r.listen(source, timeout=5, phrase_time_limit=8)
                
                print("Processing speech...")
                text = r.recognize_google(audio, language="en-IN").lower()
                print(f"You said: {text}")
                
                if "jarvis go to sleep" in text:
                    sleep_mode = True
                    TTS("Going to sleep mode. Say Jarvis wake up to activate me.")
                    listen_for_wake_command()
                    continue
                
                return text
                
            except sr.WaitTimeoutError:
                continue  # No speech detected, keep listening
            except sr.UnknownValueError:
                continue  # Could not understand, keep listening
            except sr.RequestError:
                TTS("I'm having trouble connecting to the speech service.")
                continue
            except Exception as e:
                print(f"Error: {e}")
                continue

def listen_for_wake_command():
    """Listen for wake word while in sleep mode"""
    global sleep_mode
    r = sr.Recognizer()
    r.energy_threshold = 3500
    r.dynamic_energy_threshold = True
    r.pause_threshold = 0.8
    
    with sr.Microphone() as source:
        TTS("Enjoy your time, sir.")
        
        while sleep_mode:
            try:
                audio = r.listen(source, timeout=1, phrase_time_limit=3)
                text = r.recognize_google(audio, language="en-IN").lower()
                
                if "jarvis wake up" in text:
                    print("At your service, sir")
                    TTS("At your service, sir")
                    sleep_mode = False
                    return
                    
            except (sr.WaitTimeoutError, sr.UnknownValueError):
                continue
            except sr.RequestError:
                continue
def get_battery_status():
    """Get and speak battery status"""
    battery = psutil.sensors_battery()
    if battery is None:
        TTS("Sir, I couldn't retrieve battery information.")
        return
    
    percent = battery.percent
    is_plugged = battery.power_plugged
    
    if percent <= 20 and not is_plugged:
        TTS(f"Warning! Battery is critically low at {percent} percent. Please connect the charger immediately.")
    else:
        status = "charging" if is_plugged else "on battery"
        TTS(f"Sir, battery is at {percent} percent and the laptop is {status}.")

def get_system_info():
    """Get and speak system information"""
    cpu_usage = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    total_ram = round(ram.total / (1024**3), 2)
    available_ram = round(ram.available / (1024**3), 2)
    
    message = f"Sir, CPU usage is {cpu_usage} percent. "
    message += f"Total RAM is {total_ram} gigabytes, with {available_ram} gigabytes available."
    
    print(message)
    TTS(message)

def check_internet_speed():
    """Check internet speed"""
    try:
        TTS("Checking your internet speed, please wait.")
        st = speedtest.Speedtest()
        st.get_best_server()
        download_speed = round(st.download() / 1_000_000, 2)
        upload_speed = round(st.upload() / 1_000_000, 2)
        
        TTS(f"Download speed is {download_speed} megabits per second, and upload speed is {upload_speed} megabits per second.")
    except Exception as e:
        print(f"Error testing internet speed: {e}")
        TTS("Sorry sir, I couldn't check the internet speed due to a network issue.")
def monitor_motion():
    last_motion = False
    last_announcement_time = 0  # Track when we last announced
    COOLDOWN_SECONDS = 30 # Don't announce again within 10 seconds

    while True:
        try:
            response = requests.get(
                f"{ESP_IP}/motion",
                timeout=1
            )

            motion = response.text.strip() == "1"
            current_time = time.time()

            if motion and not last_motion:
                # Motion just started (transition from False to True)
                print("🚨 Motion Detected!")
                
                # Only add to queue if enough time has passed since last announcement
                if current_time - last_announcement_time >= COOLDOWN_SECONDS:
                    speech_queue.put("Sir, motion has been detected near the door.")
                    last_announcement_time = current_time
                else:
                    print(f"Motion detected but waiting {COOLDOWN_SECONDS}s cooldown")

            last_motion = motion

        except Exception as e:
            print("Motion Monitor Error:", e)

        time.sleep(1)
def play_favourite_song():
    """Play a random favourite song"""
    TTS("Playing your favourite song, sir")
    
    song_links = {
        1: "https://www.youtube.com/watch?v=_51KXfwcPMs",
        2: "https://www.youtube.com/watch?v=pHu4PLhuKgQ",
        3: "https://www.youtube.com/watch?v=1gqBb4Y7LJA",
        4: "https://www.youtube.com/watch?v=D49nMgP7Vzc",
        5: "https://www.youtube.com/watch?v=nEnLt3pasxE"
    }
    
    random_song = random.choice(list(song_links.values()))
    webbrowser.open(random_song)    
                
            

# Keep all your existing command functions (play_favourite_song, get_battery_status, etc.)
# I'll show the modified handle_commands function without GPT/localhost:

def handle_commands(text):
    """
    Handle all local commands without GPT or localhost dependencies
    """
    text = text.lower()
    
    # Wikipedia search
    if "wikipedia" in text:
        text = text.replace("wikipedia", "")
        text = text.replace("who is", "")
        text = text.replace("what is", "")
        try:
            result = wikipedia.summary(text, sentences=2)
            TTS(result)
        except:
            TTS("I couldn't find information on that topic.")
        return True

    # Play music on YouTube
    if "play" in text:
        text = text.replace("play", "").strip()
        text = text.replace("music", "").strip()
        if text:
            kt.playonyt(text)
            TTS(f"Playing {text} on YouTube, sir")
        else:
            play_favourite_song()
        return True
    
    # Time
    if "time" in text:
        strtime = datetime.datetime.now().strftime("%I:%M %p")
        TTS(f"The current time is {strtime}")
        return True
    
    # YouTube search
    if "youtube" in text:
        text = text.replace("search", "").replace("youtube", "").strip()
        webbrowser.open(f"https://www.youtube.com/results?search_query={text}")
        TTS(f"Showing YouTube results for {text}")
        return True
    
    # Google search
    if "search" in text:
        text = text.replace("search", "").replace("on google", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={text}")
        TTS(f"Searching Google for {text}")
        return True
    # ===== LAMP CONTROL =====
    if "lamp on" in text or "turn on lamp" in text:
       control_esp("onoff")
       TTS("Turning on the lamp, sir")
       return True

    if "lamp off" in text or "turn off lamp" in text:
        control_esp("onoff")
        TTS("Turning off the lamp, sir")
        return True

    if "increase brightness" in text:
         control_esp("brightup")
         TTS("Increasing brightness")
         return True

    if "decrease brightness" in text:
        control_esp("brightdown")
        TTS("Decreasing brightness")
        return True

    if "change colour" in text:
        control_esp("color")
        TTS("Changing color")
        return True
    
    # Favourite song
    if "favourite song" in text:
        play_favourite_song()
        return True
    
    # Browser tab controls
    if "close tab" in text:
        pyautogui.hotkey("ctrl", "w")
        TTS("Tab closed, sir")
        return True
    
    if "close all tabs" in text or "close two tabs" in text:
        pyautogui.hotkey("ctrl", "w")
        sleep(0.3)
        pyautogui.hotkey("ctrl", "w")
        TTS("Tabs closed, sir")
        return True
    
    # Window controls
    if "close the window" in text:
        pyautogui.hotkey("alt", "f4")
        TTS("Closing window, sir")
        return True
    
    if "switch tab" in text:
        pyautogui.hotkey("alt", "tab")
        TTS("Switching tab, sir")
        return True
    
    # Media controls
    if "stop" in text:
        pyautogui.press("space")
        return True
    if "forward" in text:
        pyautogui.press("l")
        sleep(0.5)
        pyautogui.press("l")
        sleep(0.5)
        pyautogui.press("l")
        sleep(0.5)
        pyautogui.press("l")
        sleep(0.5)
        return True
    if "backward" in text:
        pyautogui.press("j")
        sleep(0.5)
        pyautogui.press("j")
        sleep(0.5)
        pyautogui.press("j")
        sleep(0.5)
        pyautogui.press("j")
        sleep(0.5)
        return True
    
    if "full screen" in text:
        pyautogui.press("f")
        return True
    
    if "next song" in text or "next track" in text:
        pyautogui.hotkey("shift", "n")
        TTS("Playing next song")
        return True
    
    if "previous song" in text or "previous track" in text:
        pyautogui.hotkey("shift", "p")
        TTS("Playing previous song")
        return True
    global door_state

# ===== LOCK DOOR =====
    if "lock" in text:
        if door_state == "locked":
            TTS("Sir, the door is already locked")
        else:
            control_esp("lock")
            door_state = "locked"
            TTS("Locking the door, sir")
        return True


    
    # Volume controls
    if "mute" in text:
        pyautogui.press("volumemute")
        TTS("Muted")
        return True
    
    if "increase volume" in text:
        for _ in range(10):
            pyautogui.press("volumeup")
            sleep(0.05)
        TTS("Volume increased")
        return True
    
    if "decrease volume" in text or "volume down" in text:
        for _ in range(10):
            pyautogui.press("volumedown")
            sleep(0.05)
        TTS("Volume decreased")
        return True
    
    # Window management
    if "minimise all" in text or "show desktop" in text:
        pyautogui.hotkey("win", "d")
        TTS("Minimized all windows")
        return True
    
    if "minimise" in text and "window" in text:
        pyautogui.hotkey("win", "down")
        TTS("Window minimized")
        return True
    
    # Open applications
    if "open" in text:
        app_name = text.replace("open", "").strip()
        pyautogui.press("win")
        sleep(0.3)
        pyautogui.write(app_name)
        sleep(0.3)
        pyautogui.press("enter")
        TTS(f"Opening {app_name}")
        return True
    
    # System information
    if "battery" in text:
        get_battery_status()
        return True
    
    if "system info" in text or "system information" in text:
        get_system_info()
        return True
    
    # Internet speed
    if "internet speed" in text or "speed test" in text:
        check_internet_speed()
        return True
    
    # Greetings and conversation
    if "hello" in text or "hi" in text:
        TTS("Hello sir, how can I help you?")
        return True
    
    if "who are you" in text or "what are you" in text:
        TTS("I am Jarvis, your personal assistant. I'm here to help you with various tasks.")
        return True
    
    if "how are you" in text:
        TTS("I'm functioning perfectly, sir. Thank you for asking.")
        return True
    
    if "thank you" in text or "thanks" in text:
        TTS("You're welcome, sir.")
        return True
    
    # System control
    if "restart" in text and ("computer" in text or "system" in text):
        TTS("Are you sure you want to restart?")
        confirmation = improved_STT()
        if "yes" in confirmation or "ok" in confirmation:
            TTS("Restarting system now, sir.")
            sleep(2)
            os.system("shutdown /r /t 0")
        else:
            TTS("Restart cancelled")
        return True
    
    if "shutdown" in text:
        TTS("Are you sure you want to shut down?")
        confirmation = improved_STT()
        if "yes" in confirmation or "ok" in confirmation:
            TTS("Shutting down now, sir.")
            sleep(2)
            os.system("shutdown /s /t 0")
        else:
            TTS("Shutdown cancelled")
        return True
    
    if "log off" in text or "sign out" in text:
        TTS("Are you sure you want to log off?")
        confirmation = improved_STT()
        if "yes" in confirmation or "ok" in confirmation:
            TTS("Logging off, sir.")
            sleep(2)
            os.system("shutdown /l")
        else:
            TTS("Log off cancelled")
        return True
    
    # Calculator functionality
    if "calculate" in text:
        try:
            calc_text = text.replace("calculate", "").strip()
            calc_text = calc_text.replace("plus", "+")
            calc_text = calc_text.replace("minus", "-")
            calc_text = calc_text.replace("multiply", "*")
            calc_text = calc_text.replace("divide", "/")
            result = eval(calc_text)
            TTS(f"The answer is {result}")
        except:
            TTS("I couldn't calculate that")
        return True
    
    # If no command was matched, provide help
    # if text:
    #     TTS("I'm not sure how to help with that. You can ask me to search, play music, check system info, or control your computer.")
    #     return True
    
    return False



if __name__ == "__main__":
    # Play startup sound
    try:
        play_sound(startup_sound)
        sleep(4)
    except:
        pass
    
    # TTS("I am Jarvis, sir. I am here to assist with a variety of tasks.")
    
    # ✅ START THE MOTION MONITORING THREAD
    motion_thread = threading.Thread(target=monitor_motion, daemon=True)
    motion_thread.start()
    print("✅ Motion monitoring started")
    
    while True:
        try:
            while not speech_queue.empty():
                TTS(speech_queue.get())
    
            text = improved_STT()
    
            if text:
                handle_commands(text)
    
        except Exception as e:
            print(f"Main loop error: {e}")