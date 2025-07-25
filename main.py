#!/usr/bin/env python3
import sys
from spotpress.qtcompat import QApplication, QIcon
from spotpress.ipc import send_command_to_existing_instance, setup_ipc_server
from spotpress.utils import load_dark_theme
from spotpress.ui.preferences_window import (
    SpotpressPreferences,
    ICON_FILE,
)


if __name__ == "__main__":
    # Envia comando se outra instância estiver ativa
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
        if send_command_to_existing_instance(command):
            sys.exit(0)

    debug_mode = False
    if "--debug" in sys.argv:
        print("[DEBUG] Running in debug mode...")
        debug_mode = True

    app = QApplication(sys.argv)
    app.setApplicationName("SpotPress")
    app.setWindowIcon(QIcon(ICON_FILE))
    load_dark_theme(app)

    window = SpotpressPreferences(debug_mode)

    window.ipc_server = setup_ipc_server(  # pyright: ignore
        window.handle_command_from_ipc
    )
    if window.ipc_server is None:
        print("Spotpress is already running...")
        sys.exit(0)

    window.show()

    sys.exit(app.exec())
