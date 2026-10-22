# Auto Text Typer for Mac

Type text sentences with keyboard shortcuts on your Mac. Configure shortcuts, save them to reusable config files, and control typing speed — all from a clean dashboard UI.

![Auto Text Typer](https://img.shields.io/badge/platform-macOS-lightgrey) ![Python](https://img.shields.io/badge/python-3.8%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green)

## Features

- **Keyboard Shortcuts** — Assign any modifier+key combo (Ctrl+Shift+1, Cmd+Shift+A, etc.) to auto-type a block of text
- **Dashboard UI** — Browser-based config panel to add, edit, delete, and toggle shortcuts
- **Configurable Speed** — Adjust key press duration and per-character delay with sliders
- **Save & Load Configs** — Export/import JSON config files to reuse or share your setup
- **Global Hotkeys** — Shortcuts work in any app while the server is running
- **Auto-Save** — Config saves automatically to `~/.autotyper/config.json`
- **Dark Mode** — UI follows your system theme

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/auto-text-typer-mac.git
cd auto-text-typer-mac
```

### 2. Set up the environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run it

```bash
./run.sh
```

Or manually:

```bash
source .venv/bin/activate
python3 auto_text_typer.py
```

The dashboard opens automatically at [http://127.0.0.1:8787](http://127.0.0.1:8787).

## Usage

### Adding a Shortcut

1. Click **+ Add Shortcut** in the dashboard
2. Click **"Click to record shortcut"** and press your key combo (e.g. `Ctrl+Shift+1`)
3. Give it a label and enter the text to type
4. Click **Save**

Now press `Ctrl+Shift+1` in any app — the text types itself automatically.

### Controls

| Action | How |
|--------|-----|
| Add shortcut | Click **+ Add Shortcut** in dashboard |
| Edit shortcut | Click the pencil icon on any entry |
| Delete shortcut | Click the X icon on any entry |
| Enable/disable one | Toggle the checkbox on any entry |
| Pause all | Click the **Active** pill in the header |
| Adjust speed | Move the sliders in **Typing Speed** |
| Export config | Click **Export Config** to download JSON |
| Import config | Click **Import Config** to load a JSON file |

### Speed Settings

| Setting | What it does | Range |
|---------|-------------|-------|
| Key Press Duration | Time each key is held down | 1–100 ms |
| Delay Between Characters | Pause between each character typed | 1–500 ms |

## macOS Accessibility Permission

The first time you run it, macOS will require Accessibility access for your terminal app.

**System Settings → Privacy & Security → Accessibility** → Enable your terminal (Terminal.app, iTerm2, VS Code, etc.)

This is required for global hotkey detection and simulated key presses.

## Config File

Configs auto-save to `~/.autotyper/config.json`. You can also export/import configs through the UI.

Example config:

```json
{
  "entries": [
    {
      "id": "abc-123",
      "shortcut": "<ctrl>+<shift>+1",
      "text": "Hello, this is auto-typed!",
      "label": "Greeting",
      "enabled": true
    }
  ],
  "settings": {
    "key_delay_ms": 10,
    "char_delay_ms": 30
  }
}
```

## Project Structure

```
auto-text-typer-mac/
├── auto_text_typer.py   # Backend: server, hotkey listener, typing engine
├── ui.html              # Dashboard: browser-based config UI
├── run.sh               # One-click launcher
├── requirements.txt     # Python dependencies
├── LICENSE              # MIT License
└── README.md
```

## Requirements

- macOS 10.15+
- Python 3.8+
- Accessibility permissions enabled

## License

MIT — see [LICENSE](LICENSE).
