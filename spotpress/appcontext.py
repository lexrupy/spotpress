from PyQt5.QtGui import QGuiApplication
from spotpress.utils import MODE_MOUSE, ObservableDict

from PyQt5.QtCore import QObject, pyqtSignal


class AppContext(QObject):
    configChanged = pyqtSignal(str, object)  # chave, valor

    def __init__(
        self,
        screen_index=0,
        log_function=None,
        overlay_window=None,
        show_info_function=None,
        change_screen_function=None,
        main_window=None,
    ):
        super().__init__()
        self._screen_index = screen_index
        self._log_function = log_function
        self._spotlight_overlay_window = overlay_window
        self._info_overlay_window = None
        self._show_info_function = show_info_function
        self._change_screen_function = change_screen_function
        self._compatible_modes = []
        self._config = ObservableDict(callback=self._on_config_changed)
        self.configChanged.connect(self._on_config_changed_signal)
        self._support_auto_mode = False
        self._windows_os = False
        self._current_mode = MODE_MOUSE
        self._main_window = main_window
        self._active_device = None
        self._current_screen_heigth = 600

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, cfg):
        self._config = cfg

    @property
    def current_mode(self):
        return self._current_mode

    @current_mode.setter
    def current_mode(self, mode):
        self._current_mode = mode

    @property
    def windows_os(self):
        return self._windows_os

    @windows_os.setter
    def windows_os(self, wo):
        self._windows_os = wo

    @property
    def main_window(self):
        return self._main_window

    @main_window.setter
    def main_window(self, mw):
        self._main_window = mw

    @property
    def ui(self):
        return self._ui

    @ui.setter
    def ui(self, uid):
        self._ui = uid

    @property
    def support_auto_mode(self):
        return self._support_auto_mode

    @support_auto_mode.setter
    def support_auto_mode(self, sam):
        self._support_auto_mode = sam

    @property
    def screen_index(self):
        return self._screen_index

    @screen_index.setter
    def screen_index(self, scr):
        self._screen_index = scr

    @property
    def compatible_modes(self):
        return self._compatible_modes

    @compatible_modes.setter
    def compatible_modes(self, modes):
        self._compatible_modes = modes

    @property
    def log_function(self):
        return self._log_function

    @log_function.setter
    def log_function(self, func):
        self._log_function = func

    @property
    def overlay_window(self):
        return self._spotlight_overlay_window

    @overlay_window.setter
    def overlay_window(self, window):
        self._spotlight_overlay_window = window

    @property
    def info_overlay(self):
        return self._info_overlay_window

    @info_overlay.setter
    def info_overlay(self, window):
        self._info_overlay_window = window

    @property
    def show_info_function(self):
        return self._show_info_function

    @show_info_function.setter
    def show_info_function(self, func):
        self._show_info_function = func

    @property
    def current_screen_height(self):
        return self._current_screen_heigth

    @current_screen_height.setter
    def current_screen_height(self, h):
        self._current_screen_heigth = h

    def _on_config_changed(self, key, value):
        # Apenas emite o signal, não mexe direto na UI
        self.configChanged.emit(key, value)

    def _on_config_changed_signal(self, key, value):
        ui = self._main_window
        if not ui:
            return

        if key == "spotlight_shape":
            ui.spotlight_shape.setCurrentText(value)
        elif key == "spotlight_size":
            ui.spotlight_size.setValue(value)
        elif key == "spotlight_shade":
            ui.spotlight_shade.setChecked(value)
        elif key == "spotlight_border":
            ui.spotlight_border.setChecked(value)

        elif key == "magnify_shape":
            ui.magnify_shape.setCurrentText(value)
        elif key == "magnify_size":
            ui.magnify_size.setValue(value)
        elif key == "magnify_border":
            ui.magnify_border.setChecked(value)
        elif key == "magnify_zoom":
            ui.magnify_zoom.setValue(value)

        elif key == "laser_dot_size":
            ui.laser_dot_size.setValue(value)
        elif key == "laser_color_index":
            ui.laser_color.setCurrentIndex(value)
        elif key == "laser_opacity":
            ui.laser_opacity.setValue(value)
        elif key == "laser_reflection":
            ui.laser_reflection.setChecked(value)

        elif key == "marker_width":
            ui.marker_width.setValue(value)
        elif key == "marker_color_index":
            ui.marker_color.setCurrentIndex(value)
        elif key == "marker_opacity":
            ui.marker_opacity.setValue(value)

        elif key == "shade_color_index":
            ui.shade_color.setCurrentIndex(value)
        elif key == "shade_opacity":
            ui.shade_opacity.setValue(value)

        elif key == "border_color_index":
            ui.border_color.setCurrentIndex(value)
        elif key == "border_opacity":
            ui.border_opacity.setValue(value)
        elif key == "border_width":
            ui.border_width.setValue(value)

        elif key == "general_always_capture":
            ui.general_always_capture_screenshot.setChecked(value)
        elif key == "general_auto_mode":
            ui.general_enable_auto_mode.setChecked(value)

    def set_active_device(self, device):
        if self._active_device == device:
            return

        # Para dispositivo ativo anterior
        if self._active_device:
            self._active_device.stop()

        self._active_device = device

        if device:
            device.ensure_monitoring()

    def log(self, message):
        if self._log_function:
            self._log_function(message)

    def show_info(self, message):
        if self._show_info_function:
            self._show_info_function(message)

    def change_screen(self, screen_index):
        if screen_index != self.screen_index:
            self._screen_index = screen_index
            screen = QGuiApplication.screens()[screen_index]
            self._current_screen_heigth = screen.size().height()
            if self._change_screen_function:
                self._change_screen_function(screen_index)
