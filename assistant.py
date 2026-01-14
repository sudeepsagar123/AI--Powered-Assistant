import os
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

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

class Jarvis:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.voices = self.engine.getProperty('voices')
        # Try to select a more human-like voice
        try:
            self.engine.setProperty('voice', self.voices[1].id)
        except:
            self.engine.setProperty('voice', self.voices[0].id)
        
        self.engine.setProperty('rate', 175)
        self.recognizer = sr.Recognizer()
        # Increase recognition timeout
        self.recognizer.operation_timeout = 5  # 5 seconds max for recognition

    def speak(self, text):
        """Converts text to speech."""
        print(f"Jarvis: {text}")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except:
            pass  # Continue even if speech fails

    def listen(self):
        """Listens to the microphone and returns the recognized text."""
        print("\nListening...")
        fs = 16000
        seconds = 4
        
        try:
            # Play beep
            import winsound
            winsound.Beep(1000, 200)
            
            print("🎤 Speak now!")
            myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
            sd.wait()
            
            # Check audio level
            max_level = np.max(np.abs(myrecording))
            if max_level < 100:
                print("⚠️ No audio detected.")
                return None
            
            write('temp_audio.wav', fs, myrecording)
            
            print("🔍 Recognizing...")
            with sr.AudioFile('temp_audio.wav') as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self.recognizer.record(source)
                
                try:
                    command = self.recognizer.recognize_google(audio, language='en-US')
                    print(f"✅ You said: {command}")
                    return command.lower()
                except sr.UnknownValueError:
                    print("❌ Could not understand. Please speak clearly.")
                    return None
                except sr.RequestError:
                    print("❌ Network error. Check internet connection.")
                    return None
                except Exception as e:
                    print(f"❌ Error: {str(e)[:50]}")
                    return None
                    
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"❌ Listen error: {str(e)[:50]}")
            return None

    def think(self, prompt):
        """Uses OpenAI to generate responses."""
        if not openai.api_key or openai.api_key == "your_api_key_here":
            return "I need an OpenAI API key. Please set it in the .env file."
        
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are Jarvis, a helpful AI assistant. Be concise and friendly."},
                    {"role": "user", "content": prompt}
                ],
                timeout=10
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"I encountered an error: Check your API key and internet connection."

    def open_application(self, app_name):
        """Opens Windows applications."""
        app_map = {
            'word': ['WINWORD.EXE', r'C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE'],
            'excel': ['EXCEL.EXE', r'C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE'],
            'powerpoint': ['POWERPNT.EXE', r'C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE'],
            'chrome': ['chrome.exe'],
            'firefox': ['firefox.exe'],
            'edge': ['msedge.exe'],
            'notepad': ['notepad.exe'],
            'calculator': ['calc.exe'],
            'paint': ['mspaint.exe'],
            'cmd': ['cmd.exe'],
            'powershell': ['powershell.exe'],
            'explorer': ['explorer.exe'],
        }
        
        app_name_lower = app_name.lower()
        
        for key, executables in app_map.items():
            if key in app_name_lower:
                for exe in executables:
                    try:
                        subprocess.Popen([exe])
                        return True
                    except:
                        continue
        
        try:
            subprocess.Popen(['start', app_name], shell=True)
            return True
        except:
            return False

    def execute_command(self, command):
        """Executes user commands."""
        if not command:
            return

        print(f"📝 Processing: {command}")

        # Websites
        if "youtube" in command and "open" in command:
            self.speak("Opening YouTube")
            webbrowser.open("https://www.youtube.com")
        
        elif "google" in command and "open" in command:
            self.speak("Opening Google")
            webbrowser.open("https://www.google.com")
        
        elif "gmail" in command or ("mail" in command and "open" in command):
            self.speak("Opening Gmail")
            webbrowser.open("https://mail.google.com")
        
        elif "search" in command:
            query = command.replace("search", "").replace("for", "").strip()
            self.speak(f"Searching for {query}")
            webbrowser.open(f"https://www.google.com/search?q={query}")

        # Applications
        elif "open" in command:
            app_name = command.replace("open", "").strip()
            self.speak(f"Opening {app_name}")
            if not self.open_application(app_name):
                self.speak(f"Sorry, couldn't find {app_name}")

        # System commands
        elif "time" in command:
            time_str = datetime.datetime.now().strftime("%I:%M %p")
            self.speak(f"It's {time_str}")
        
        elif "date" in command or "today" in command:
            date_str = datetime.datetime.now().strftime("%B %d, %Y")
            self.speak(f"Today is {date_str}")

        elif "screenshot" in command:
            self.speak("Taking screenshot")
            screenshot = pyautogui.screenshot()
            filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            screenshot.save(filename)
            self.speak("Screenshot saved")

        elif "minimize" in command or "hide" in command:
            self.speak("Minimizing windows")
            pyautogui.hotkey('win', 'd')

        elif "volume up" in command or "increase volume" in command:
            self.speak("Increasing volume")
            for _ in range(5):
                pyautogui.press('volumeup')
        
        elif "volume down" in command or "decrease volume" in command:
            self.speak("Decreasing volume")
            for _ in range(5):
                pyautogui.press('volumedown')
        
        elif "mute" in command:
            self.speak("Toggling mute")
            pyautogui.press('volumemute')
        
        elif "lock" in command:
            self.speak("Locking computer")
            subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'])

        elif "exit" in command or "quit" in command or "goodbye" in command or "stop" in command:
            self.speak("Goodbye!")
            exit()
        
        else:
            # Ask AI
            response = self.think(command)
            self.speak(response)

    def run(self):
        """Main loop."""
        self.speak("Hello, how can I help?")
        
        while True:
            try:
                command = self.listen()
                if command:
                    self.execute_command(command)
            except KeyboardInterrupt:
                self.speak("Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                continue

if __name__ == "__main__":
    print("="*50)
    print("JARVIS AI ASSISTANT")
    print("="*50)
    print("Say commands after the beep!")
    print("Try: 'open google', 'what time', 'take screenshot'")
    print("Say 'exit' to quit")
    print("="*50)
    
    app = Jarvis()
    app.run()
