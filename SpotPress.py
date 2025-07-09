import sys
import os
import configparser
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
    QWidget,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMainWindow,
    QDesktopWidget,
)
from PyQt5.QtGui import QIcon, QPainter, QPixmap, QColor
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from spotpress.appcontext import AppContext
from spotpress.spotlight import SpotlightOverlayWindow
from spotpress.infoverlay import InfOverlayWindow
from spotpress.utils import (
    capture_monitor_screenshot,
)
from spotpress.ui.preferences_tab import PreferencesTab
from spotpress.ui.devices_tab import DevicesTab
from spotpress.ui.log_tab import LogTab


CONFIG_PATH = os.path.expanduser("~/.config/spotpress/config.ini")

WINDOWS_OS = False
if sys.platform.startswith("win"):
    WINDOWS_OS = True
    from spotpress.devices_win import DeviceMonitor
else:
    from spotpress.devices import DeviceMonitor


class SpotpressPreferences(QMainWindow):
    log_signal = pyqtSignal(str)
    info_signal = pyqtSignal(str)
    refresh_devices_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spotpress preferences dialog")
        self.setGeometry(100, 100, 650, 550)

        # Quando fechar a janela, ao invés de fechar, esconder
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint)
        if WINDOWS_OS:
            self.setMinimumSize(650, 760)
        else:
            self.setMinimumSize(800, 680)

        self._ctx = AppContext(
            screen_index=0,
            log_function=self.thread_safe_log,
            show_info_function=self.thread_safe_info,
            main_window=self,
        )

        self._ctx.windows_os = WINDOWS_OS

        self.tabs = QTabWidget()
        self.preferences_tab = PreferencesTab(self, self._ctx)
        self.devices_tab = DevicesTab(self, self._ctx)
        self.log_tab = LogTab(self, self._ctx)

        self.tabs.addTab(self.preferences_tab, "Preferences")
        self.tabs.addTab(self.devices_tab, "Devices")
        self.tabs.addTab(self.log_tab, "Log")

        self.devices_tab.screen_changed.connect(self.change_screen)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)

        bottom_layout = QHBoxLayout()
        self.quit_button = QPushButton("Quit Spotpress")
        self.quit_button.clicked.connect(self.on_quit_clicked)
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.on_close_clicked)
        bottom_layout.addWidget(self.quit_button)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.close_button)

        container = QWidget()
        container.setLayout(main_layout)
        main_layout.addLayout(bottom_layout)
        self.setCentralWidget(container)

        # Functional Startups

        self.tray_icon = None
        self.create_tray_icon()

        self.center_on_screen()

        self.create_spotlight_overlay()

        self.create_information_overlay()

        self.devices_tab.refresh_screens()

        self._ctx.ui_ready = True

        self.load_config()

        self.log_signal.connect(self.append_log)
        self.info_signal.connect(self.show_info)

        self.device_monitor = DeviceMonitor(self._ctx)
        self.device_monitor.start_monitoring()
        self.refresh_devices_signal.connect(self.refresh_devices_list)
        self.device_monitor.register_hotplug_callback(self.emit_refresh_devices_signal)
        self.refresh_devices_list()
        self.preferences_tab.update_modes_list_from_context()

    def center_on_screen(self):
        # screen_geometry = QDesktopWidget().availableGeometry()
        screen_geometry = QDesktopWidget().availableGeometry()
        screen_center_point = screen_geometry.center()
        qt_rectangle = self.frameGeometry()
        qt_rectangle.moveCenter(screen_center_point)
        self.move(qt_rectangle.topLeft())

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show_normal()
                self.activateWindow()

    def refresh_devices_list(self):
        self.devices_tab.devices_list.clear()
        devices = self.device_monitor.get_monitored_devices()
        if not devices:
            self.devices_tab.devices_list.addItem("Nenhum dispositivo monitorado")
            self.devices_tab.devices_list.setEnabled(False)
            return

        self.devices_tab.devices_list.setEnabled(True)
        for dev in devices:
            item = QListWidgetItem(dev.display_name())
            item.setData(Qt.UserRole, dev)
            self.devices_tab.devices_list.addItem(item)

    def create_tray_icon(self):
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor("gray"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, size, size)
        painter.end()

        icon = QIcon(pixmap)
        self.tray_icon = QSystemTrayIcon(icon, self)
        menu = QMenu()
        restore_action = QAction("Restaurar", self)
        restore_action.triggered.connect(self.show_normal)
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
        screenshot, geometry = capture_monitor_screenshot(screen_index)

        if self._ctx.overlay_window:
            self._ctx.screen_index = screen_index
            self._ctx.overlay_window.setGeometry(geometry)
        else:
            self._ctx.overlay_window = SpotlightOverlayWindow(
                context=self._ctx,
                screenshot=screenshot,
                screen_geometry=geometry,
            )

    def show_normal(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def show_about(self):
        QMessageBox.information(
            self,
            "About SpotPress...",
            "SpotPress: A Spotlight Aplication For Presentations.\nLicenced under LGPL\nContributors:\nAlexandre da Silva <lexrupy>",
        )

    def append_log(self, message):
        self.log_tab.append_log_message(message)

    def show_info(self, mensagem):
        if self._ctx.info_overlay:
            self._ctx.info_overlay.show_message(mensagem)

            if hasattr(self, "_info_timer") and self._info_timer:
                self._info_timer.stop()

            self._info_timer = QTimer(self)
            self._info_timer.setSingleShot(True)
            self._info_timer.timeout.connect(self._ctx.info_overlay.hide)
            self._info_timer.start(1000)

    def thread_safe_log(self, message):
        self.log_signal.emit(message)

    def thread_safe_info(self, message):
        self.info_signal.emit(message)

    def emit_refresh_devices_signal(self):
        self.refresh_devices_signal.emit()

    # Métodos de eventos (placeholders)
    def on_quit_clicked(self):
        self.running = False
        self.save_config()
        QApplication.quit()

    def on_close_clicked(self):
        self.hide()
        self.append_log("Janela oculta. Clique no ícone da bandeja para restaurar.")

    def on_refresh_clicked(self):
        self.refresh_screens()

    def change_screen(self, screen_index):
        if self._ctx.screen_index != screen_index:
            self._ctx.screen_index = screen_index
            self.create_spotlight_overlay()
            self.create_information_overlay()
            self.append_log(f"> Tela selecionada: {screen_index}")

    def load_config(self):
        if not os.path.exists(CONFIG_PATH):
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("SpotPress")
    window = SpotpressPreferences()
    window.show()
    sys.exit(app.exec_())
