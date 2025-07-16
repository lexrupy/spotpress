from spotpress.utils import MODE_MOUSE, ObservableDict

from spotpress.qtcompat import QObject, pyqtSignal


class AppContext(QObject):
    configChanged = pyqtSignal(str, object)  # chave, valor
    currentModeChanged = pyqtSignal(int)

    def __init__(
        self,
        screen_index=0,
        log_function=None,
        overlay_window=None,
        show_info_function=None,
        show_overlay_function=None,
        hide_overlay_function=None,
        active_device_changed_function=None,
        main_window=None,
        debug_mode=False,
    ):
        super().__init__()
        self._debug_mode = debug_mode
        self._screen_index = screen_index
        self._log_function = log_function
        self._spotlight_overlay_window = overlay_window
        self._info_overlay_window = None
        self._show_info_function = show_info_function
        self._show_overlay_function = show_overlay_function
        self._hide_overlay_function = hide_overlay_function
        self._active_device_changed_function = active_device_changed_function
        self._compatible_modes = []
        self._config = ObservableDict(callback=self._on_config_changed)
        self._support_auto_mode = False
        self._windows_os = False
        self._current_mode = MODE_MOUSE
        self._main_window = main_window
        self._active_device = None
        self._current_screen_heigth = 600
        self._ui_ready = False
        self._device_monitor = None

        self.configChanged.connect(self._on_config_changed_signal)

    @property
    def debug_mode(self):
        return self._debug_mode

    @debug_mode.setter
    def debug_mode(self, dbg):
        self._debug_mode = dbg

    @property
    def active_device_changed_function(self):
        return self._active_device_changed_function

    @active_device_changed_function.setter
    def active_device_changed_function(self, func):
        self._active_device_changed_function = func

    @property
    def device_monitor(self):
        return self._device_monitor

    @device_monitor.setter
    def device_monitor(self, dm):
        self._device_monitor = dm

    @property
    def ui_ready(self):
        return self._ui_ready

    @ui_ready.setter
    def ui_ready(self, rdy):
        self._ui_ready = rdy

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
        if mode != self._current_mode:
            self._current_mode = mode
            self.currentModeChanged.emit(mode)

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
        if self._main_window:
            self._main_window.preferences_tab.update_modes_list_from_context()

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

        pt = ui.preferences_tab

        if key == "spotlight_shape":
            pt.spotlight_shape.setCurrentText(value)
        elif key == "spotlight_size":
            pt.spotlight_size.setValue(value)
        elif key == "spotlight_background_mode":
            pt.spotlight_bg_mode.setCurrentIndex(value)
        elif key == "spotlight_border":
            pt.spotlight_border.setChecked(value)

        elif key == "magnify_shape":
            pt.magnify_shape.setCurrentText(value)
        elif key == "magnify_size":
            pt.magnify_size.setValue(value)
        elif key == "magnify_border":
            pt.magnify_border.setChecked(value)
        elif key == "magnify_zoom":
            pt.magnify_zoom.setValue(value)
        elif key == "magnify_background_mode":
            pt.magnify_bg_mode.setCurrentIndex(value)

        elif key == "laser_dot_size":
            pt.laser_dot_size.setValue(value)
        elif key == "laser_color_index":
            pt.laser_color.setCurrentIndex(value)
        elif key == "laser_opacity":
            pt.laser_opacity.setValue(value)
        elif key == "laser_reflection":
            pt.laser_reflection.setChecked(value)

        elif key == "marker_width":
            pt.marker_width.setValue(value)
        elif key == "marker_color_index":
            pt.marker_color.setCurrentIndex(value)
        elif key == "marker_opacity":
            pt.marker_opacity.setValue(value)

        elif key == "shade_color_index":
            pt.shade_color.setCurrentIndex(value)
        elif key == "shade_opacity":
            pt.shade_opacity.setValue(value)

        elif key == "border_color_index":
            pt.border_color.setCurrentIndex(value)
        elif key == "border_opacity":
            pt.border_opacity.setValue(value)
        elif key == "border_width":
            pt.border_width.setValue(value)

        elif key == "general_always_capture":
            pt.general_always_capture_screenshot.setChecked(value)
        elif key == "general_auto_mode":
            pt.general_enable_auto_mode.setChecked(value)

    def set_active_device(self, device):
        if self._active_device == device:
            return

        # Para o anterior
        if self._active_device:
            self._active_device.stop()

        self._active_device = device

        if device:
            device.ensure_monitoring()
            self.compatible_modes = sorted(getattr(device._ctx, "compatible_modes", []))
            if self._active_device_changed_function is not None:
                self._active_device_changed_function(device)
        else:
            self.compatible_modes = []

    @property
    def active_device(self):
        return self._active_device

    def log(self, message):
        if self._log_function:
            self._log_function(message)

    def show_info(self, message):
        if self._show_info_function:
            self._show_info_function(message)

    def show_overlay(self):
        if self._show_overlay_function:
            self._show_overlay_function()

    def hide_overlay(self):
        if self._hide_overlay_function:
            self._hide_overlay_function()
