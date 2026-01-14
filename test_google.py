import webbrowser

print("Testing 'open google' command...")
command = "open google"

if "open google" in command:
    print("✅ Command matched!")
    print("Opening Google in browser...")
    webbrowser.open("https://www.google.com")
    print("✅ Google should be opening now!")
else:
    print("❌ Command did not match")
