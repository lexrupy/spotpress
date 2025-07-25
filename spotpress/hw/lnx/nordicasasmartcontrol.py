import time
import uinput
import threading
import os
import select
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


class ASASmartControlPointer(PointerDevice):
    VENDOR_ID = 0x1915
    PRODUCT_ID = 0x1001
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
        self._last_click_time = {}
        self._last_release_time = {}
        self._pending_click_timers = {}
        self._button_states = {}
        self._ultimo_botao_ativo = None
        self._lock = threading.Lock()
        self._is_mouse_down = False
        self._mouse_down_time = 0
        self._hold_states = {}
        self._was_last_esc = False
        self._rel_x_buffer = []
        self._rel_y_buffer = []
        self._rel_buffer_size = 15
        self._rel_trigger_count = 8
        self._last_movement_time = 0
        self._last_mouse_move_action = 0
        self._auto_mode_active = False
        self._auto_mode_timeout = 1.0
        self._auto_mode_timer = None
        self._last_overlay_color_change = 0
        self._button_map = {
            bytes([0, 0, 75, 0]): "PREV",
            bytes([0, 0, 78, 0]): "NEXT",
            bytes([0, 0, 8, 0]): "HGL",
            bytes([0, 0, 5, 0]): "BLACK",
            bytes([0, 0, 0, 40]): "TAB++",
            bytes([0, 0, 0, 41]): "ESC",
            bytes([0, 0, 0, 43]): "TAB",
            bytes([4, 0, 0, 43]): "TAB+repeat",
            bytes([1, 0, 0, 19]): "HGL+hold",
            bytes([1, 0, 0, 4]): "HGL+release",
            bytes([2, 0, 0, 62]): "START",
        }

    def _on_button_press(self, botao):
        now = time.time()
        last_click = self._last_click_time.get(botao, 0)
        time_since_last = now - last_click

        is_second_click = (
            0 < time_since_last < self.DOUBLE_CLICK_INTERVAL
            and self._last_release_time.get(botao, 0) > 0
        )

        self._last_click_time[botao] = now

        state = {
            "start_time": now,
            "is_second_click": is_second_click,
        }

        self._button_states[botao] = state

        # Cancelar clique simples pendente se houver
        if botao in self._pending_click_timers:
            self._pending_click_timers[botao].cancel()
            del self._pending_click_timers[botao]

    def _on_button_release(self, botao):
        state = self._button_states.pop(botao, None)
        if not state:
            return

        now = time.time()
        duration = now - state["start_time"]
        last_release = self._last_release_time.get(botao, 0)

        self._last_release_time[botao] = now

        if (
            last_release > 0
            and (now - last_release) < self.DOUBLE_CLICK_INTERVAL
            and duration < self.DOUBLE_CLICK_INTERVAL
        ):
            self.do_action(f"{botao}++")
            return

        # Agendar clique simples após DOUBLE_CLICK_INTERVAL
        def delayed_click():
            self.do_action(botao)
            if botao in self._pending_click_timers:
                del self._pending_click_timers[botao]

        t = threading.Timer(self.DOUBLE_CLICK_INTERVAL, delayed_click)
        self._pending_click_timers[botao] = t
        t.start()

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
        for t in self._pending_click_timers.values():
            t.cancel()
        self._pending_click_timers.clear()
        if self._auto_mode_timer:
            self._auto_mode_timer.cancel()
            self._auto_mode_timer = None

    def stop_hidraw_monitoring(self):
        self._stop_hidraw_thread.set()
        if self._hidraw_thread and self._hidraw_thread.is_alive():
            self._stop_hidraw_thread.set()
            self._hidraw_thread.join(
                timeout=1
            )  # espera a thread encerrar (timeout opcional)

    def read_pacotes_completos(self, f):
        fd = f.fileno()
        # Coloca o fd em não bloqueante
        os.set_blocking(fd, False)

        try:
            while not self._stop_hidraw_thread.is_set():
                rlist, _, _ = select.select([fd], [], [], 0.1)
                if fd in rlist:
                    b = f.read(8)
                    if not b:
                        # EOF ou dispositivo desconectado
                        break
                    if len(b) == 8:
                        yield bytes(b)
                else:
                    # Timeout, permite checar stop event
                    continue

        except OSError as e:
            self.log(f"[ERRO] Falha ao ler do device: {e}")
        except Exception as e:
            self.log(f"[ERRO] Exceção inesperada: {e}")

    def processa_pacote_hid(self, data):

        if not (isinstance(data, bytes) and len(data) == 8):
            return

        button = self._button_map.get(data[:4])

        status_byte = sum(data[:4])

        if status_byte == 0:
            # Somente libera o botão que estava ativo
            if self._ultimo_botao_ativo:
                self._on_button_release(self._ultimo_botao_ativo)
                self._ultimo_botao_ativo = None

            return

        if not button:
            return

        # Se for um novo botão e havia outro ativo, libera o anterior
        if self._ultimo_botao_ativo and self._ultimo_botao_ativo != button:
            self._on_button_release(self._ultimo_botao_ativo)

        # Atualiza botão atualmente ativo
        self._ultimo_botao_ativo = button

        # Processa pressão do novo botão
        self._on_button_press(button)

    def do_action(self, button):
        if self._ctx.active_device != self:
            return
        ow = self._ctx.overlay_window
        current_mode = self._ctx.current_mode
        normal_mode = current_mode == MODE_MOUSE or ow.is_overlay_actually_visible()

        if button != "MOUSE_MOVE":
            self.log(f"DO ACTION -> {button}")
        match button:
            case "TAB":
                ow.switch_mode()
            case "TAB+repeat":
                self.emit_key_chord([uinput.KEY_LEFTALT, uinput.KEY_TAB])
            case "TAB++":
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
            case "PREV":
                if current_mode == MODE_PEN:
                    ow.next_pen_color(-1)
                elif current_mode == MODE_LASER:
                    ow.next_laser_color(-1)
                elif current_mode == MODE_SPOTLIGHT:
                    ow.next_overlay_color(-1)
                elif current_mode == MODE_MAG_GLASS:
                    ow.zoom()
                elif normal_mode:
                    self.emit_key_press(uinput.KEY_PAGEUP)
            case "NEXT":
                if current_mode == MODE_PEN:
                    ow.next_pen_color()
                elif current_mode == MODE_LASER:
                    ow.next_laser_color()
                elif current_mode == MODE_SPOTLIGHT:
                    ow.next_overlay_color()
                elif current_mode == MODE_MAG_GLASS:
                    ow.zoom(-1)
                elif normal_mode:
                    self.emit_key_press(uinput.KEY_PAGEDOWN)
            case "G_UP":
                if ow.is_overlay_actually_visible():
                    if current_mode == MODE_LASER:
                        ow.change_laser_size(+1)
                    if current_mode in [MODE_SPOTLIGHT, MODE_MAG_GLASS]:
                        ow.change_spot_radius(+2)
            case "G_DOWN":
                if current_mode == MODE_LASER:
                    ow.change_laser_size(-1)
                if current_mode in [MODE_SPOTLIGHT, MODE_MAG_GLASS]:
                    ow.change_spot_radius(-2)
            case "G_LEFT":
                if ow.is_overlay_actually_visible():
                    if current_mode == MODE_MAG_GLASS:
                        ow.zoom(-1)
                    elif current_mode == MODE_LASER:
                        ow.next_laser_color()
                    elif current_mode == MODE_SPOTLIGHT:
                        now = time.time()
                        if now - self._last_overlay_color_change > 1.2:
                            self._last_overlay_color_change = now
                            ow.next_overlay_color(-1)
            case "G_RIGHT":
                if ow.is_overlay_actually_visible():
                    if current_mode == MODE_MAG_GLASS:
                        ow.zoom(+1)
                    elif current_mode == MODE_LASER:
                        ow.next_laser_color(-1)
                    elif current_mode == MODE_SPOTLIGHT:
                        now = time.time()
                        if now - self._last_overlay_color_change > 1.2:
                            self._last_overlay_color_change = now
                            ow.next_overlay_color()
            case "HGL":
                if current_mode == MODE_PEN:
                    ow.clear_drawing()
            case "HGL+hold":
                if current_mode == MODE_PEN:
                    ow.clear_drawing(all=True)
            case "HGL+release":
                ow.finish_pen_path()
            case "ESC":
                if normal_mode:
                    self.emit_key_press(uinput.KEY_ESC)
                    refocus_presentation_window()
            case "START":
                if normal_mode:
                    keys = get_keychord_for_presentation_program()
                    self.emit_key_chord(keys)
            case "NEXT++":
                ow.switch_mode()
            case "PREV++":
                ow.switch_mode(-1)

    @classmethod
    def device_filter(cls, device_info, udevadm_output):
        # Only InterfaceProtocol 01 returns relevant info
        if "hidraw" in device_info:
            return 'attrs{binterfaceprotocol}=="01"' in udevadm_output
        return True

    def log_key(self, ev):
        all_keys = ec.KEY | ec.BTN
        if ev.value == 1:
            direction = "down"
        else:
            direction = "up"
        self.log(f"{all_keys[ev.code]} - {direction}")

    def _verifica_direcao_gestos(self):
        if len(self._rel_x_buffer) == self._rel_buffer_size:
            esquerda = sum(1 for v in self._rel_x_buffer if v < 0)
            direita = sum(1 for v in self._rel_x_buffer if v > 0)

            if esquerda >= self._rel_trigger_count:
                self.do_action("G_LEFT")
                self._rel_x_buffer.clear()
                self._rel_y_buffer.clear()
                return

            if direita >= self._rel_trigger_count:
                self.do_action("G_RIGHT")
                self._rel_x_buffer.clear()
                self._rel_y_buffer.clear()
                return

        if len(self._rel_y_buffer) == self._rel_buffer_size:
            cima = sum(1 for v in self._rel_y_buffer if v < 0)
            baixo = sum(1 for v in self._rel_y_buffer if v > 0)

            if cima >= self._rel_trigger_count:
                self.do_action("G_UP")
                self._rel_x_buffer.clear()
                self._rel_y_buffer.clear()
                return

            if baixo >= self._rel_trigger_count:
                self.do_action("G_DOWN")
                self._rel_x_buffer.clear()
                self._rel_y_buffer.clear()
                return

    def handle_event(self, event):
        if self._ctx.active_device != self:
            return
        ow = self._ctx.overlay_window
        if event.type == ec.EV_REL:  # Movimento de Mouse
            self._last_movement_time = time.time()
            self._reset_auto_mode_timer()
            if self._is_mouse_down:
                if event.code == ec.REL_X:
                    self._rel_x_buffer.append(event.value)
                    if len(self._rel_x_buffer) > self._rel_buffer_size:
                        self._rel_x_buffer.pop(0)

                elif event.code == ec.REL_Y:
                    self._rel_y_buffer.append(event.value)
                    if len(self._rel_y_buffer) > self._rel_buffer_size:
                        self._rel_y_buffer.pop(0)
                # Repassa evento virtual
                if not ow.drawing:
                    self._verifica_direcao_gestos()
                else:
                    self._ctx.ui.emit((event.type, event.code), event.value)
            else:
                self._last_mouse_movement = time.time()
                if self._last_mouse_movement - self._mouse_down_time > 1.5:
                    self._ctx.ui.emit((event.type, event.code), event.value)
                    self.do_action("MOUSE_MOVE")

        elif event.type == ec.EV_KEY:
            self._last_movement_time = time.time()
            self._reset_auto_mode_timer()
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
