import time
import threading
from pywinusb import hid

from spotpress.genericvrbox_win import GenericVRBoxPointer
from spotpress.baseusorangedotai_win import BaseusOrangeDotAI
from spotpress.virtualdevice_win import VirtualPointer

DEVICE_CLASSES = {
    BaseusOrangeDotAI,
    GenericVRBoxPointer,
    VirtualPointer
}


class DeviceMonitor:
    def __init__(self, context):
        self._ctx = context
        self._monitored_devices = {}
        self._hotplug_callbacks = []
        self._known_paths = set()

        # TODO: Substituir uinput por equivalente no Windows
        self._ctx.ui = None  # Placeholder, pois uinput não roda no Windows

    def start_monitoring(self):
        self.monitor_usb_hotplug()

    def add_monitored_device(self, cls, hid_device):
        if cls not in self._monitored_devices:
            dev = cls(app_ctx=self._ctx, hid_device=hid_device)
            threading.Thread(target=dev.monitor, daemon=True).start()
            self._monitored_devices[cls] = dev
            self._notify_callbacks()
            self._ctx.log(f"Adicionando dispositivo: {cls.__name__}")
        else:
            self._ctx.log(f"Dispositivo {cls.__name__} já monitorado.")

    def remove_monitored_device(self, cls):
        if cls in self._monitored_devices:
            dev = self._monitored_devices[cls]
            dev.stop()
            del self._monitored_devices[cls]
            self._notify_callbacks()
            self._ctx.log(f"Dispositivo {cls.__name__} removido.")

    def get_monitored_devices(self):
        return list(self._monitored_devices.values())

    def register_hotplug_callback(self, callback):
        self._hotplug_callbacks.append(callback)

    def _notify_callbacks(self):
        for cb in self._hotplug_callbacks:
            cb()

    def monitor_usb_hotplug(self):
        def poll_loop():
            while True:
                all_devices = hid.HidDeviceFilter().get_devices()
                for dev in all_devices:
                    path = dev.device_path
                    if path in self._known_paths:
                        continue

                    for cls in DEVICE_CLASSES:
                        if cls.is_known_device(dev):
                            self._ctx.log(f"+ Novo dispositivo detectado: {dev.product_name}")
                            self._known_paths.add(path)
                            self.add_monitored_device(cls, dev)

                # Checagem de desconexão
                current_paths = set(d.device_path for d in hid.HidDeviceFilter().get_devices())
                removed_paths = self._known_paths - current_paths
                for removed in removed_paths:
                    self._ctx.log(f"- Dispositivo removido: {removed}")
                    self._known_paths.remove(removed)
                    # Opcional: remover da lista monitorada

                time.sleep(2)

        threading.Thread(target=poll_loop, daemon=True).start()
