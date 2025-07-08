import sys
import os
import configparser
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QSizePolicy,
    QSystemTrayIcon,
    QWidget,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QTextEdit,
    QListWidget,
    QMainWindow,
    QGroupBox,
    QDesktopWidget,
)
from PyQt5.QtGui import QGuiApplication, QIcon, QPainter, QPixmap, QColor
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from spotpress.appcontext import AppContext
from spotpress.spotlight import SpotlightOverlayWindow
from spotpress.infoverlay import InfOverlayWindow
from spotpress.utils import (
    LASER_COLORS,
    MODE_MAP,
    PEN_COLORS,
    SHADE_COLORS,
    capture_monitor_screenshot,
)


CONFIG_PATH = os.path.expanduser("~/.config/spotpress/config.ini")

WINDOWS_OS = False
if sys.platform.startswith("win"):
    WINDOWS_OS = True
    from spotpress.devices_win import DeviceMonitor
else:
    from spotpress.devices import DeviceMonitor


def create_color_combobox(colors):
    combo = QComboBox()
    for color, name in colors:
        pixmap = QPixmap(16, 16)
        pixmap.fill(color)
        combo.addItem(QIcon(pixmap), name)
    return combo


def create_named_color_combobox(named_colors):
    combo = QComboBox()
    for value in named_colors:
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(value[0]))
        combo.addItem(QIcon(pixmap), value[1])
    return combo


