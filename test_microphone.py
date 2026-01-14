import sounddevice as sd
import numpy as np

print("Testing microphone...")
print("Available audio devices:")
print(sd.query_devices())

print("\nDefault input device:")
print(sd.query_devices(kind='input'))

print("\nRecording 3 seconds of audio to test microphone...")
fs = 44100
duration = 3
myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
sd.wait()

print(f"Recording complete!")
print(f"Audio level (max): {np.max(np.abs(myrecording))}")

if np.max(np.abs(myrecording)) < 0.01:
    print("⚠️ WARNING: Very low audio detected! Check your microphone:")
    print("   - Is it plugged in?")
    print("   - Is it set as default recording device in Windows?")
    print("   - Is it muted?")
else:
    print("✅ Microphone is working!")
