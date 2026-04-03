# Jarvis

Jarvis is a beginner-friendly AI personal assistant built with Python for Windows. It supports both voice and text commands, can open apps and websites, remembers simple user facts, and performs practical desktop actions.

## Features

- Voice input using `SpeechRecognition`
- Text-to-speech responses using `pyttsx3`
- Typed input fallback when voice is unavailable
- Open installed applications such as VS Code, Chrome, Notepad, and more
- Open websites such as YouTube, Google, GitHub, and custom URLs
- Google search commands such as `Search AI projects`
- Open files and folders
- Close running applications
- JSON-based memory for facts like `My name is Sujal`
- Beginner-friendly modular Python structure

## Folder Structure

```text
JARVIS/
|-- data/
|   `-- memory.json
|-- jarvis/
|   |-- __init__.py
|   |-- assistant.py
|   |-- intent_parser.py
|   |-- memory.py
|   |-- system_control.py
|   `-- voice.py
|-- main.py
|-- README.md
`-- requirements.txt
```

## How It Works

- `voice.py` handles speech recognition and text-to-speech.
- `system_control.py` opens apps, websites, folders, files, and closes apps.
- `memory.py` saves and retrieves user details from `data/memory.json`.
- `intent_parser.py` extracts intent from natural language commands.
- `assistant.py` connects everything into a working assistant loop.
- `main.py` starts the application.

## Setup Instructions

1. Install Python 3.10 or newer on Windows.
2. Open Command Prompt or PowerShell in this project folder.
3. Create a virtual environment:

```powershell
python -m venv .venv
```

4. Activate the virtual environment:

```powershell
.venv\Scripts\activate
```

5. Install dependencies:

```powershell
pip install -r requirements.txt
```

6. If `PyAudio` fails to install, try:

```powershell
pip install pipwin
pipwin install pyaudio
```

7. Run the assistant:

```powershell
python main.py
```

## Notes About Voice Input

- Voice recognition uses Google's recognizer through the `SpeechRecognition` package.
- You need a working microphone.
- You also need an internet connection for speech-to-text.
- If voice is unavailable, Jarvis still works in text mode.
- If you installed a newer `SpeechRecognition` version manually and voice stops working, run `pip install -r requirements.txt` to restore the tested version.
- On Python 3.12, `setuptools` is also required because `SpeechRecognition 3.8.1` still expects the old `distutils` module during microphone setup.

## Example Commands

- `Open VS Code`
- `Can you open Chrome?`
- `Please open Google`
- `Open YouTube`
- `Open github.com`
- `Search AI projects`
- `Open downloads folder`
- `Open C:\Users\YourName\Documents`
- `Close Notepad`
- `My name is Sujal`
- `What is my name?`
- `Forget my name`
- `Hello`
- `Exit`

## How App Opening Works

Jarvis tries the following in order:

1. Known app shortcuts such as VS Code, Chrome, Edge, Notepad, and PowerShell.
2. Executables available in your system `PATH`.
3. Start Menu shortcut search for installed applications.

This makes commands like `Open VS Code` and `Open Chrome` practical on Windows.

## Future Improvements

- Add offline speech recognition
- Add reminders and to-do items
- Add music controls
- Add weather and news integration
- Add OpenAI or local LLM chat support
