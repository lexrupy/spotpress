#!/usr/bin/env python3
import sys
import os
import configparser
from spotpress.qtcompat import (
    SP_QT_VERSION,
    QApplication,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
    QSystemTrayIcon_Trigger,
    QWidget,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMainWindow,
    QIcon,
    QAction,
    Qt_Key_S,
    Qt_WindowMinimizeButtonHint,
    QtItem_UserRole,
    pyqtSignal,
    QTimer,
    QPixmap,
)

from spotpress.appcontext import AppContext
from spotpress.spotlight import SpotlightOverlayWindow
from spotpress.infoverlay import InfOverlayWindow
from spotpress.utils import (
    MODES_CMD_LINE_MAP,
    get_screen_geometry,
    ICON_FILE,
    CONFIG_PATH,
)
from spotpress.ui.preferences_tab import PreferencesTab
from spotpress.ui.devices_tab import DevicesTab
from spotpress.ui.log_tab import LogTab


from spotpress.hw.lnx.devices import DeviceMonitor


if SP_QT_VERSION == 5:
    import ctypes

    # Redireciona mensagens do Qt para /dev/null
    ctypes.CDLL(None).freopen(
        b"/dev/null", b"w", ctypes.c_void_p.in_dll(ctypes.CDLL(None), "stderr")
    )


