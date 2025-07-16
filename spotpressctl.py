#!/usr/bin/env python3
import sys
import subprocess
import os
from spotpress.ipc import send_command_to_existing_instance
from spotpress.utils import MODES_CMD_LINE_MAP

VALID_BASE_COMMANDS = {
    "--show-window",
    "--hide-window",
    "--quit",
    "--set-auto-mode=on",
    "--set-auto-mode=off",
    "--start",
}


def print_usage():
    print("Usage: spotpressctl [command]")
    print("Available commands:")
    print("  --start                 Start SpotPress if not already running")
    print("  --show-window           Show the SpotPress main window")
    print("  --hide-window           Hide the SpotPress main window")
    print("  --quit                  Quit SpotPress")
    print(
        "  --set-mode=MODE         Set mode to one of: mouse, spotlight, laser, pen, mag_glass or 0-4"
    )
    print("  --set-auto-mode=on|off  Enable or disable automatic mode switching")
    sys.exit(1)


def is_valid_command(command):
    if command in VALID_BASE_COMMANDS:
        return True
    if command.startswith("--set-mode="):
        mode = command.split("=", 1)[1].strip().lower()
        return mode in MODES_CMD_LINE_MAP
    return False


def launch_spotpress():
    try:
        base_dir = os.path.dirname(os.path.realpath(__file__))
        main_script = os.path.join(base_dir, "main.py")

        if not os.path.exists(main_script):
            print("Cannot find main.py. Please check your installation.")
            return False

        subprocess.Popen(
            [sys.executable, main_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("SpotPress launched in the background.")
        return True
    except Exception as e:
        print(f"Failed to launch SpotPress: {e}")
        return False


def main():
    if len(sys.argv) <= 1:
        print_usage()

    command = " ".join(sys.argv[1:]).strip()

    if not is_valid_command(command):
        print(f"Unknown or invalid command: {command}\n")
        print_usage()

    if command == "--start":
        if send_command_to_existing_instance("--ping"):
            print("SpotPress is already running.")
            sys.exit(0)
        else:
            success = launch_spotpress()
            sys.exit(0 if success else 1)

    if send_command_to_existing_instance(command):
        sys.exit(0)
    else:
        print("SpotPress is not running. Use spotpressctl --start to run SpotPress")
        sys.exit(1)


if __name__ == "__main__":
    main()
