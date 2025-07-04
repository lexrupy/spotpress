import time
import threading
from spotpress.utils import MODE_LASER, MODE_MAG_GLASS, MODE_MOUSE, MODE_SPOTLIGHT
from .pointerdevice_win import BasePointerDevice


class GenericVRBoxPointer(BasePointerDevice):
    VENDOR_ID = 0x248A
    PRODUCT_ID = 0x8266
    PRODUCT_DESCRIPTION = "Generic VR BOX Bluetooth Controller"

    LONG_PRESS_INTERVAL = 0.6
    DOUBLE_CLICK_INTERVAL = 0.4
    REPEAT_INTERVAL = 0.05

    def __init__(self, app_ctx, device):
        super().__init__(app_ctx=app_ctx, hid_device=device)
        self._button_states = {}
        self._last_click_time = {}
        self._last_release_time = {}
        self._pending_click_timers = {}
        self._lock = threading.Lock()
        self._ctx.compatible_modes = [
            MODE_MOUSE,
            MODE_SPOTLIGHT,
            MODE_LASER,
            MODE_MAG_GLASS,
        ]

    def _build_button_name(self, button, long_press=False, repeat=False):
        parts = [button]
        if repeat:
            parts.append("repeat")
        elif long_press:
            parts.append("long")
        return "+".join(parts)

    def _on_button_press(self, botao):
        if not botao:
            return
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
            "long_pressed": False,
            "repeat_active": False,
            "is_second_click": is_second_click,
        }

        def set_long_pressed():
            state["long_pressed"] = True
            timer = self._pending_click_timers.pop(botao, None)
            if timer:
                timer.cancel()
            button_name = self._build_button_name(botao, long_press=True)
            if is_second_click:
                with self._lock:
                    state["repeat_active"] = True
                self._repeat_timer(botao)
            else:
                self.executa_acao(button_name, state=1)

        long_timer = threading.Timer(self.LONG_PRESS_INTERVAL, set_long_pressed)
        long_timer.start()
        state["long_timer"] = long_timer

        self._button_states[botao] = state

        if botao in self._pending_click_timers:
            self._pending_click_timers[botao].cancel()
            del self._pending_click_timers[botao]

        if not is_second_click:

            def emitir_clique_simples():
                current_state = self._button_states.get(botao)
                if current_state is None or (
                    not current_state["long_pressed"]
                    and not current_state["repeat_active"]
                ):
                    self.executa_acao(botao, state=1)
                self._pending_click_timers.pop(botao, None)

            click_timer = threading.Timer(
                self.LONG_PRESS_INTERVAL, emitir_clique_simples
            )
            click_timer.start()
            self._pending_click_timers[botao] = click_timer

    def _repeat_timer(self, botao):
        with self._lock:
            state = self._button_states.get(botao)
            if not state or not state.get("repeat_active"):
                return
            button = self._build_button_name(botao, repeat=True)
        self.executa_acao(button, state=1)
        t = threading.Timer(self.REPEAT_INTERVAL, self._repeat_timer, args=(botao,))
        with self._lock:
            state = self._button_states.get(botao)
            if not state or not state.get("repeat_active"):
                return
            state["repeat_timer"] = t
            t.start()

    def _on_button_release(self, botao):
        state = self._button_states.pop(botao, None)
        if not state:
            return

        if "long_timer" in state:
            state["long_timer"].cancel()

        with self._lock:
            if "repeat_timer" in state:
                state["repeat_timer"].cancel()

        now = time.time()
        duration = now - state["start_time"]
        last_release = self._last_release_time.get(botao, 0)

        self._last_release_time[botao] = now

        if (
            last_release > 0
            and (now - last_release) < self.DOUBLE_CLICK_INTERVAL
            and duration < self.LONG_PRESS_INTERVAL
            and not state["long_pressed"]
        ):
            self.executa_acao(f"{botao}++", state=1)

    def handle_event(self, data):
        """
        Recebe o relatório bruto do pywinusb (data: list[int])
        """
        # data[0] é sempre o tamanho no pywinusb, ignore
        # Exemplo de análise:
        pressed_bits = data[1]  # Ex: byte 1 = bitmap de botões

        def is_pressed(bitmask, bit):
            return (bitmask & (1 << bit)) != 0

        for i in range(8):  # analisa os 8 bits
            botao = self._map_button_bit(i)
            if not botao:
                continue
            if is_pressed(pressed_bits, i):
                self._on_button_press(botao)
            else:
                self._on_button_release(botao)

    def _map_button_bit(self, bit_index):
        # Mapeie os bits para seus botões conhecidos
        return {
            0: "G1",
            1: "G2",
            2: "A",
            3: "B",
            4: "C",
            5: "D",
            # 6: "SL", 7: "SR" se necessário
        }.get(bit_index)

    def executa_acao(self, botao, state):
        ow = self._ctx.overlay_window
        current_mode = self._ctx.current_mode
        match botao:
            case "G1":
                if current_mode == MODE_MOUSE:
                    self._ctx.ui.key("pagedown")
                elif current_mode == MODE_LASER:
                    ow.next_color()
            case "G1++":
                ow.next_color()
            case "G1+long":
                self._ctx.ui.hotkey("shift", "f5")
            case "G1+repeat":
                (
                    ow.change_spot_radius(+1)
                    if current_mode == MODE_SPOTLIGHT
                    else ow.change_laser_size(+1)
                )
            case "G2":
                if current_mode == MODE_MOUSE:
                    self._ctx.ui.key("pageup")
                elif current_mode == MODE_LASER:
                    ow.next_color(-1)
            case "G2+long":
                (
                    ow.set_mouse_mode()
                    if current_mode != MODE_MOUSE
                    else ow.set_last_pointer_mode()
                )
            case "G2+repeat":
                (
                    ow.change_spot_radius(-1)
                    if current_mode == MODE_SPOTLIGHT
                    else ow.change_laser_size(-1)
                )
            case "B":
                if current_mode == MODE_MOUSE:
                    self._ctx.ui.key("b")
            case "B+long":
                ow.set_laser_mode()
            case "C":
                ow.switch_mode()
            case "C++":
                ow.switch_mode(step=-1)
            case "C+long":
                ow.set_spotlight_mode()
