from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QApplication,
    QListWidget,
    QGroupBox,
    QTextEdit,
)

from PyQt5.QtCore import pyqtSignal, Qt, QTimer


class DevicesTab(QWidget):
    screen_changed = pyqtSignal(int)

    def __init__(self, parent, ctx):
        super().__init__(parent)
        self._ctx = ctx
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        screen_group = QGroupBox("Screens")
        screen_layout = QHBoxLayout()
        self.screen_list = QListWidget()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.on_refresh_clicked)
        self.screen_list.currentItemChanged.connect(self.on_screen_changed)
        self.screen_list.setMaximumHeight(70)
        screen_layout.addWidget(self.screen_list)
        screen_layout.addWidget(self.refresh_button)
        screen_group.setLayout(screen_layout)
        layout.addWidget(screen_group)

        self.devices_list = QListWidget()

        layout.addWidget(QLabel("Detected Devices"))
        layout.addWidget(self.devices_list)
        self.devices_list.currentItemChanged.connect(self.on_device_selected)
        layout.addWidget(QLabel("Device Configuration"))
        layout.addWidget(QTextEdit("this device does not have special configurations"))
        self.setLayout(layout)

    def refresh_screens(self):
        non_primary_index = None
        self.screens = QApplication.screens()
        self.screen_list.clear()
        for i, screen in enumerate(self.screens):
            geom = screen.geometry()
            x, y, w, h = geom.x(), geom.y(), geom.width(), geom.height()
            text = f"{i}: {w}x{h} @ {x},{y}"
            if screen == QApplication.primaryScreen():
                text += " [Primário]"
            else:
                non_primary_index = i
            self.screen_list.addItem(text)
        # Seleciona o primeiro monitor que não for primário
        if non_primary_index is not None:
            self.screen_list.setCurrentRow(non_primary_index)
        elif self.screen_list.count() > 0:
            self.screen_list.setCurrentRow(0)  # Fallback

    def on_refresh_clicked(self):
        self.refresh_screens()

    def on_screen_changed(self):
        idx = self.screen_list.currentRow()
        if idx >= 0:
            self.screen_changed.emit(idx)

    def change_device(self, dev):
        self._ctx.device_monitor.set_active_device(dev)
        # self._ctx.set_active_device(dev)

    def on_device_selected(self, current, previous):
        if current:
            dev = current.data(Qt.UserRole)
            QTimer.singleShot(50, lambda: self.change_device(dev))
            # self._ctx.main_window.preferences_tab.update_modes_list_from_context()
        else:
            self._ctx.set_active_device(None)
            # self._ctx.main_window.preferences_tab.update_modes_list_from_context()
