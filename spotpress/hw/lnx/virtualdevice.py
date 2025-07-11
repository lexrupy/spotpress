from spotpress.utils import (
    MODE_LASER,
    MODE_MAG_GLASS,
    MODE_MOUSE,
    MODE_SPOTLIGHT,
    MODE_PEN,
)

from spotpress.hw.lnx.pointerdevice import PointerDevice


class VirtualPointer(PointerDevice):
    VENDOR_ID = 0x0000
    PRODUCT_ID = 0x0000
    PRODUCT_DESCRIPTION = "Virtual Pointer Device"
    LONG_PRESS_INTERVAL = 0.6  # tempo mínimo para considerar pressionamento longo
    DOUBLE_CLICK_INTERVAL = 0.4  # segundos
    REPEAT_INTERVAL = 0.05
    IS_VIRTUAL = True

    def __init__(self, app_ctx, hidraw_path):
        super().__init__(app_ctx=app_ctx, hidraw_path=hidraw_path)

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
