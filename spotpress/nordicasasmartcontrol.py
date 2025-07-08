import time
import uinput
import threading
import os
import evdev.ecodes as ec

from spotpress.utils import (
    MODE_LASER,
    MODE_MOUSE,
    MODE_SPOTLIGHT,
    MODE_MAG_GLASS,
)
from .pointerdevice import BasePointerDevice


class ASASmartControlPointer(BasePointerDevice):
    VENDOR_ID = 0x1915
    PRODUCT_ID = 0x1001
    # PRODUCT_DESCRIPTION = "123 COM Smart Control"
    DOUBLE_CLICK_INTERVAL = 0.3

    def __init__(self, app_ctx, hidraw_path):
        super().__init__(app_ctx=app_ctx, hidraw_path=hidraw_path)
        self._ctx.compatible_modes = [
            MODE_MOUSE,
            MODE_SPOTLIGHT,
            MODE_LASER,
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
        self._auto_mode_active = False
        self._auto_mode_timeout = 1.0
        self._auto_mode_timer = None
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
            self.executa_acao(f"{botao}++")
            return

        # Agendar clique simples após DOUBLE_CLICK_INTERVAL
        def delayed_click():
            self.executa_acao(botao)
            del self._pending_click_timers[botao]

        t = threading.Timer(self.DOUBLE_CLICK_INTERVAL, delayed_click)
        self._pending_click_timers[botao] = t
        t.start()

    def _check_auto_mode_activation(self):
        now = time.time()
        if not self._is_mouse_down:
            # Se houve movimento recente e overlay está escondido, ativa
            if (
                self._ctx.current_mode != MODE_MOUSE
                and self._ctx.overlay_window
                and not self._ctx.overlay_window.isVisible()
                and self._ctx.overlay_window.auto_mode_enabled()
                and (now - self._last_movement_time) > self._auto_mode_timeout
            ):
                self._ctx.log("[AUTO] Ativando overlay por movimento")
                self._ctx.overlay_window.show_overlay()
                self._auto_mode_active = True

    def _reset_auto_mode_timer(self):
        if self._auto_mode_timer is not None:
            self._auto_mode_timer.cancel()

        def timeout_callback():
            self._ctx.log("[AUTO] Timer expirou, executando MOUSE_STOP")
            self.executa_acao("MOUSE_STOP")

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

    def start_hidraw_monitoring(self):
        if self._hidraw_thread and self._hidraw_thread.is_alive():
            return

        def run():
            try:
                if os.path.exists(self.path):
                    with open(self.path, "rb") as f:
                        for pacote in self.read_pacotes_completos(f):
                            self.processa_pacote_hid(pacote)
            except PermissionError:
                self._ctx.log(
                    f"* Sem permissão para acessar {self.path} (tente ajustar udev ou rodar com sudo)"
                )
            except KeyboardInterrupt:
                self._ctx.log(f"\nFinalizando monitoramento de {self.path}")
            except OSError as e:
                if e.errno == 5:  # Input/output error
                    self._ctx.log("- Dispositivo desconectado ou erro de I/O")
                else:
                    self._ctx.log(f"* Erro em {self.path}: {e}")

            except Exception as e:
                self._ctx.log(f"*  Erro em {self.path}: {e}")

        # self._hidraw_thread = threading.Thread(target=run, daemon=True).start()
        self._hidraw_thread = threading.Thread(target=run, daemon=True)
        self._hidraw_thread.start()

    def stop_hidraw_monitoring(self):
        self._stop_hidraw_event.set()
        if self._hidraw_thread and self._hidraw_thread.is_alive():
            self._stop_hidraw_event.set()
            self._hidraw_thread.join(
                timeout=1
            )  # espera a thread encerrar (timeout opcional)

    def read_pacotes_completos(self, f):
        try:
            while not self._stop_event.is_set():
                b = f.read(8)
                if not b:
                    # time.sleep(0.01)
                    break
                yield bytes(b)
        except OSError as e:
            print(f"[ERRO] Falha ao ler do device: {e}")
            self._ctx.log(f"[ERRO] Falha ao ler do device: {e}")
        except Exception as e:
            print(f"[ERRO] Exceção inesperada: {e}")
            self._ctx.log(f"[ERRO] Exceção inesperada: {e}")

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

    def executa_acao(self, button):
        ow = self._ctx.overlay_window
        current_mode = self._ctx.current_mode

        if button != "MOUSE_MOVE":
            self._ctx.log(f"EXECUTA ACAO -> {button}")
        match button:
            case "TAB":
                ow.switch_mode()
            case "TAB+repeat":
                self.emit_key_chord([uinput.KEY_LEFTALT, uinput.KEY_TAB])
            case "TAB++":
                ow.set_auto_mode(not ow.auto_mode_enabled())
            case "MOUSE_MOVE":
                if ow.auto_mode_enabled() and not ow.isVisible():
                    pass
                    # ow.show_overlay()
            case "MOUSE_STOP":
                if ow.auto_mode_enabled() and ow.isVisible():
                    ow.hide_overlay()
            case "PREV":
                if not ow.isVisible() or current_mode == MODE_MOUSE:
                    self.emit_key_press(uinput.KEY_PAGEUP)
            case "NEXT":
                if not ow.isVisible() or current_mode == MODE_MOUSE:
                    self.emit_key_press(uinput.KEY_PAGEDOWN)
            case "G_UP":
                if ow.isVisible():
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
                if ow.isVisible():
                    if current_mode == MODE_MAG_GLASS:
                        ow.zoom(-1)
                    elif current_mode == MODE_LASER:
                        ow.next_laser_color()
            case "G_RIGHT":
                if ow.isVisible():
                    if current_mode == MODE_MAG_GLASS:
                        ow.zoom(+1)
                    elif current_mode == MODE_LASER:
                        ow.next_laser_color(-1)
            case "HGL+hold":
                if ow.isVisible():
                    pass
            case "HGL+release":
                ow.finish_pen_path()
            case "ESC":
                if not ow.isVisible():
                    self.emit_key_press(uinput.KEY_ESC)
            case "START":
                if not ow.isVisible():
                    self.emit_key_chord([uinput.KEY_LEFTSHIFT, uinput.KEY_F5])
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
        self._ctx.log(f"{all_keys[ev.code]} - {direction}")

    def _verifica_direcao_gestos(self):
        if len(self._rel_x_buffer) == self._rel_buffer_size:
            esquerda = sum(1 for v in self._rel_x_buffer if v < 0)
            direita = sum(1 for v in self._rel_x_buffer if v > 0)

            if esquerda >= self._rel_trigger_count:
                self.executa_acao("G_LEFT")
                self._rel_x_buffer.clear()
                self._rel_y_buffer.clear()
                return

            if direita >= self._rel_trigger_count:
                self.executa_acao("G_RIGHT")
                self._rel_x_buffer.clear()
                self._rel_y_buffer.clear()
                return

        if len(self._rel_y_buffer) == self._rel_buffer_size:
            cima = sum(1 for v in self._rel_y_buffer if v < 0)
            baixo = sum(1 for v in self._rel_y_buffer if v > 0)

            if cima >= self._rel_trigger_count:
                self.executa_acao("G_UP")
                self._rel_x_buffer.clear()
                self._rel_y_buffer.clear()
                return

            if baixo >= self._rel_trigger_count:
                self.executa_acao("G_DOWN")
                self._rel_x_buffer.clear()
                self._rel_y_buffer.clear()
                return

    def handle_event(self, event):
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
                self._verifica_direcao_gestos()
            else:
                self._last_mouse_movement = time.time()
                if self._last_mouse_movement - self._mouse_down_time > 1.5:
                    self.executa_acao("MOUSE_MOVE")
                    self._ctx.ui.emit((event.type, event.code), event.value)

        elif event.type == ec.EV_KEY:
            self._last_movement_time = time.time()
            self._reset_auto_mode_timer()
            match event.code:
                case ec.BTN_LEFT:
                    if self._ctx.current_mode == MODE_MOUSE:
                        self._ctx.ui.emit((event.type, event.code), event.value)
                    else:
                        if event.value == 1:
                            self._is_mouse_down = True
                            self._mouse_down_time = time.time()
                            if ow and ow.isVisible():
                                self.executa_acao("BTN_LEFT")
                        else:
                            self._is_mouse_down = False
