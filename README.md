# SpotPress

**SpotPress** is a modern, cross-platform presentation tool written in Python.
It provides a spotlight/laser pointer overlay for live presentations, supporting multiple display setups and advanced features like pen drawing, magnifier, and full device integration.

**_ Notice: currently only works on Linux with X11 interface backend _**

---

## ✨ Features

- 🌟 **Spotlight** and **Laser Pointer** modes
- 🖍️ **Pen drawing** overlay on slides or screen
- 🔍 **Magnifying Glass** mode
- 🖥️ Multi-monitor support
- ⚙️ Graphical preferences window (via system tray)
- 🎮 Integration with presenter remote controls (e.g. Baseus, VR Box)
- 🧹 Modular device detection (Linux & Windows)
- 🛠️ Command-line control with `spotpressctl`
- 📆 Works with PyQt5 or PyQt6

---

## 💻 Dependencies

### On Debian/Ubuntu-based systems:

#### If PyQt6 is available:

```bash
sudo apt install pyqt6-dev pyqt6-dev-tools python3-pyudev python3-evdev python3-uinput
```

#### Or if using PyQt5:

```bash
sudo apt install pyqt5-dev pyqt5-dev-tools python3-pyudev python3-evdev python3-uinput
```

You may also need `libuinput-dev` for some systems.

---

## 🚀 Running SpotPress

To start the main application:

```bash
python3 main.py
```

It will run in the background with a system tray icon. From there, you can open the preferences window, configure devices, and manage overlay modes.

---

## 🧠 Command-Line Tool

The `spotpressctl` utility allows controlling the running instance from the command line:

### Usage:

```bash
spotpressctl [command]
```

### Available commands:

| Command               | Description                                                           |
| --------------------- | --------------------------------------------------------------------- |
| `--start`             | Starts SpotPress if not already running                               |
| `--show-window`       | Opens the configuration window                                        |
| `--hide-window`       | Hides the configuration window                                        |
| `--quit`              | Terminates the SpotPress process                                      |
| `--set-mode=<MODE>`   | Sets mode: `mouse`, `spotlight`, `laser`, `pen`, `mag_glass` or `0-4` |
| `--set-auto-mode=on`  | Enables automatic device-based switching                              |
| `--set-auto-mode=off` | Disables automatic mode switching                                     |

Example:

```bash
spotpressctl --set-mode=spotlight
```

---

## 🛠 Development

### Install dependencies via `pip` (optional):

```bash
pip install -r requirements.txt
```

Or for development:

```bash
pip install -e .
```

### Run from source:

```bash
python3 main.py
```

### To create a command line on system

```
sudo ln -s /path/to/spotpressctl.py /usr/local/bin/spotpressctl
```

---

## 📁 Project Structure

- `main.py` – Entry point to launch the application
- `spotpressctl.py` – Command-line controller
- `spotpress/` – Core source code
- `spotpress/ui/` – UI components and tabs
- `spotpress/hw/` – Device detection backends
- `spotpress/qtcompat.py` – Qt compatibility wrapper
- `README.md` – This file

---

## 📦 Packaging (optional)

You can package this into a `.deb`, `.exe`, or `.AppImage` using tools like `PyInstaller` or `fpm`.

---

## 📝 License

This project is licensed under the **LGPL License**.

---

## 👨‍💻 Author

**Alexandre da Silva**
Contact: <lexrupy>

Contributions are welcome via pull requests or issue reports.
