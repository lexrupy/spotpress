from spotpress.utils import (
    MODE_LASER,
    MODE_MAG_GLASS,
    MODE_MOUSE,
    MODE_SPOTLIGHT,
    MODE_PEN,
)

from spotpress.hw.lnx.pointerdevice import PointerDevice


class VirtualPointer(PointerDevice):
    PRODUCT_DESCRIPTION = "Virtual Pointer Device"
    IS_VIRTUAL = True

    def __init__(self, app_ctx, hidraw_path):
        super().__init__(app_ctx=app_ctx, hidraw_path=hidraw_path)

        self._known_paths.add("virtual")

        self.compatible_modes = [
            MODE_MOUSE,
            MODE_SPOTLIGHT,
            MODE_LASER,
            MODE_MAG_GLASS,
            MODE_PEN,
        ]

    def monitor(self):
        pass

    def ensure_monitoring(self):
        pass

    @classmethod
    def is_known_device(cls, device_info):
        return True

    def add_known_path(self, path):
        return True

    def remove_known_path(self, path):
        return True

    def find_all_event_devices_for_known(self):
        return []
