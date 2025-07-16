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

    # Cria o servidor para receber comandos externos

    app = QApplication(sys.argv)
    app.setApplicationName("SpotPress")
    app.setWindowIcon(QIcon(ICON_FILE))
    load_dark_theme(app)

    window = SpotpressPreferences()

    window._ipc_server = setup_ipc_server(window.handle_command_from_ipc)
    if server is None:
        print("SpotPress já está rodando.")
        sys.exit(0)

    window.show()

    sys.exit(app.exec())