class SpotpressPreferences(QMainWindow):
    log_signal = pyqtSignal(str)
    info_signal = pyqtSignal(str)
    refresh_devices_signal = pyqtSignal()
    show_overlay_signal = pyqtSignal()
    hide_overlay_signal = pyqtSignal()

    def __init__(self, debug_mode=False):
        super().__init__()

        self.ipc_server = None

        self.setWindowTitle("Spotpress preferences dialog")
        self.setGeometry(100, 100, 650, 700)

        # Quando fechar a janela, ao invés de fechar, esconder
        self.setWindowFlags(self.windowFlags() | Qt_WindowMinimizeButtonHint)
        self.setMinimumSize(650, 700)

        self._ctx = AppContext(
            screen_index=0,
            log_function=self.thread_safe_log,
            show_info_function=self.thread_safe_info,
            show_overlay_function=self.thread_safe_show_overlay,
            hide_overlay_function=self.thread_safe_hide_overlay,
            main_window=self,
            debug_mode=debug_mode,
        )

        self.tabs = QTabWidget()
        self.preferences_tab = PreferencesTab(self, self._ctx)
        self.devices_tab = DevicesTab(self, self._ctx)
        self.log_tab = LogTab(self, self._ctx)

        self.tabs.addTab(self.preferences_tab, "Preferences")
        self.tabs.addTab(self.devices_tab, "Devices")

        if debug_mode:
            self.log_tab = LogTab(self, self._ctx)
            self.tabs.addTab(self.log_tab, "Log")

        self.devices_tab.screen_changed.connect(self.change_screen)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)

        bottom_layout = QHBoxLayout()
        self.quit_button = QPushButton("Quit Spotpress")
        self.quit_button.clicked.connect(self.on_quit_clicked)
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.on_close_clicked)

        self.about_button = QPushButton("About Spotpress...")
        self.about_button.clicked.connect(self.show_about)
        bottom_layout.addWidget(self.quit_button)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.about_button)
        bottom_layout.addWidget(self.close_button)

        main_layout.addLayout(bottom_layout)

        container = QWidget()

        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Functional Startups

        self.tray_icon = None

        self._info_timer = QTimer(self)
        self._info_timer.setSingleShot(True)
        self._info_timer.timeout.connect(
            lambda: self._ctx.info_overlay and self._ctx.info_overlay.hide()
        )

        self.create_tray_icon()

        self.center_on_screen()

        self.create_spotlight_overlay()

        self.create_information_overlay()

        self.devices_tab.refresh_screens()

        self._ctx.ui_ready = True

        self.load_config()
        if debug_mode:
            self.log_signal.connect(self.append_log)
        self.info_signal.connect(self.show_info)
        self.show_overlay_signal.connect(self.show_overlay)
        self.hide_overlay_signal.connect(self.hide_overlay)

        self.device_monitor = DeviceMonitor(self._ctx)
        self.device_monitor.start_monitoring()
        self.refresh_devices_signal.connect(self.refresh_devices_list)
        self.refresh_devices_signal.connect(
            self.preferences_tab.update_modes_list_from_context
        )
        self.device_monitor.register_hotplug_callback(self.emit_refresh_devices_signal)
        self.refresh_devices_list()
        self.preferences_tab.update_modes_list_from_context()

        # if debug_mode:
        #     from spotpress.utils import set_debug_border
        #
        #     set_debug_border(self)

    def handle_command_from_ipc(self, command: str):
        if command == "--ping":
            pass  # Used only to check if the instance is alive
        elif command == "--show-window":
            self.show_window()
        elif command == "--hide-window":
            self.hide_window()
        elif command == "--quit":
            self.on_quit_clicked()
        elif command.startswith("--set-auto-mode="):
            val = command.split("=", 1)[1] == "on"
            if self._ctx.overlay_window:
                self._ctx.overlay_window.set_auto_mode(enable=val)
        elif command.startswith("--set-mode="):
            mode = command.split("=", 1)[1]
            if mode in MODES_CMD_LINE_MAP.keys() and self._ctx.overlay_window:
                mode_to_switch = MODES_CMD_LINE_MAP[mode]
                self._ctx.overlay_window.switch_mode(direct_mode=mode_to_switch)
                self.thread_safe_log(f"[IPC] Comando: mudar para modo '{mode}'")
        else:
            self.thread_safe_log(f"[IPC] Comando desconhecido: {command}")

    def center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            fg = self.frameGeometry()
            fg.moveCenter(geometry.center())
            self.move(fg.topLeft())

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon_Trigger:

            if self.isVisible():
                self.hide_window()
            else:
                self.show_window()
                self.activateWindow()

    def refresh_devices_list(self):
        self.devices_tab.devices_list.blockSignals(True)
        try:
            devices = self.device_monitor.get_monitored_devices()
            current_items = {}

            # Mapear dispositivos atualmente na lista
            for i in range(self.devices_tab.devices_list.count()):
                item = self.devices_tab.devices_list.item(i)
                dev = item.data(QtItem_UserRole)  # pyright: ignore
                if dev:
                    current_items[dev] = item

            new_devices = set(devices)
            old_devices = set(current_items.keys())

            # Remover itens que não estão mais presentes
            for dev in old_devices - new_devices:
                item = current_items[dev]
                row = self.devices_tab.devices_list.row(item)
                self.devices_tab.devices_list.takeItem(row)

            # Adicionar novos dispositivos que ainda não estão na lista
            for dev in new_devices - old_devices:
                item = QListWidgetItem(dev.display_name())
                item.setData(QtItem_UserRole, dev)
                self.devices_tab.devices_list.addItem(item)

            # Atualiza o modo se necessário
            self.preferences_tab.update_modes_list_from_context()

            # Re-seleciona o dispositivo ativo
            active_dev = self._ctx.active_device
            self.devices_tab.select_device_on_list(active_dev)

            self.devices_tab.devices_list.setEnabled(bool(devices))

        finally:
            self.devices_tab.devices_list.blockSignals(False)

    def create_tray_icon(self):
        icon = QIcon(ICON_FILE)
        self.tray_icon = QSystemTrayIcon(icon, self)

        menu = QMenu()
        restore_action = QAction("Restore", self)
        restore_action.triggered.connect(self.show_window)
        menu.addAction(restore_action)
        about_action = QAction("About...", self)
        about_action.triggered.connect(self.show_about)
        menu.addAction(about_action)
        exit_action = QAction("Sair", self)
        exit_action.triggered.connect(self.on_quit_clicked)
        menu.addAction(exit_action)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def create_information_overlay(self):
        # Pega o monitor que não está sendo usado pelo spotlight
        all_screens = QApplication.screens()
        target_index = 0
        if len(all_screens) > 1:
            target_index = 1 if self._ctx.screen_index == 0 else 0
        else:
            return
        geometry = all_screens[target_index].geometry()
        if self._ctx.info_overlay:
            self._ctx.info_overlay.setGeometry(geometry)
        self._ctx.info_overlay = InfOverlayWindow(geometry)

    def create_spotlight_overlay(self):
        screen_index = self._ctx.screen_index
        geometry = get_screen_geometry(screen_index)

        if self._ctx.overlay_window:
            self._ctx.screen_index = screen_index
            self._ctx.overlay_window.setGeometry(geometry)
        else:
            self._ctx.overlay_window = SpotlightOverlayWindow(
                context=self._ctx,
                screen_geometry=geometry,
            )

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_window(self):
        self.hide()

    def show_about(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("About SpotPress...")
        msg.setText(
            "SpotPress: A Spotlight Aplication For Presentations.\n"
            f"Powered By PyQT{SP_QT_VERSION}\n"
            f"Active Device: {self._ctx.active_device}\n"
            "Licenced under LGPL\nContributors:\nAlexandre da Silva <lexrupy>"
        )

        pixmap = QPixmap(ICON_FILE)
        msg.setIconPixmap(pixmap)

        msg.exec()

    def append_log(self, message):
        if self._ctx.debug_mode:
            if hasattr(self, "log_tab"):
                self.log_tab.append_log_message(message)
            print(message)

    def show_info(self, mensagem):
        if self._ctx.info_overlay:
            self._ctx.info_overlay.show_message(mensagem)
            self._info_timer.start(1000)

    def show_overlay(self):
        if self._ctx.overlay_window is not None:
            self._ctx.overlay_window.show_overlay()

    def hide_overlay(self):
        if self._ctx.overlay_window is not None:
            self._ctx.overlay_window.hide_overlay()

    def thread_safe_hide_overlay(self):
        self.hide_overlay_signal.emit()

    def thread_safe_show_overlay(self):
        self.show_overlay_signal.emit()

    def thread_safe_log(self, message):
        self.log_signal.emit(message)

    def thread_safe_info(self, message):
        self.info_signal.emit(message)

    def emit_refresh_devices_signal(self):
        self.refresh_devices_signal.emit()

    # Métodos de eventos (placeholders)
    def on_quit_clicked(self):
        self.hide_window()
        self.running = False
        if hasattr(self, "device_monitor"):
            self.device_monitor.stop_monitoring()
        if self.tray_icon:
            self.tray_icon.hide()
        if self._ctx.overlay_window:
            self._ctx.overlay_window.close()
        if self._ctx.info_overlay:
            self._ctx.info_overlay.close()
        self.save_config()
        QApplication.quit()

    def on_close_clicked(self):
        self.hide_window()
        self.append_log("Janela oculta. Clique no ícone da bandeja para restaurar.")

    def change_screen(self, screen_index):
        if self._ctx.screen_index != screen_index:
            self._ctx.screen_index = screen_index
            self.create_spotlight_overlay()
            self.create_information_overlay()
            self.append_log(f"> Tela selecionada: {screen_index}")

    def load_config(self):
        if not os.path.exists(CONFIG_PATH):
            self.preferences_tab.load_defaults()
            return
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)
        self.preferences_tab.load_config(config)
        current_mode = config.getint("Modes", "current_mode", fallback=0)
        self._ctx.current_mode = current_mode
        self.preferences_tab.set_current_mode(current_mode)
        self.preferences_tab.update_context_config()

    def save_config(self):
        config = configparser.ConfigParser()
        self.preferences_tab.save_config(config)
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as configfile:
            config.write(configfile)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt_Key_S:
            self.show_overlay()
