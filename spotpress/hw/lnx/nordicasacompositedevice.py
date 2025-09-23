import time
import uinput
import threading
import evdev.ecodes as ec

from spotpress.utils import (
    MODE_LASER,
    MODE_MOUSE,
    MODE_SPOTLIGHT,
    MODE_MAG_GLASS,
    MODE_PEN,
    get_keychord_for_presentation_program,
    refocus_presentation_window,
)
from spotpress.hw.lnx.pointerdevice import PointerDevice


class ASACompositeDevicePointer(PointerDevice):
    VENDOR_ID = 0x1915
    PRODUCT_ID = 0x1025
    # PRODUCT_DESCRIPTION = "123 COM Smart Control"
    DOUBLE_CLICK_INTERVAL = 0.3

    def __init__(self, app_ctx, hidraw_path):
        super().__init__(app_ctx=app_ctx, hidraw_path=hidraw_path)
        self.compatible_modes = [
            MODE_MOUSE,
            MODE_SPOTLIGHT,
            MODE_LASER,
            MODE_PEN,
            MODE_MAG_GLASS,
        ]

        self._ctx.support_auto_mode = True
        self._lock = threading.Lock()
        self._is_mouse_down = False
        self._auto_mode_timer = None
        self._auto_mode_timeout = 1.0
        self._last_mouse_movement = 0
        self._last_mouse_move_action = 0
        self._mouse_down_time = 0
        self._was_last_esc = True

    def start_hidraw_monitoring(self):
        # No Hidraw monitoring needed in this device
        pass

    def _reset_auto_mode_timer(self):
        if self._auto_mode_timer is not None:
            self._auto_mode_timer.cancel()

        def timeout_callback():
            self.log("[AUTO] Timer expirou, executando MOUSE_STOP")
            self.do_action("MOUSE_STOP")

        self._auto_mode_timer = threading.Timer(
            self._auto_mode_timeout, timeout_callback
        )
        self._auto_mode_timer.start()

    def stop(self):
        super().stop()
        if self._auto_mode_timer:
            self._auto_mode_timer.cancel()
            self._auto_mode_timer = None

    def do_action(self, button):
        if self._ctx.active_device != self:
            return

        ow = self._ctx.overlay_window
        current_mode = self._ctx.current_mode
        normal_mode = current_mode == MODE_MOUSE or not ow.is_overlay_actually_visible()

        if button != "MOUSE_MOVE":
            self.log(f"DO_ACTION -> {button}")

        match button:
            case "KEY_COMPOSE+RELEASE":
                ow.switch_mode()
            case "KEY_HOMEPAGE+RELEASE":
                ow.set_auto_mode(not ow.auto_mode_enabled())
            case "MOUSE_MOVE":
                if ow.auto_mode_enabled() and not ow.is_overlay_actually_visible():
                    now = time.time()
                    if now - self._last_mouse_move_action > 1.2:
                        self._last_mouse_move_action = now
                        self.log(f"DO ACTION -> {button}")
                        self._ctx.show_overlay()
            case "MOUSE_STOP":
                if ow.auto_mode_enabled() and ow.is_overlay_actually_visible():
                    self._ctx.hide_overlay()
            case "KEY_PAGEUP+RELEASE":
                if normal_mode:
                    self.emit_key_press(uinput.KEY_PAGEUP)
            case "KEY_PAGEDOWN+RELEASE":
                if normal_mode:
                    self.emit_key_press(uinput.KEY_PAGEDOWN)
            case "KEY_UP+PRESS" | "KEY_UP+REPEAT":
                if ow.is_overlay_actually_visible():
                    if current_mode == MODE_LASER:
                        ow.change_laser_size(+1)
                    if current_mode in [MODE_SPOTLIGHT, MODE_MAG_GLASS]:
                        ow.change_spot_radius(+2)
            case "KEY_DOWN+PRESS" | "KEY_DOWN+REPEAT":
                if current_mode == MODE_LASER:
                    ow.change_laser_size(-1)
                if current_mode in [MODE_SPOTLIGHT, MODE_MAG_GLASS]:
                    ow.change_spot_radius(-2)
            case "KEY_LEFT+REPEAT":
                if normal_mode:
                    self.emit_key_press(uinput.KEY_PAGEUP)
            case "KEY_LEFT+PRESS":
                if normal_mode:
                    self.emit_key_press(uinput.KEY_PAGEUP)
                elif ow.is_overlay_actually_visible():
                    if current_mode == MODE_MAG_GLASS:
                        ow.zoom(-1)
                    elif current_mode == MODE_LASER:
                        ow.next_laser_color(-1)
                    elif current_mode == MODE_SPOTLIGHT:
                        ow.next_overlay_color(-1)
                    elif current_mode == MODE_PEN:
                        ow.next_pen_color(-1)
            case "KEY_RIGHT+PRESS":
                if normal_mode:
                    self.emit_key_press(uinput.KEY_PAGEDOWN)
                elif ow.is_overlay_actually_visible():
                    if current_mode == MODE_MAG_GLASS:
                        ow.zoom()
                    elif current_mode == MODE_LASER:
                        ow.next_laser_color()
                    elif current_mode == MODE_SPOTLIGHT:
                        ow.next_overlay_color()
                    elif current_mode == MODE_PEN:
                        ow.next_pen_color()
            case "KEY_RIGHT+REPEAT":
                if normal_mode:
                    self.emit_key_press(uinput.KEY_PAGEDOWN)
            case "KEY_PLAYPAUSE+RELEASE":
                if normal_mode:
                    if self._was_last_esc:
                        keys = get_keychord_for_presentation_program()
                        if self._ctx.debug_mode:
                            self.log_key(keys)
                        self.emit_key_chord(keys)
                        self._was_last_esc = False
                    else:
                        self.emit_key_press(uinput.KEY_ESC)
                        self._was_last_esc = True
                        refocus_presentation_window()
            case "KEY_BACKSPACE+RELEASE":
                if current_mode == MODE_PEN:
                    ow.clear_drawing()

    @classmethod
    def device_filter(cls, device_info, udevadm_output):
        # Only InterfaceProtocol 01 returns relevant info
        if "hidraw" in device_info:
            return 'attrs{binterfaceprotocol}=="01"' in udevadm_output
        return True

    def handle_event(self, event):
        if self._ctx.active_device != self:
            return
        directions = {0: "RELEASE", 1: "PRESS", 2: "REPEAT"}
        ow = self._ctx.overlay_window
        if event.type == ec.EV_REL:  # Movimento de Mouse
            self._last_mouse_movement = time.time()
            self._reset_auto_mode_timer()
            if self._last_mouse_movement - self._mouse_down_time > 1.5:
                self._ctx.ui.emit((event.type, event.code), event.value)
                self.do_action("MOUSE_MOVE")

        elif event.type == ec.EV_KEY:
            button = None
            match event.code:
                case ec.BTN_LEFT:
                    if self._ctx.current_mode in [MODE_MOUSE, MODE_PEN]:
                        self._ctx.ui.emit((event.type, event.code), event.value)
                    else:
                        if event.value == 1:
                            self._is_mouse_down = True
                            self._mouse_down_time = time.time()
                            if ow and ow.is_overlay_actually_visible():
                                self.do_action("BTN_LEFT")
                        else:
                            self._is_mouse_down = False

                case ec.KEY_VOLUMEUP | ec.KEY_VOLUMEDOWN | ec.KEY_MUTE:

                    self._ctx.ui.emit((event.type, event.code), event.value)

                case _:
                    button = ec.bytype[event.type][event.code]

            if button is not None:
                self.do_action(f"{button}+{directions[event.value]}")
