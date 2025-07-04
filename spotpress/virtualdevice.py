from spotpress.utils import (
    MODE_LASER,
    MODE_MAG_GLASS,
    MODE_MOUSE,
    MODE_SPOTLIGHT,
    MODE_PEN,
)

from .pointerdevice import BasePointerDevice


class VirtualPointer(BasePointerDevice):
    VENDOR_ID = 0x0000
    PRODUCT_ID = 0x0000
    PRODUCT_DESCRIPTION = "Virtual Pointer Device"
    LONG_PRESS_INTERVAL = 0.6  # tempo mínimo para considerar pressionamento longo
    DOUBLE_CLICK_INTERVAL = 0.4  # segundos
    REPEAT_INTERVAL = 0.05

    def __init__(self, app_ctx, hidraw_path):
        super().__init__(app_ctx=app_ctx, hidraw_path=hidraw_path)

        self._ctx.compatible_modes = [
            MODE_MOUSE,
            MODE_SPOTLIGHT,
            MODE_LASER,
            MODE_MAG_GLASS,
            MODE_PEN,
        ]

    def monitor(self):
        pass

    @classmethod
    def is_known_device(cls, device_info):
        return True
