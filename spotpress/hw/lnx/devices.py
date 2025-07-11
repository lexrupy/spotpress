import os
import time
import pyudev
import glob
import threading
import uinput

from spotpress.hw.base_device_monitor import BaseDeviceMonitor
from spotpress.hw.lnx.genericvrbox import GenericVRBoxPointer
from spotpress.hw.lnx.baseusorangedotai import BaseusOrangeDotAI
from spotpress.hw.lnx.nordicasasmartcontrol import ASASmartControlPointer
from spotpress.hw.lnx.virtualdevice import VirtualPointer


DEVICE_CLASSES = {
    BaseusOrangeDotAI,
    GenericVRBoxPointer,
    ASASmartControlPointer,
}


class DeviceMonitor(BaseDeviceMonitor):
    def __init__(self, context):
        self._ctx = context
        self._ctx.device_monitor = self
        self._stop_event = threading.Event()
        self._hotplug_thread = None
        self._switch_lock = threading.Lock()
        self._switch_thread = None
        self._monitored_devices = {}
        self._hotplug_callbacks = []
        self._ctx.ui = uinput.Device(
            [
                uinput.REL_X,
                uinput.REL_Y,
                uinput.BTN_LEFT,
                uinput.BTN_RIGHT,
                uinput.KEY_B,
                uinput.KEY_PAGEUP,
                uinput.KEY_PAGEDOWN,
                uinput.KEY_ESC,
                # uinput.KEY_LEFTCTRL,
                uinput.KEY_F5,
                uinput.KEY_SPACE,
                uinput.KEY_LEFTSHIFT,
                uinput.KEY_VOLUMEUP,
                uinput.KEY_VOLUMEDOWN,
            ],
            name="Virtual Spotlight Mouse",
        )

    def start_monitoring(self):
        self.monitor_usb_hotplug()
        # Lança monitoramento dos dispositivos já conectados
        hidraws = self.find_known_devices()
        if hidraws:
            for path, cls in hidraws:
                self.add_monitored_device(cls, path)
        else:
            self._ctx.log("* Nenhum dispositivo compatível encontrado.")
        if len(self._monitored_devices) == 1:
            dev = next(iter(self._monitored_devices.values()))
            self.set_active_device(dev)

    def set_active_device(self, device):
        if self._ctx.active_device == device:
            return

        # Se já tem troca em andamento, ignora nova troca
        if self._switch_thread and self._switch_thread.is_alive():
            self._ctx.log("Troca de dispositivo já em andamento, ignorando")
            return

        old_device = self._ctx.active_device

        def switch_device():
            with self._switch_lock:
                if old_device:
                    self._ctx.log(
                        f"* Desativando: {old_device.__class__.__name__} ({old_device._known_paths})"
                    )
                    old_device.stop()
                if device:
                    self._ctx.log(
                        f"* Ativando: {device.__class__.__name__} ({device._known_paths})"
                    )
                    device.ensure_monitoring()
                    self._ctx.set_active_device(device)
                    self._ctx.compatible_modes = sorted(
                        getattr(device, "compatible_modes", [])
                    )

        self._switch_thread = threading.Thread(target=switch_device, daemon=True)
        self._switch_thread.start()

    def add_monitored_device(self, cls, path=None):
        if cls not in self._monitored_devices:
            dev = cls(app_ctx=self._ctx, hidraw_path=path)
            # threading.Thread(target=dev.monitor, daemon=True).start()
            self._monitored_devices[cls] = dev
            self._ctx.log(f"Dispositivo detectado: {cls.__name__} (path: {path})")
        else:
            dev = self._monitored_devices[cls]
            dev.add_known_path(path)
            # dev.ensure_monitoring()
            self._ctx.log(f"{cls.__name__} já conhecido. Adicionando novo path: {path}")
        self._notify_callbacks()

    def remove_monitored_device(self, dev):
        # Encontra a classe correspondente à instância
        for cls, inst in list(self._monitored_devices.items()):
            if inst is dev:
                inst.stop()
                del self._monitored_devices[cls]
                break
        self._notify_callbacks()

    def remove_monitored_device_path(self, path):
        for dev in self.get_monitored_devices():
            if path in dev._known_paths:
                self._ctx.log(f"- Removendo path {path} do dispositivo {dev}")
                # dev._known_paths.remove(path)
                dev._known_paths.discard(path)
                self._ctx.log(f"- Path {path} removido de {dev.__class__.__name__}")
                if not dev._known_paths:
                    self._ctx.log(
                        f"* Nenhum dispositivo restante para monitorar. Encerrando thread."
                    )
                    self.remove_monitored_device(dev)
                break

    def get_monitored_devices(self):
        return list(self._monitored_devices.values())

    def register_hotplug_callback(self, callback):
        self._hotplug_callbacks.append(callback)

    def _notify_callbacks(self):
        for cb in self._hotplug_callbacks:
            cb()

    def find_known_devices(self):
        devices = []
        for path in glob.glob("/dev/hidraw*"):
            for cls in DEVICE_CLASSES:
                if cls.is_known_device(path):
                    devices.append((path, cls))
        for path in glob.glob("/dev/input/*"):
            if not os.path.isfile(path):
                continue
            for cls in DEVICE_CLASSES:
                if cls.is_known_device(path):
                    devices.append((path, cls))

        devices.append(("virtual", VirtualPointer))
        return devices

    def hotplug_callback(self, action, device):
        path = device.device_node
        if not path:
            return

        if action == "add":
            if path.startswith("/dev/hidraw") or path.startswith("/dev/input"):
                for _ in range(10):  # tenta por até 1s
                    if os.path.exists(path):
                        break
                    time.sleep(0.1)
                else:
                    self._ctx.log(f"! Dispositivo {path} não apareceu após o plug.")
                    return  # não apareceu
                # time.sleep(0.8)
                for dev in self.get_monitored_devices():
                    if dev.known_path(path):
                        return  # já monitorado
                for cls in DEVICE_CLASSES:
                    if cls.is_known_device(path):
                        self._ctx.log(
                            f"+ Novo dispositivo compatível conectado: {path}"
                        )
                        self.add_monitored_device(cls, path)
        elif action == "remove":
            for dev in self.get_monitored_devices():
                self._ctx.log(
                    f"Verificando dispositivo {dev.__class__.__name__} com paths {dev._known_paths}"
                )
                if dev.known_path(path):
                    self.remove_monitored_device_path(path)

    def monitor_usb_hotplug(self):
        def monitor_loop():
            context = pyudev.Context()
            monitor = pyudev.Monitor.from_netlink(context)
            monitor.start()

            while not self._stop_event.is_set():
                device = monitor.poll(timeout=1.0)
                if device is None:
                    continue
                if device.subsystem not in ("hidraw", "input"):
                    continue
                action = device.action
                self.hotplug_callback(action, device)

        self._hotplug_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._hotplug_thread.start()

    # def monitor_usb_hotplug(self):
    #     def monitor_loop():
    #         context = pyudev.Context()
    #         monitor = pyudev.Monitor.from_netlink(context)
    #         monitor.filter_by("input")
    #         monitor.filter_by("hidraw")
    #         monitor.start()
    #
    #         for device in iter(monitor.poll, None):
    #             action = device.action  # 'add' ou 'remove'
    #             self.hotplug_callback(action, device)
    #
    #     threading.Thread(target=monitor_loop, daemon=True).start()
    def stop_monitoring(self):
        self._ctx.log("* Encerrando monitoramento de dispositivos.")
        self._stop_event.set()

        for dev in self.get_monitored_devices():
            self._ctx.log(f"- Finalizando {dev.__class__.__name__}")
            dev.stop()
        self._monitored_devices.clear()

        if self._hotplug_thread and self._hotplug_thread.is_alive():
            self._hotplug_thread.join(timeout=2.0)
            self._ctx.log("* Thread de hotplug finalizada.")
