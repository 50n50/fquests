# FQuests

Automated tool to fulfill Discord Activity Quest requirements by fetching detectable game definitions, compiling a dummy windowed executable, running it for 15 minutes, and cleaning up created files.

## Features

- Fetches and caches game metadata from `https://discord.com/api/v9/applications/detectable`.
- Compiles a native Win32 windowed executable via `.NET` `csc.exe` to trigger Discord overlay and quest heartbeats.
- Supports nested executable relative paths (e.g. `_retail_\wow.exe`).
- Runs a 15-minute timer with real-time status, auto-minimize window option, and manual cancel support.
- Automatically kills the process and deletes temporary executables and empty folders on exit or cancel.
- Includes GUI and CLI interfaces.

## Requirements

- Windows 10 / 11
- Python 3.8+
- Discord Desktop Client

Optional UI dependencies:
```bash
pip install customtkinter Pillow win10toast
```

## Usage

Option 1: Double-click `run.bat` in File Explorer.

Option 2: Run GUI via Python:
```bash
python main.py
```

Option 3: Run CLI:
```bash
python main.py --cli
```

Refresh application cache:
```bash
python main.py --refresh
```

## Quest Troubleshooting

1. Accept the quest in Discord (`User Settings` > `Gift Inventory / Quests`) before starting.
2. Ensure `User Settings` > `Data & Privacy` > `In-game Rewards (aka Quests)` is enabled.
3. If the quest is a Stream Quest, join a Discord voice channel, click Share Screen, and stream the generated game window for 15 minutes.
4. If progress does not update immediately, reload the Discord client (`Ctrl + R`).
