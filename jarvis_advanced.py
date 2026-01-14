import os
import threading
import speech_recognition as sr
import pyttsx3
import openai
import webbrowser
import subprocess
import datetime
import pyautogui
from dotenv import load_dotenv
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import tkinter as tk
from tkinter import Canvas
from PIL import Image, ImageTk
import time
import requests
import winreg
import psutil
from bs4 import BeautifulSoup
import pyperclip
import wikipediaapi
import json
from newsapi import NewsApiClient

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

class AdvancedJarvis:
    def __init__(self):
        # Voice engine
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        try:
            self.engine.setProperty('voice', voices[1].id)
        except:
            self.engine.setProperty('voice', voices[0].id)
        self.engine.setProperty('rate', 175)
        
        # Speech recognizer
        self.recognizer = sr.Recognizer()
        self.recognizer.operation_timeout = 5
        
        # GUI
        self.root = None
        self.canvas = None
        self.status_text = None
        self.message_text = None
        self.pulse_circle = None
        self.activated = False
        self.running = True
        
        # Build application database on startup
        self.installed_apps = self.scan_installed_apps()
        
    def scan_installed_apps(self):
        """Comprehensive scan of ALL system applications"""
        print("🔍 Scanning entire system for applications...")
        apps = {}
        
        # Critical paths to scan
        paths_to_scan = [
            r"C:\Program Files",
            r"C:\Program Files (x86)",
            r"C:\Windows\System32",
            os.path.expanduser(r"~\AppData\Local"),
            os.path.expanduser(r"~\AppData\Roaming"),
        ]
        
        # Common executable names to find
        exe_to_find = set()
        
        print("  Scanning common locations...")
        # Quick scan first - find all .exe files (up to 2 levels deep for speed)
        for base_path in paths_to_scan:
            if not os.path.exists(base_path):
                continue
            
            try:
                # Scan up to 3 levels deep
                for root, dirs, files in os.walk(base_path):
                    # Limit depth for speed
                    depth = root[len(base_path):].count(os.sep)
                    if depth > 2:
                        dirs[:] = []  # Don't go deeper
                        continue
                    
                    for file in files:
                        if file.lower().endswith('.exe'):
                            full_path = os.path.join(root, file)
                            # Extract app name (remove .exe and common suffixes)
                            app_name = file[:-4].lower()
                            app_name = app_name.replace('_', ' ').replace('-', ' ')
                            
                            # Store with simple name as key
                            if app_name not in apps or len(full_path) < len(apps[app_name]):
                                apps[app_name] = full_path
                                
            except (PermissionError, OSError):
                continue
        
        print(f"✅ Found {len(apps)} applications!")
        print(f"  (Use 'what apps' to see installed apps)")
        return apps
    
    def find_app(self, app_name):
        """Smart app finder - searches installed apps"""
        app_name = app_name.lower().strip()
        
        # Direct match
        if app_name in self.installed_apps:
            return self.installed_apps[app_name]
        
        # Partial match - find best match
        matches = []
        for name, path in self.installed_apps.items():
            if app_name in name or name in app_name:
                matches.append((name, path))
        
        if matches:
            # Return first match
            return matches[0][1]
        
        # Search by keywords
        keywords = app_name.split()
        for keyword in keywords:
            if len(keyword) > 2:  # Ignore short words
                for name, path in self.installed_apps.items():
                    if keyword in name:
                        return path
        
        return None
        
    def create_gui(self):
        """Create the GUI"""
        self.root = tk.Tk()
        self.root.title("JARVIS AI Assistant")
        
        # Window settings
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.95)
        self.root.overrideredirect(True)
        
        # Center on screen
        width, height = 400, 500
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Canvas
        self.canvas = Canvas(self.root, width=width, height=height, bg='#0a0a1a', highlightthickness=0)
        self.canvas.pack()
        
        # Logo
        try:
            logo = Image.open("jarvis_logo.png")
            logo = logo.resize((250, 250), Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(logo)
            self.canvas.create_image(200, 150, image=self.logo_img)
        except:
            self.canvas.create_oval(75, 25, 325, 275, fill='#00ffff', outline='#00ffff', width=3)
        
        # Status text
        self.status_text = self.canvas.create_text(200, 320, text="STANDBY", 
                                                    font=('Arial', 14, 'bold'), fill='#ffaa00')
        
        # Message text
        self.message_text = self.canvas.create_text(200, 360, text="Say 'Hey Assistant' to activate", 
                                                     font=('Arial', 12), fill='#ffffff', width=350)
        
        # Pulse circle
        self.pulse_circle = self.canvas.create_oval(180, 400, 220, 440, fill='', outline='#00ff00', width=3)
        self.canvas.itemconfig(self.pulse_circle, state='hidden')
        
        # Close button
        close_btn = tk.Button(self.root, text="×", command=self.close_app, 
                             bg='#ff0000', fg='white', font=('Arial', 16, 'bold'),
                             relief=tk.FLAT)
        close_btn.place(x=370, y=5, width=25, height=25)
        
        # Start voice processing in separate thread
        self.voice_thread = threading.Thread(target=self.voice_loop, daemon=True)
        self.voice_thread.start()
        
    def update_status(self, text, color="#00ffff"):
        """Update status"""
        if self.canvas and self.status_text:
            self.canvas.itemconfig(self.status_text, text=text, fill=color)
            self.root.update()
    
    def update_message(self, text):
        """Update message"""
        if self.canvas and self.message_text:
            self.canvas.itemconfig(self.message_text, text=text)
            self.root.update()
    
    def show_listening(self):
        """Show listening state"""
        if self.canvas and self.pulse_circle:
            self.canvas.itemconfig(self.pulse_circle, state='normal')
            self.update_status("LISTENING", "#00ff00")
    
    def hide_listening(self):
        """Hide listening state"""
        if self.canvas and self.pulse_circle:
            self.canvas.itemconfig(self.pulse_circle, state='hidden')
    
    def show_activated(self):
        """Show activation"""
        self.update_status("ACTIVATED", "#00ff00")
        self.update_message("Hello Boss, how can I help you?")
        # Flash animation
        for _ in range(3):
            self.root.attributes('-alpha', 0.5)
            self.root.update()
            time.sleep(0.1)
            self.root.attributes('-alpha', 0.95)
            self.root.update()
            time.sleep(0.1)
    
    def speak(self, text):
        """Speak text"""
        print(f"Jarvis: {text}")
        self.update_message(text)
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except:
            pass
    
    def listen_wake_word(self):
        """Listen for wake word"""
        fs, seconds = 16000, 3
        try:
            myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
            sd.wait()
            
            if np.max(np.abs(myrecording)) < 50:
                return False
            
            write('temp_audio.wav', fs, myrecording)
            
            with sr.AudioFile('temp_audio.wav') as source:
                audio = self.recognizer.record(source)
                try:
                    text = self.recognizer.recognize_google(audio, language='en-US').lower()
                    print(f"Heard: {text}")
                    return "hey assistant" in text or "hey jarvis" in text
                except:
                    return False
        except:
            return False
    
    def listen_command(self):
        """Listen for command"""
        self.show_listening()
        print("🎤 Listening for command...")
        
        fs, seconds = 16000, 5
        try:
            import winsound
            winsound.Beep(1000, 200)
            
            myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
            sd.wait()
            
            self.hide_listening()
            self.update_status("PROCESSING", "#ffaa00")
            
            if np.max(np.abs(myrecording)) < 100:
                return None
            
            write('temp_audio.wav', fs, myrecording)
            
            with sr.AudioFile('temp_audio.wav') as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self.recognizer.record(source)
                
                try:
                    command = self.recognizer.recognize_google(audio, language='en-US')
                    print(f"✅ You said: {command}")
                    return command.lower()
                except:
                    return None
        except:
            return None
    
    def open_website(self, name):
        """Smart website opener"""
        name = name.lower().strip().replace("open ", "").replace("website", "").replace("site", "").strip()
        
        print(f"🔍 Searching for: {name}")
        
        known_sites = {
            'google': 'https://www.google.com', 'youtube': 'https://www.youtube.com',
            'facebook': 'https://www.facebook.com', 'twitter': 'https://www.twitter.com',
            'x': 'https://www.x.com', 'instagram': 'https://www.instagram.com',
            'linkedin': 'https://www.linkedin.com', 'github': 'https://www.github.com',
            'gmail': 'https://mail.google.com', 'whatsapp': 'https://web.whatsapp.com',
            'reddit': 'https://www.reddit.com', 'amazon': 'https://www.amazon.com',
            'netflix': 'https://www.netflix.com', 'spotify': 'https://www.spotify.com',
            'pinterest': 'https://www.pinterest.com', 'tiktok': 'https://www.tiktok.com',
        }
        
        if name in known_sites:
            print(f"✅ Found: {known_sites[name]}")
            webbrowser.open(known_sites[name])
            return True
        
        for tld in ['.com', '.net', '.org', '.io']:
            try:
                url = f"https://www.{name}{tld}"
                response = requests.head(url, timeout=2, allow_redirects=True)
                if response.status_code < 400:
                    print(f"✅ Found: {url}")
                    webbrowser.open(url)
                    return True
            except:
                continue
        
        print(f"🌐 Using Google to find {name}...")
        webbrowser.open(f"https://www.google.com/search?q={name}&btnI=1")
        return True
    
    
    def open_application(self, app_name):
        """Smart application launcher - finds and opens ANY installed app"""
        app_name_original = app_name
        app_name = app_name.lower().strip()
        
        print(f"🔍 Looking for application: {app_name}")
        
        # Use smart finder
        app_path = self.find_app(app_name)
        
        if app_path:
            print(f"✅ Found: {app_path}")
            
            # Try multiple launch methods
            # Method 1: Direct execution
            try:
                subprocess.Popen([app_path], shell=False)
                return True
            except Exception as e1:
                print(f"  Method 1 failed: {e1}")
                
                # Method 2: Shell execution
                try:
                    subprocess.Popen([app_path], shell=True)
                    return True
                except Exception as e2:
                    print(f"  Method 2 failed: {e2}")
                    
                    # Method 3: Use start command (best for WindowsApps)
                    try:
                        os.startfile(app_path)
                        return True
                    except Exception as e3:
                        print(f"  Method 3 failed: {e3}")
                        
                        # Method 4: Explorer shell
                        try:
                            subprocess.run(['explorer', app_path])
                            return True
                        except:
                            pass
        
        # Fallback: Try built-in Windows commands
        built_in = {
            'word': 'WINWORD.EXE', 'excel': 'EXCEL.EXE', 'powerpoint': 'POWERPNT.EXE',
            'chrome': 'chrome.exe', 'edge': 'msedge.exe', 'notepad': 'notepad.exe',
            'calculator': 'calc.exe', 'paint': 'mspaint.exe', 'cmd': 'cmd.exe',
            'powershell': 'powershell.exe', 'explorer': 'explorer.exe',
            'file manager': 'explorer.exe', 'task manager': 'taskmgr.exe',
        }
        
        for name, exe in built_in.items():
            if name in app_name:
                try:
                    subprocess.Popen([exe])
                    return True
                except:
                    pass
        
        # Final fallback: Try Windows start command
        try:
            subprocess.Popen(['start', '', app_name_original], shell=True)
            return True
        except:
            return False
    
    def execute_command(self, command):
        """Execute command with advanced system control"""
        if not command:
            return
        
        print(f"📝 Processing: {command}")
        
        # SMART COMMAND HANDLING
        # Handle complex phrases like "go for google and search of chatgpt and open"
        clean_cmd = command.lower()
        if ("search" in clean_cmd or "google" in clean_cmd) and "open" in clean_cmd:
            # The user likely wants to open the result directly
            target = clean_cmd.replace("go for", "").replace("google", "").replace("search", "").replace("and", "").replace("open", "").replace("for", "").replace("of", "").replace("the", "").strip()
            if target:
                self.speak(f"Opening {target}")
                self.open_website(target)
                return

        # List installed applications
        if "what apps" in command or "list apps" in command or "installed applications" in command:
            count = len(self.installed_apps)
            self.speak(f"I found {count} installed applications. Some examples are:")
            # List first 10 apps
            for i, (name, path) in enumerate(list(self.installed_apps.items())[:10]):
                print(f"  {i+1}. {name}")
            self.speak("Check console for full list")
            return
        
        # File system navigation
        elif "go to" in command and "drive" in command:
            # Extract drive letter
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                if f"{letter} drive" in command or f"{letter}:" in command:
                    self.speak(f"Opening {letter} drive")
                    subprocess.Popen(['explorer', f'{letter}:\\'])
                    return
        
        # Create folder
        elif "create folder" in command or "new folder" in command:
            folder_name = command.replace("create folder", "").replace("new folder", "").replace("called", "").replace("named", "").strip()
            if folder_name:
                self.speak(f"Creating folder {folder_name}")
                # Create on desktop by default
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                folder_path = os.path.join(desktop, folder_name)
                try:
                    os.makedirs(folder_path, exist_ok=True)
                    self.speak(f"Folder created on desktop")
                    subprocess.Popen(['explorer', desktop])
                except Exception as e:
                    self.speak("Could not create folder")
            else:
                self.speak("Opening file explorer")
                subprocess.Popen(['explorer.exe'])
        
        # Website/Application opening
        elif "open" in command:
            target = command.replace("open", "").strip()
            if not target:
                return
            
            # Check if it's a built-in command first
            if "file manager" in target or "explorer" in target:
                self.speak("Opening File Manager")
                subprocess.Popen(['explorer.exe'])
                return
            
            # Extract first word/phrase as target
            words = target.split()
            if words:
                target_name = ' '.join(words[:2]) if len(words) > 1 else words[0]
                
                # Try as application first
                if self.open_application(target_name):
                    self.speak(f"Opening {target_name}")
                else:
                    # Try as website
                    self.speak(f"Opening {target_name}")
                    self.open_website(target_name)
        
        # Web search
        elif "search" in command:
            query = command.replace("search", "").replace("for", "").strip()
            self.speak(f"Searching for {query}")
            webbrowser.open(f"https://www.google.com/search?q={query}")
        
        # Time and date
        elif "time" in command:
            self.speak(f"It's {datetime.datetime.now().strftime('%I:%M %p')}")
        
        elif "date" in command or "today" in command:
            self.speak(f"Today is {datetime.datetime.now().strftime('%B %d, %Y')}")
        
        # Screenshot
        elif "screenshot" in command or "capture" in command:
            self.speak("Taking screenshot")
            screenshot = pyautogui.screenshot()
            filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            screenshot.save(filename)
            self.speak("Screenshot saved")
        
        # Volume
        elif "volume up" in command or "increase volume" in command:
            self.speak("Increasing volume")
            for _ in range(5):
                pyautogui.press('volumeup')
        
        elif "volume down" in command or "decrease volume" in command:
            self.speak("Decreasing volume")
            for _ in range(5):
                pyautogui.press('volumedown')
        
        elif "mute" in command or "unmute" in command:
            self.speak("Toggling mute")
            pyautogui.press('volumemute')
        
        # Window management
        elif "minimize" in command or "hide windows" in command:
            self.speak("Minimizing all windows")
            pyautogui.hotkey('win', 'd')
        
        elif "maximize" in command or "restore" in command:
            self.speak("Restoring windows")
            pyautogui.hotkey('win', 'd')
        
        # System power
        elif "lock" in command:
            self.speak("Locking computer")
            subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'])
        
        elif "sleep" in command:
            self.speak("Putting computer to sleep")
            subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0', '1', '0'])
        
        elif "shutdown" in command:
            self.speak("Shutting down in 10 seconds")
            subprocess.run(['shutdown', '/s', '/t', '10'])
        
        # Download Image
        elif "download" in command and "image" in command:
            self.download_image(command)
            
        elif "restart" in command:
            self.speak("Restarting in 10 seconds")
            subprocess.run(['shutdown', '/r', '/t', '10'])
            

        
        # ADVANCED FEATURES
        
        # System Statistics
        elif "system status" in command or "system stats" in command or "performance" in command:
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            self.speak(f"CPU usage is {cpu} percent. Memory usage is {memory} percent. Disk usage is {disk} percent.")
        
        elif "battery" in command:
            try:
                battery = psutil.sensors_battery()
                if battery:
                    percent = battery.percent
                    plugged = "plugged in" if battery.power_plugged else "on battery"
                    self.speak(f"Battery is at {percent} percent and {plugged}")
                else:
                    self.speak("No battery detected")
            except:
                self.speak("Could not get battery information")
        
        # Clipboard Operations
        elif "copy" in command and "clipboard" in command:
            text = command.replace("copy", "").replace("clipboard", "").replace("to", "").strip()
            if text:
                pyperclip.copy(text)
                self.speak(f"Copied to clipboard")
        
        elif "paste" in command or "what's in clipboard" in command:
            text = pyperclip.paste()
            if text:
                self.speak(f"Clipboard contains: {text[:100]}")
            else:
                self.speak("Clipboard is empty")
        
        # Calculator
        elif "calculate" in command or "what is" in command and any(op in command for op in ['+', '-', '*', '/', 'plus', 'minus', 'times', 'divided']):
            try:
                # Extract math expression
                expr = command.replace("calculate", "").replace("what is", "").strip()
                expr = expr.replace("plus", "+").replace("minus", "-").replace("times", "*").replace("multiplied by", "*")
                expr = expr.replace("divided by", "/").replace("equals", "")
                result = eval(expr)
                self.speak(f"The answer is {result}")
            except:
                self.speak("Could not calculate that")
        
        # Wikipedia Search
        elif "wikipedia" in command or "wiki" in command:
            query = command.replace("wikipedia", "").replace("wiki", "").replace("search", "").replace("about", "").strip()
            if query:
                try:
                    wiki = wikipediaapi.Wikipedia('en')
                    page = wiki.page(query)
                    if page.exists():
                        summary = page.summary[:200]
                        self.speak(f"According to Wikipedia: {summary}")
                    else:
                        self.speak(f"Could not find information about {query}")
                except:
                    self.speak("Wikipedia search failed")
        
        # Type Text
        elif "type" in command:
            text = command.replace("type", "").strip()
            if text:
                self.speak(f"Typing {text}")
                time.sleep(1)
                pyautogui.typewrite(text, interval=0.1)
        
        # File Operations
        elif "open file" in command:
            self.speak("Opening file explorer")
            subprocess.Popen(['explorer.exe'])
        
        elif "delete file" in command:
            self.speak("Please use file explorer to delete files safely")
        
        # Window Switching
        elif "switch window" in command or "next window" in command:
            self.speak("Switching window")
            pyautogui.hotkey('alt', 'tab')
        
        elif "close window" in command or "close this" in command:
            self.speak("Closing window")
            pyautogui.hotkey('alt', 'f4')
        
        # Browser Tab Operations
        elif "new tab" in command:
            self.speak("Opening new tab")
            pyautogui.hotkey('ctrl', 't')
        
        elif "close tab" in command:
            self.speak("Closing tab")
            pyautogui.hotkey('ctrl', 'w')
        
        elif "refresh" in command or "reload" in command:
            self.speak("Refreshing page")
            pyautogui.press('f5')
        
        # Email (opens default email client)
        elif "send email" in command or "compose email" in command:
            self.speak("Opening email client")
            webbrowser.open('mailto:')
        
        # Music Control
        elif "play music" in command or "pause music" in command or "play pause" in command:
            self.speak("Toggling play pause")
            pyautogui.press('playpause')
        
        elif "next song" in command or "next track" in command:
            self.speak("Next track")
            pyautogui.press('nexttrack')
        
        elif "previous song" in command or "previous track" in command:
            self.speak("Previous track")
            pyautogui.press('prevtrack')
        
        # Brightness (if supported)
        elif "brightness up" in command or "increase brightness" in command:
            self.speak("Increasing brightness")
            for _ in range(5):
                pyautogui.press('brightness_up')
        
        elif "brightness down" in command or "decrease brightness" in command:
            self.speak("Decreasing brightness")
            for _ in range(5):
                pyautogui.press('brightness_down')
        
        # Read News
        elif "news" in command or "headlines" in command:
            self.speak("Here are the top headlines")
            # Simple news without API
            webbrowser.open("https://news.google.com")
        
        # Weather
        elif "weather" in command:
            location = command.replace("weather", "").replace("in", "").replace("at", "").strip()
            if not location:
                location = "current location"
            self.speak(f"Opening weather for {location}")
            webbrowser.open(f"https://www.google.com/search?q=weather+{location}")
        
        # Take Notes
        elif "take note" in command or "make note" in command or "note" in command:
            note_text = command.replace("take note", "").replace("make note", "").replace("note", "").strip()
            if note_text:
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                note_file = os.path.join(desktop, f"note_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                with open(note_file, 'w') as f:
                    f.write(note_text)
                self.speak("Note saved on desktop")
        
        # Read Text from Screen (OCR simulation - opens snipping tool)
        elif "read screen" in command or "read text" in command:
            self.speak("Opening snipping tool")
            subprocess.Popen(['SnippingTool.exe'])
        
        # Timer
        elif "timer" in command and ("minute" in command or "second" in command):
            try:
                import re
                numbers = re.findall(r'\d+', command)
                if numbers:
                    duration = int(numbers[0])
                    unit = "minutes" if "minute" in command else "seconds"
                    self.speak(f"Setting timer for {duration} {unit}")
                    # Simple timer notification
                    if "minute" in command:
                        duration *= 60
                    threading.Thread(target=lambda: (time.sleep(duration), self.speak("Timer finished!"))).start()
            except:
                self.speak("Could not set timer")
        
        # Fun Commands
        elif "tell me a joke" in command or "joke" in command:
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything!",
                "Why did the programmer quit? Because he didn't get arrays!",
                "What's an astronaut's favorite key? The space bar!",
                "Why do programmers prefer dark mode? Because light attracts bugs!",
            ]
            import random
            self.speak(random.choice(jokes))
        
        elif "flip a coin" in command or "coin flip" in command:
            import random
            result = random.choice(["Heads", "Tails"])
            self.speak(f"The coin landed on {result}")
        
        elif "roll dice" in command or "roll a die" in command:
            import random
            result = random.randint(1, 6)
            self.speak(f"The dice rolled {result}")
        
        # AI Conversation
        elif "smart mode" in command or "ai mode" in command:
            query = command.replace("smart mode", "").replace("ai mode", "").strip()
            if query:
                response = self.think_ai(query)
                self.speak(response)
        
        # CONVERSATION & COMPLIMENTS
        elif "good" in command or "great" in command or "nice" in command or "amazing" in command or "awesome" in command:
            if "morning" in command:
                self.speak("Good morning boss!")
            elif "afternoon" in command:
                self.speak("Good afternoon boss!")
            elif "evening" in command:
                self.speak("Good evening boss!")
            elif "night" in command:
                self.speak("Good night boss, sweet dreams!")
            else:
                responses = [
                    "Thank you boss! I try my best.",
                    "I'm glad you like my service, boss.",
                    "Always happy to help!",
                    "You're too kind, boss!",
                    "At your service, boss!"
                ]
                import random
                self.speak(random.choice(responses))
        
        elif "thank" in command:
            self.speak("You're welcome boss!")
            
        elif "hello" in command or "hi" in command or "hey" in command:
            self.speak("Hello boss! I'm ready for your commands.")
            
        elif "how are you" in command:
            self.speak("I'm functioning at 100% efficiency and ready to help you!")
            
        elif "who are you" in command or "what are you" in command:
            self.speak("I am Jarvis, your personal AI assistant. I can control your system, find information, and help you with daily tasks.")
            
        elif "what is your name" in command:
            self.speak("My name is Jarvis.")
            
        # Help
        elif "help" in command or "what can you do" in command:
            self.speak("I have advanced capabilities! I can control your system, check performance, use clipboard, search Wikipedia, do calculations, type text, control music, show weather and news, set timers, take notes, download images, and much more. Just ask!")
        
        else:
            # Fallback for unknown commands - try to be more polite
            self.speak("I didn't quite catch that. Could you please repeat?")
    
    def think_ai(self, query):
        """Use OpenAI for advanced conversational AI"""
        if not openai.api_key or openai.api_key == "your_api_key_here":
            return "AI features require an OpenAI API key"
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are Jarvis, an advanced AI assistant. Be helpful, concise, and intelligent."},
                    {"role": "user", "content": query}
                ],
                timeout=10
            )
            return response.choices[0].message.content
        except:
            return "AI processing failed"
    
    def download_image(self, command):
        """Download image from Google Images"""
        try:
            # Extract query - Remove common command words to get the actual search term
            remove_words = [
                "google", "search", "find", "download", "get", "fetch",
                "image", "images", "picture", "pictures", "photo", "photos", "pic", "pics", "wallpaper", "wallpapers",
                "of", "for", "about", "and", "a", "an", "the"
            ]
            
            query = command
            for word in remove_words:
                # Replace whole words only to avoid damaging the query
                query = query.replace(f" {word} ", " ").replace(f"{word} ", " ").replace(f" {word}", " ")
            
            # Clean up
            query = query.strip()
            
            # If query became empty (e.g. just "download image"), ask user
            if not query:
                self.speak("What should I download an image of?")
                return

            self.speak(f"Downloading {query}")
            
            # Create directory on Desktop
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            download_folder = os.path.join(desktop, "Jarvis_Downloads")
            os.makedirs(download_folder, exist_ok=True)
            
            # Search Google Images
            url = f"https://www.google.com/search?q={query}&tbm=isch"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find image URLs (looking for gstatic which are the thumbnails in search results)
            img_tags = soup.find_all('img')
            img_url = None
            
            for img in img_tags:
                src = img.get('src')
                if src and src.startswith('http') and 'gstatic.com' in src:
                    img_url = src
                    break
            
            if not img_url:
                # Try finding any http image if gstatic fails
                for img in img_tags:
                    src = img.get('src')
                    if src and src.startswith('http') and 'google' not in src:
                        img_url = src
                        break

            if img_url:
                # Download
                img_data = requests.get(img_url).content
                filename = f"{query.replace(' ', '_')}_{int(time.time())}.jpg"
                file_path = os.path.join(download_folder, filename)
                
                with open(file_path, 'wb') as f:
                    f.write(img_data)
                
                self.speak(f"Downloaded {query} image to Jarvis Downloads folder on Desktop")
                # Open the image
                os.startfile(file_path)
            else:
                self.speak("Sorry, I couldn't find an image to download.")
                
        except Exception as e:
            print(f"Error downloading image: {e}")
            self.speak("I encountered an error while downloading the image.")

    def voice_loop(self):
        """Voice processing loop - runs forever"""
        print("="*60)
        print("JARVIS - Say 'Hey Assistant' ONCE to activate")
        print("="*60)
        
        while self.running:
            try:
                if not self.activated:
                    if self.listen_wake_word():
                        self.show_activated()
                        self.speak("Hello boss, how can I help you?")
                        self.activated = True
                        self.update_status("READY", "#00ff00")
                        print("✅ ACTIVATED - Ready for commands!")
                else:
                    print("\n⏳ Ready for your command...")
                    self.update_status("READY", "#00ff00")
                    self.update_message("Waiting for your command...")
                    
                    command = self.listen_command()
                    if command:
                        if "goodbye" in command or "exit" in command or "quit" in command:
                            self.speak("Goodbye boss!")
                            time.sleep(1)
                            self.close_app()
                            break
                        else:
                            self.execute_command(command)
                            print("✅ Command completed! Ready for next command...")
                            self.update_status("READY", "#00ff00")
                            self.update_message("Ready for your next command...")
                            time.sleep(0.5)
                    else:
                        print("❌ No command detected, listening again...")
                        
            except KeyboardInterrupt:
                print("\n⚠️ Keyboard interrupt detected")
                break
            except Exception as e:
                print(f"⚠️ Error: {e}")
                time.sleep(0.5)
                continue
    
    def close_app(self):
        """Close application safely"""
        self.running = False
        try:
            if self.root:
                self.root.after(100, self.root.destroy)
        except:
            pass
    
    def run(self):
        """Run the application"""
        try:
            self.create_gui()
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.close_app()
        except Exception as e:
            print(f"Application error: {e}")
        finally:
            self.running = False

if __name__ == "__main__":
    app = AdvancedJarvis()
    app.run()
