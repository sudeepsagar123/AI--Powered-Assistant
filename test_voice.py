import pyttsx3

# Test TTS
engine = pyttsx3.init()
voices = engine.getProperty('voices')

print("Available voices:")
for i, voice in enumerate(voices):
    print(f"{i}: {voice.name}")

# Test speaking
engine.setProperty('rate', 175)
try:
    engine.setProperty('voice', voices[1].id)
except:
    engine.setProperty('voice', voices[0].id)

print("\nTesting voice output...")
engine.say("Hello, I am Jarvis. Your AI assistant is online and ready to help you.")
engine.runAndWait()

print("If you heard my voice, the text-to-speech is working correctly!")
