import os
import threading
import subprocess
import select
import glob
import evdev
from evdev import ecodes as ec

from spotpress.hw.base_pointer_device import BasePointerDevice


class PointerDevice(BasePointerDevice):
    VENDOR_ID = None
    PRODUCT_ID = None
    IS_VIRTUAL = False

    def __init__(self, app_ctx, hidraw_path):
        self._is_virtual = False
        self._thread_set = set()
        self.path = hidraw_path
        self._monitor_lock = threading.Lock()
        self._stop_event_thread = threading.Event()
        self._stop_hidraw_thread = threading.Event()
        self._event_thread = None
        self._hidraw_thread = None
        self._ctx = app_ctx
        self._device_name = None
        self._known_paths = set()

        self.add_known_path(hidraw_path)
        for device in self.find_all_event_devices_for_known():
            self.add_known_path(device.path)

    @classmethod
    def is_virtual(cls):
        return cls.IS_VIRTUAL

    def is_virtual_device(self):
        return self.__class__.IS_VIRTUAL

    def _start_thread(self, name, target):
        if name in self._thread_set:
            self.log(f"* Tentativa de Criar Thread já existente com mesmo nome: {name}")
            return
        t = threading.Thread(target=target, daemon=True, name=name)
        t.start()
        self._thread_set.add(name)
        return t

    def start_event_blocking(self):
        if not self._event_thread or not self._event_thread.is_alive():
            self._stop_event_thread.clear()
            devs = self.find_all_event_devices_for_known()
            if devs:
                self._event_thread = self._start_thread(
                    "event_thread", lambda: self.read_input_events(devs)
                )
            else:
                self.log(
                    "* Nenhum dispositivo de entrada conhecido encontrado para bloquear."
                )

    def find_all_event_devices_for_known(self):
        devices = []
        for path in glob.glob("/dev/input/event*"):
            if self.__class__.is_known_device(path):
                try:
                    devices.append(evdev.InputDevice(path))
                    # self._ctx.log(f"* Encontrado device de entrada: {path}")
                except Exception as e:
                    self.log(f"* Erro ao acessar {path}: {e}")
        return devices

    def monitor(self):
        self.start_event_blocking()
        self.start_hidraw_monitoring()

    def start_hidraw_monitoring(self):
        if self._hidraw_thread and self._hidraw_thread.is_alive():
            return

        self._stop_hidraw_thread.clear()

        def run():
            self.log(f"* Device monitorado: {self.path}")
            try:
                if os.path.exists(self.path):
                    with open(self.path, "rb") as f:
                        for pacote in self.read_pacotes_completos(f):
                            self.processa_pacote_hid(pacote)
            except PermissionError:
                self.log(
                    f"* Sem permissão para acessar {self.path} (tente ajustar udev ou rodar com sudo)"
                )
            except KeyboardInterrupt:
                self.log(f"\nFinalizando monitoramento de {self.path}")
            except OSError as e:
                if e.errno == 5:  # Input/output error
                    self.log("- Dispositivo desconectado ou erro de I/O")
                else:
                    self.log(f"* Erro em {self.path}: {e}")

            except Exception as e:
                self.log(f"*  Erro em {self.path}: {e}")
            self.log(f"Finalizou thread hidraw ({self.path})")

        self._hidraw_thread = self._start_thread("hidraw_thread", run)

    def stop_hidraw_monitoring(self):
        self._stop_hidraw_thread.set()
        if self._hidraw_thread and self._hidraw_thread.is_alive():
            self._hidraw_thread.join(timeout=1)
        self._hidraw_thread = None

    def stop_event_blocking(self):
        self._stop_event_thread.set()
        if self._event_thread and self._event_thread.is_alive():
            self._event_thread.join(timeout=1)
        self._event_thread = None

    def stop(self):
        self.stop_event_blocking()
        self.stop_hidraw_monitoring()

    def ensure_monitoring(self):
        with self._monitor_lock:
            need_start = False

            if (
                not hasattr(self, "_event_thread")
                or not self._event_thread
                or not self._event_thread.is_alive()
            ):
                need_start = True

            if (
                not hasattr(self, "_hidraw_thread")
                or not self._hidraw_thread
                or not self._hidraw_thread.is_alive()
            ):
                need_start = True

            if need_start:
                self.log(f"* Monitorando {self.display_name()}")
                self.monitor()

    def known_path(self, path):
        return path is not None and path in self._known_paths

    def cleanup_known_paths(self):
        self._known_paths = set([p for p in self._known_paths if os.path.exists(p)])

    def add_known_path(self, path):
        self.cleanup_known_paths()
        if path and path not in self._known_paths and os.path.exists(path):
            self._known_paths.add(path)
            return True
        return False

    def remove_known_path(self, path):
        if path in self._known_paths:
            self.log(f"- Removendo path {path} de {self.__class__.__name__}")
            self._known_paths.remove(path)
        return len(self._known_paths) == 0  # retorna True se ficou vazio

    def __str__(self):
        return self.display_name()

    def display_name(self):
        desc = getattr(self.__class__, "PRODUCT_DESCRIPTION", None)
        if desc:
            return desc

        try:
            devname = os.path.basename(self.path or "")
            if devname.startswith("event"):
                path = f"/sys/class/input/{devname}/device/name"
                if os.path.exists(path):
                    return open(path).read().strip()

            elif devname.startswith("hidraw"):
                path = f"/sys/class/hidraw/{devname}/device/uevent"
                if os.path.exists(path):
                    with open(path) as f:
                        for line in f:
                            if line.startswith("HID_NAME="):
                                return line.strip().split("=", 1)[1]
        except Exception as e:
            self.log(f"Erro ao obter nome: {e}")

        return self.__class__.__name__  # Fallback genérico

    @classmethod
    def device_filter(cls, device_info, udevadm_output) -> bool:
        return True

    @classmethod
    def is_known_device(cls, device_info):
        try:
            output = subprocess.check_output(
                ["udevadm", "info", "-a", "-n", device_info], text=True
            ).lower()
            vid = f"{cls.VENDOR_ID:04x}"
            pid = f"{cls.PRODUCT_ID:04x}"
            known_device = vid in output and pid in output
            return known_device and cls.device_filter(device_info, output)
        except subprocess.CalledProcessError:
            return False

    def emit_key_press(self, key):
        if isinstance(key, list):
            self.emit_key_chord(key)
            return
        ui = self._ctx.ui
        ui.emit(key, 1)  # Pressiona
        ui.emit(key, 0)  # Solta

    def emit_key_chord(self, keys):
        ui = self._ctx.ui
        ui = self._ctx.ui
        # Pressiona todas
        for key in keys:
            ui.emit(key, 1)
        # Solta todas em ordem inversa
        for key in reversed(keys):
            ui.emit(key, 0)

    def handle_event(self, event):
        pass

    def read_input_events(self, devices):
        while not self._stop_event_thread.is_set():
            fd_para_dev = {}
            for dev in devices:
                try:
                    dev.grab()
                    fd_para_dev[dev.fd] = dev
                    self.log(f"* Device monitorado: {dev.path}")
                except Exception as e:
                    self.log(
                        f"* Erro ao monitorar dispositivo {dev.path}: {e}. Tente executar como root ou ajuste as regras udev."
                    )
            try:
                while not self._stop_event_thread.is_set():
                    r, _, _ = select.select(fd_para_dev, [], [], 0.1)
                    for fd in r:
                        dev = fd_para_dev.get(fd)
                        if dev is None:
                            continue
                        try:
                            for event in dev.read():
                                self.handle_event(event)

                        except OSError as e:
                            if e.errno == 19:  # No such device
                                self.log(f"- Dispositivo desconectado: {dev.path}")
                                # Remove dispositivo da lista para não monitorar mais
                                fd_para_dev.pop(fd, None)
                                try:
                                    dev.ungrab()
                                except Exception:
                                    pass
                                # Opcional: se não há mais dispositivos, pode encerrar ou esperar
                                if not fd_para_dev:
                                    self.log(
                                        "* Nenhum dispositivo restante para monitorar. Encerrando thread."
                                    )
                                    return
                            else:
                                raise

            except KeyboardInterrupt:
                self.log("\n* Encerrando monitoramento.")
            finally:
                for dev in devices:
                    try:
                        dev.ungrab()
                        dev.close()
                    except Exception:
                        pass

    def read_pacotes_completos(self, f):
        # raise NotImplementedError()
        yield []

    def processa_pacote_hid(self, data):
        # raise NotImplementedError()
        pass

    def log(self, message):
        self._ctx.log(f"[{self.__class__.__name__}] - {message}")

    def log_key(self, ev):
        all_keys = ec.KEY | ec.BTN
        if ev.value == 1:
            direction = "down"
        else:
            direction = "up"
        self.log(f"{all_keys[ev.code]} - {direction}")