class SpotpressPreferences(QMainWindow):
    log_signal = pyqtSignal(str)
    info_signal = pyqtSignal(str)
    change_screen_signal = pyqtSignal(int)
    refresh_devices_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spotpress preferences dialog")
        self.setGeometry(100, 100, 650, 550)
        self.ui_started_up = False

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
            change_screen_function=self.thread_safe_change_screen,
            main_window=self,
        )

        self._ctx.windows_os = WINDOWS_OS

        # Reverter MODE_MAP para obter nome -> valor
        self.MODE_NAME_TO_ID = {v: k for k, v in MODE_MAP.items()}

        # Lista default com todos habilitados
        self.default_modes = [(name, True) for name in self.MODE_NAME_TO_ID.keys()]

        self.tabs = QTabWidget()
        self.preferences_tab = QWidget()
        self.devices_tab = QWidget()
        self.log_tab = QWidget()

        self.icon = None

        self.tabs.addTab(self.preferences_tab, "Preferences")
        self.tabs.addTab(self.devices_tab, "Devices")
        self.tabs.addTab(self.log_tab, "Log")

        self.init_preferences_tab()
        self.init_devices_tab()
        self.init_log_tab()

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

        self.refresh_screens()

        self.ui_started_up = True

        self.load_config()

        if self.modes_list.count() == 0:
            for name, enabled in self.default_modes:
                item = QListWidgetItem(name)
                item.setFlags(
                    item.flags()
                    | Qt.ItemIsUserCheckable
                    | Qt.ItemIsEnabled
                    | Qt.ItemIsSelectable
                )
                item.setCheckState(Qt.Checked if enabled else Qt.Unchecked)
                self.modes_list.addItem(item)

        self.log_signal.connect(self.append_log)
        self.info_signal.connect(self.show_info)

        self.change_screen_signal.connect(self.change_screen)

        self.device_monitor = DeviceMonitor(self._ctx)
        self.device_monitor.start_monitoring()
        self.refresh_devices_signal.connect(self.refresh_devices_list)
        self.device_monitor.register_hotplug_callback(self.emit_refresh_devices_signal)
        self.refresh_devices_list()

    def init_preferences_tab(self):
        main_layout = QVBoxLayout()

        def make_group(title):
            box = QGroupBox(title)
            box.setStyleSheet(
                "QGroupBox { background-color: #f0f0f0; border: 2px solid lightgray; margin-top: 1ex; }"
            )
            return box

        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Spotlight
        self.spotlight_shape = QComboBox()
        self.spotlight_shape.addItem("Elipse")
        self.spotlight_shape.addItem("Rectangle")
        self.spotlight_shape.currentIndexChanged.connect(
            self.on_spotlight_shape_changed
        )
        self.spotlight_size = QSpinBox()
        self.spotlight_size.setMaximum(99)
        self.spotlight_size.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.spotlight_size.valueChanged.connect(self.on_spotlight_size_changed)
        self.spotlight_shade = QCheckBox("Show shade")
        self.spotlight_shade.stateChanged.connect(self.on_spotlight_shade_changed)
        self.spotlight_border = QCheckBox("Show border")
        self.spotlight_border.stateChanged.connect(self.on_spotlight_border_changed)

        spotlight_group = make_group("Spotlight")
        spotlight_layout = QGridLayout()
        spotlight_layout.addWidget(QLabel("Shape:"), 0, 0)
        spotlight_layout.addWidget(self.spotlight_shape, 0, 1, 1, 2)
        spotlight_layout.addWidget(QLabel("Size:"), 1, 0)
        spotlight_layout.addWidget(self.spotlight_size, 1, 1)
        spotlight_layout.addWidget(QLabel("% of screen heigth"), 1, 2)
        spotlight_layout.addWidget(self.spotlight_shade, 2, 0, 1, 2)
        spotlight_layout.addWidget(self.spotlight_border, 2, 2)
        spotlight_group.setLayout(spotlight_layout)
        left_layout.addWidget(spotlight_group)

        # Magnifyer
        self.magnify_shape = QComboBox()

        self.magnify_shape.addItem("Elipse")
        self.magnify_shape.addItem("Rectangle")
        self.magnify_shape.currentIndexChanged.connect(self.on_magnify_shape_changed)
        self.magnify_size = QSpinBox()
        self.magnify_size.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.magnify_size.valueChanged.connect(self.on_magnify_size_changed)
        self.magnify_border = QCheckBox("Show border")
        self.magnify_border.stateChanged.connect(self.on_magnify_border_changed)
        self.magnify_zoom = QSpinBox()
        self.magnify_zoom.setMaximum(5)
        self.magnify_zoom.setMinimum(2)
        self.magnify_zoom.valueChanged.connect(self.on_magnify_zoom_changed)

        magnify_group = make_group("Magnifyer")
        magnify_layout = QGridLayout()
        magnify_layout.addWidget(QLabel("Shape:"), 0, 0)
        magnify_layout.addWidget(self.magnify_shape, 0, 1, 1, 2)
        magnify_layout.addWidget(QLabel("Size:"), 1, 0)
        magnify_layout.addWidget(self.magnify_size, 1, 1)
        magnify_layout.addWidget(QLabel("% of screen height"), 1, 2)
        magnify_layout.addWidget(self.magnify_border, 2, 0, 1, 3)
        magnify_layout.addWidget(QLabel("Zoom level:"), 3, 0)
        magnify_layout.addWidget(self.magnify_zoom, 3, 1, 1, 2)
        magnify_group.setLayout(magnify_layout)
        left_layout.addWidget(magnify_group)

        # Laser
        self.laser_dot_size = QSpinBox()

        self.laser_dot_size.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.laser_dot_size.valueChanged.connect(self.on_laser_dot_size_changed)
        self.laser_color = create_color_combobox(LASER_COLORS)
        self.laser_color.currentIndexChanged.connect(self.on_laser_color_changed)
        self.laser_opacity = QSpinBox()

        self.laser_opacity.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.laser_opacity.valueChanged.connect(self.on_laser_opacity_changed)
        self.laser_reflection = QCheckBox("Show reflection")
        self.laser_reflection.stateChanged.connect(self.on_laser_reflection_changed)

        laser_group = make_group("Laser")
        laser_layout = QGridLayout()
        laser_layout.addWidget(QLabel("Dot size:"), 0, 0)
        laser_layout.addWidget(self.laser_dot_size, 0, 1)
        laser_layout.addWidget(QLabel("% of screen height"), 0, 2)
        laser_layout.addWidget(QLabel("Dot color:"), 1, 0)
        laser_layout.addWidget(self.laser_color, 1, 1, 1, 2)
        laser_layout.addWidget(QLabel("Opacity:"), 2, 0)
        laser_layout.addWidget(self.laser_opacity, 2, 1)
        laser_layout.addWidget(QLabel("%"), 2, 2)
        laser_layout.addWidget(self.laser_reflection, 3, 0, 1, 3)
        laser_group.setLayout(laser_layout)
        left_layout.addWidget(laser_group)

        # Marker
        self.marker_width = QSpinBox()

        self.marker_width.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.marker_width.valueChanged.connect(self.on_marker_width_changed)
        self.marker_color = create_color_combobox(PEN_COLORS)
        self.marker_color.currentIndexChanged.connect(self.on_marker_color_changed)
        self.marker_opacity = QSpinBox()

        self.marker_opacity.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.marker_opacity.valueChanged.connect(self.on_marker_opacity_changed)

        marker_group = make_group("Marker")
        marker_layout = QGridLayout()
        marker_layout.addWidget(QLabel("Width:"), 0, 0)
        marker_layout.addWidget(self.marker_width, 0, 1)
        marker_layout.addWidget(QLabel("pixels"), 0, 2)
        marker_layout.addWidget(QLabel("Color:"), 1, 0)
        marker_layout.addWidget(self.marker_color, 1, 1, 1, 2)
        marker_layout.addWidget(QLabel("Opacity:"), 2, 0)
        marker_layout.addWidget(self.marker_opacity, 2, 1)
        marker_layout.addWidget(QLabel("%"), 2, 2)
        marker_group.setLayout(marker_layout)
        right_layout.addWidget(marker_group)

        # Shade
        self.shade_color = create_named_color_combobox(SHADE_COLORS)
        self.shade_color.currentIndexChanged.connect(self.on_shade_color_changed)
        self.shade_opacity = QSpinBox()

        self.shade_opacity.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.shade_opacity.valueChanged.connect(self.on_shade_opacity_changed)

        shade_group = make_group("Shade")
        shade_layout = QGridLayout()
        shade_layout.addWidget(QLabel("Color:"), 0, 0)
        shade_layout.addWidget(self.shade_color, 0, 1, 1, 2)
        shade_layout.addWidget(QLabel("Opacity:"), 1, 0)
        shade_layout.addWidget(self.shade_opacity, 1, 1)
        shade_layout.addWidget(QLabel("%"), 1, 2)
        shade_group.setLayout(shade_layout)
        right_layout.addWidget(shade_group)

        # Border
        self.border_color = create_color_combobox(PEN_COLORS)
        self.border_color.currentIndexChanged.connect(self.on_border_color_changed)
        self.border_opacity = QSpinBox()

        self.border_opacity.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.border_opacity.valueChanged.connect(self.on_border_opacity_changed)
        self.border_width = QSpinBox()

        self.border_width.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.border_width.valueChanged.connect(self.on_border_width_changed)

        border_group = make_group("Border")
        border_layout = QGridLayout()
        border_layout.addWidget(QLabel("Color:"), 0, 0)
        border_layout.addWidget(self.border_color, 0, 1, 1, 2)
        border_layout.addWidget(QLabel("Opacity:"), 1, 0)
        border_layout.addWidget(self.border_opacity, 1, 1)
        border_layout.addWidget(QLabel("%"), 1, 2)
        border_layout.addWidget(QLabel("Width:"), 2, 0)
        border_layout.addWidget(self.border_width, 2, 1)
        border_layout.addWidget(QLabel("pixels"), 2, 2)
        border_group.setLayout(border_layout)
        right_layout.addWidget(border_group)

        # General abaixo
        general_group = make_group("General")
        general_layout = QHBoxLayout()

        # Lado esquerdo com checkboxes e botões
        left_side = QVBoxLayout()

        checkbox_layout = QHBoxLayout()
        self.general_always_capture_screenshot = QCheckBox("Always capture screenshot")
        self.general_always_capture_screenshot.stateChanged.connect(
            self.on_general_always_capture_screenshot_changed
        )
        self.general_enable_auto_mode = QCheckBox("Enable AUTO mode if supported")
        self.general_enable_auto_mode.stateChanged.connect(
            self.on_general_enable_auto_mode_changed
        )
        checkbox_layout.addWidget(self.general_always_capture_screenshot)
        checkbox_layout.addWidget(self.general_enable_auto_mode)

        button_layout = QHBoxLayout()
        self.reset_button = QPushButton("Reset Settings")
        self.reset_button.clicked.connect(self.on_reset_clicked)
        self.test_button = QPushButton("Show Test...")
        self.test_button.clicked.connect(self.on_test_clicked)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.test_button)

        left_side.addLayout(checkbox_layout)
        left_side.addLayout(button_layout)

        # Lado direito com a lista de modos
        self.modes_list = QListWidget()
        self.modes_list.setSelectionMode(QListWidget.SingleSelection)
        self.modes_list.setDragDropMode(QListWidget.InternalMove)
        self.modes_list.setDefaultDropAction(Qt.MoveAction)

        right_side = QVBoxLayout()
        right_side.addWidget(QLabel("Enabled Modes (drag to reorder):"))
        right_side.addWidget(self.modes_list)

        # Junta os lados
        general_layout.addLayout(left_side)
        general_layout.addLayout(right_side)
        general_group.setLayout(general_layout)

        main_layout.addLayout(self._side_by_side_layout(left_layout, right_layout))
        main_layout.addWidget(general_group)
        self.preferences_tab.setLayout(main_layout)

    def _side_by_side_layout(self, left, right):
        layout = QHBoxLayout()
        layout.addLayout(left)
        layout.addLayout(right)
        return layout

    def init_devices_tab(self):
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
        layout.addWidget(QLabel("Device Configuration"))
        layout.addWidget(QTextEdit("this device does not have special configurations"))
        self.devices_tab.setLayout(layout)

    def init_log_tab(self):
        layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Log...")
        clear_btn = QPushButton("Clear Log")
        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        button_layout.addWidget(clear_btn)
        clear_btn.clicked.connect(self.on_clear_log_clicked)
        layout.addLayout(button_layout)
        self.log_tab.setLayout(layout)

    def center_on_screen(self):
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
        self.devices_list.clear()
        devices = self.device_monitor.get_monitored_devices()
        if not devices:
            self.devices_list.addItem("Nenhum dispositivo monitorado")
            self.devices_list.setEnabled(False)
            return

        self.devices_list.setEnabled(True)
        for dev in devices:
            item = QListWidgetItem(dev.display_name())
            item.setData(Qt.UserRole, dev)
            self.devices_list.addItem(item)

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
        all_screens = QGuiApplication.screens()
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
        self.log_text.append(message)

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

    def thread_safe_change_screen(self, screen_index):
        self.change_screen_signal.emit(screen_index)

    def emit_refresh_devices_signal(self):
        self.refresh_devices_signal.emit()

    # Métodos de eventos (placeholders)
    def on_quit_clicked(self):

        self.running = False
        if self.icon:
            self.icon.stop()
        self.save_config()
        QApplication.quit()

    def on_close_clicked(self):
        self.hide()
        self.append_log("Janela oculta. Clique no ícone da bandeja para restaurar.")

    def on_spotlight_shape_changed(self):
        self.update_context_config()

    def on_spotlight_size_changed(self):
        self.update_context_config()

    def on_spotlight_shade_changed(self):
        self.update_context_config()

    def on_spotlight_border_changed(self):
        self.update_context_config()

    def on_magnify_shape_changed(self):
        self.update_context_config()

    def on_magnify_size_changed(self):
        self.update_context_config()

    def on_magnify_border_changed(self):
        self.update_context_config()

    def on_magnify_zoom_changed(self):
        self.update_context_config()

    def on_laser_dot_size_changed(self):
        self.update_context_config()

    def on_laser_color_changed(self):
        self.update_context_config()

    def on_laser_opacity_changed(self):
        self.update_context_config()

    def on_laser_reflection_changed(self):
        self.update_context_config()

    def on_marker_width_changed(self):
        self.update_context_config()

    def on_marker_color_changed(self):
        self.update_context_config()

    def on_marker_opacity_changed(self):
        self.update_context_config()

    def on_shade_color_changed(self):
        self.update_context_config()

    def on_shade_opacity_changed(self):
        self.update_context_config()

    def on_border_color_changed(self):
        self.update_context_config()

    def on_border_opacity_changed(self):
        self.update_context_config()

    def on_border_width_changed(self):
        self.update_context_config()

    def on_refresh_clicked(self):
        self.refresh_screens()

    def on_screen_changed(self):
        idx = self.screen_list.currentRow()
        self.change_screen(idx)

    def change_screen(self, screen_index):
        if self._ctx.screen_index != screen_index:
            self._ctx.screen_index = screen_index
            self.create_spotlight_overlay()
            self.create_information_overlay()
            self.append_log(f"> Tela selecionada: {screen_index}")

    def on_general_always_capture_screenshot_changed(self):
        pass

    def on_general_enable_auto_mode_changed(self):
        pass

    def on_clear_log_clicked(self):
        self.log_text.clear()

    def on_reset_clicked(self):
        resposta = QMessageBox.question(
            self,
            "Confirmation",
            "Are you sure to reset configuration to defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if resposta == QMessageBox.Yes:
            self.spotlight_size.setValue(35)
            self.spotlight_shade.setChecked(True)
            self.spotlight_shape.setCurrentIndex(0)
            self.magnify_size.setValue(35)
            self.magnify_border.setChecked(True)
            self.magnify_shape.setCurrentIndex(1)
            self.laser_dot_size.setValue(20)
            self.laser_opacity.setValue(10)
            self.laser_reflection.setChecked(True)
            self.marker_width.setValue(20)
            self.marker_opacity.setValue(0)
            self.marker_color.setCurrentIndex(1)
            self.shade_opacity.setValue(5)
            self.border_opacity.setValue(90)
            self.border_width.setValue(16)
            self.border_color.setCurrentIndex(7)  # White
            self.general_always_capture_screenshot.setChecked(True)
            self.general_enable_auto_mode.setChecked(True)

    def load_config(self):
        config = configparser.ConfigParser()
        if not os.path.exists(CONFIG_PATH):
            return

        config.read(CONFIG_PATH)

        def getint(section, key, fallback):
            return int(config.get(section, key, fallback=str(fallback)))

        def getbool(section, key, fallback):
            return config.getboolean(section, key, fallback=fallback)

        def getindex_by_text(combo, text):
            for i in range(combo.count()):
                if combo.itemText(i).lower() == text.lower():
                    return i
            return 0

        try:
            self.spotlight_shape.setCurrentIndex(
                getindex_by_text(
                    self.spotlight_shape,
                    config.get("Spotlight", "shape", fallback="elipse"),
                )
            )
            self.spotlight_size.setValue(getint("Spotlight", "size", 35))
            self.spotlight_shade.setChecked(getbool("Spotlight", "shade", True))
            self.spotlight_border.setChecked(getbool("Spotlight", "border", True))

            self.magnify_shape.setCurrentIndex(
                getindex_by_text(
                    self.magnify_shape,
                    config.get("Magnify", "shape", fallback="rectangle"),
                )
            )
            self.magnify_size.setValue(getint("Magnify", "size", 35))
            self.magnify_border.setChecked(getbool("Magnify", "border", True))
            self.magnify_zoom.setValue(getint("Magnify", "zoom", 2))

            self.laser_dot_size.setValue(getint("Laser", "dot_size", 20))
            self.laser_color.setCurrentIndex(getint("Laser", "color_index", 0))
            self.laser_opacity.setValue(getint("Laser", "opacity", 10))
            self.laser_reflection.setChecked(getbool("Laser", "reflection", True))

            self.marker_width.setValue(getint("Marker", "width", 20))
            self.marker_color.setCurrentIndex(getint("Marker", "color_index", 1))
            self.marker_opacity.setValue(getint("Marker", "opacity", 0))

            self.shade_color.setCurrentIndex(getint("Shade", "color_index", 0))
            self.shade_opacity.setValue(getint("Shade", "opacity", 5))

            self.border_color.setCurrentIndex(getint("Border", "color_index", 7))
            self.border_opacity.setValue(getint("Border", "opacity", 90))
            self.border_width.setValue(getint("Border", "width", 16))

            self.general_always_capture_screenshot.setChecked(
                getbool("General", "always_capture", True)
            )
            self.general_enable_auto_mode.setChecked(
                getbool("General", "auto_mode", True)
            )

            self.modes_list.clear()
            mode_id_to_name = MODE_MAP
            i = 0
            while True:
                key = f"mode{i}"
                if "Modes" not in config or key not in config["Modes"]:
                    break
                try:
                    raw = config["Modes"][key]
                    mode_id_str, enabled_str = raw.split("|")
                    mode_id = int(mode_id_str)
                    enabled = bool(int(enabled_str))
                    name = mode_id_to_name.get(mode_id, f"Unknown({mode_id})")
                    item = QListWidgetItem(name)
                    item.setFlags(
                        item.flags()
                        | Qt.ItemIsUserCheckable
                        | Qt.ItemIsEnabled
                        | Qt.ItemIsSelectable
                    )
                    item.setCheckState(Qt.Checked if enabled else Qt.Unchecked)
                    self.modes_list.addItem(item)
                except Exception as e:
                    self.append_log(f"Erro ao carregar modo '{raw}': {e}")
                i += 1

            current_mode = config.getint("Modes", "current_mode", fallback=0)
            self._ctx.current_mode = current_mode  # armazena no contexto se quiser

            # Seleciona o item correspondente na lista
            for i in range(self.modes_list.count()):
                item = self.modes_list.item(i)
                name = item.text()
                mode_id = self.MODE_NAME_TO_ID.get(name)
                if mode_id == current_mode:
                    self.modes_list.setCurrentRow(i)
                    break

        except Exception as e:
            print("Erro ao carregar configurações:", e)

        self.update_context_config()

    def save_config(self):
        config = configparser.ConfigParser()

        config["Spotlight"] = {
            "shape": self.spotlight_shape.currentText(),
            "size": str(self.spotlight_size.value()),
            "shade": str(self.spotlight_shade.isChecked()),
            "border": str(self.spotlight_border.isChecked()),
        }
        config["Magnify"] = {
            "shape": self.magnify_shape.currentText(),
            "size": str(self.magnify_size.value()),
            "border": str(self.magnify_border.isChecked()),
            "zoom": str(self.magnify_zoom.value()),
        }
        config["Laser"] = {
            "dot_size": str(self.laser_dot_size.value()),
            "color_index": str(self.laser_color.currentIndex()),
            "opacity": str(self.laser_opacity.value()),
            "reflection": str(self.laser_reflection.isChecked()),
        }
        config["Marker"] = {
            "width": str(self.marker_width.value()),
            "color_index": str(self.marker_color.currentIndex()),
            "opacity": str(self.marker_opacity.value()),
        }
        config["Shade"] = {
            "color_index": str(self.shade_color.currentIndex()),
            "opacity": str(self.shade_opacity.value()),
        }
        config["Border"] = {
            "color_index": str(self.border_color.currentIndex()),
            "opacity": str(self.border_opacity.value()),
            "width": str(self.border_width.value()),
        }
        config["General"] = {
            "always_capture": str(self.general_always_capture_screenshot.isChecked()),
            "auto_mode": str(self.general_enable_auto_mode.isChecked()),
        }

        config["Modes"] = {}

        for i in range(self.modes_list.count()):
            item = self.modes_list.item(i)
            name = item.text()
            mode_id = self.MODE_NAME_TO_ID.get(name)
            if mode_id is not None:
                enabled = item.checkState() == Qt.Checked
                config["Modes"][f"mode{i}"] = f"{mode_id}|{int(enabled)}"

        selected_items = self.modes_list.selectedItems()
        if selected_items:
            selected_name = selected_items[0].text()
            current_id = self.MODE_NAME_TO_ID.get(selected_name)
            if current_id is not None:
                config["Modes"]["current_mode"] = str(current_id)

        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as configfile:
            config.write(configfile)

    def update_context_config(self):
        if self._ctx and self.ui_started_up:
            cfg = self._ctx.config
            cfg["spotlight_shape"] = self.spotlight_shape.currentText()
            cfg["spotlight_size"] = self.spotlight_size.value()
            cfg["spotlight_shade"] = self.spotlight_shade.isChecked()
            cfg["spotlight_border"] = self.spotlight_border.isChecked()
            cfg["magnify_shape"] = self.magnify_shape.currentText()
            cfg["magnify_size"] = self.magnify_size.value()
            cfg["magnify_border"] = self.magnify_border.isChecked()
            cfg["magnify_zoom"] = self.magnify_zoom.value()
            cfg["laser_dot_size"] = self.laser_dot_size.value()
            cfg["laser_color_index"] = self.laser_color.currentIndex()
            cfg["laser_opacity"] = self.laser_opacity.value()
            cfg["laser_reflection"] = self.laser_reflection.isChecked()
            cfg["marker_width"] = self.marker_width.value()
            cfg["marker_color_index"] = self.marker_color.currentIndex()
            cfg["marker_opacity"] = self.marker_opacity.value()
            cfg["shade_color_index"] = self.shade_color.currentIndex()
            cfg["shade_opacity"] = self.shade_opacity.value()
            cfg["border_color_index"] = self.border_color.currentIndex()
            cfg["border_opacity"] = self.border_opacity.value()
            cfg["border_width"] = self.border_width.value()
            cfg["general_always_capture"] = (
                self.general_always_capture_screenshot.isChecked()
            )
            cfg["general_auto_mode"] = self.general_enable_auto_mode.isChecked()
            cfg["modes_current_mode"] = self._ctx.current_mode

    def on_test_clicked(self):
        if self._ctx.overlay_window is not None:
            self._ctx.overlay_window.show_overlay()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("SpotPress")
    window = SpotpressPreferences()
    window.show()
    sys.exit(app.exec_())
