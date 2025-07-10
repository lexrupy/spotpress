# import mss
from PyQt5.QtGui import QColor, QImage, QGuiApplication
from PyQt5.QtCore import QRect


MODE_MOUSE = 0
MODE_SPOTLIGHT = 1
MODE_LASER = 2
MODE_PEN = 3
MODE_MAG_GLASS = 4


MODE_MAP = {
    MODE_MOUSE: "Mouse",
    MODE_SPOTLIGHT: "Spotlight",
    MODE_LASER: "Laser",
    MODE_PEN: "Marcador",
    MODE_MAG_GLASS: "Lente",
}


LASER_COLORS = [
    (QColor(255, 0, 0), "Red"),
    (QColor(0, 255, 0), "Green"),
    (QColor(0, 0, 255), "Blue"),
    (QColor(255, 0, 255), "Magenta"),
    (QColor(255, 255, 0), "Yellow"),
    (QColor(0, 255, 255), "Cyan"),
    (QColor(255, 165, 0), "Orange"),
    (QColor(255, 255, 255), "White"),
    (QColor(0, 0, 0), "Black"),
    # SE INCLUIR MAIS CORES MANTER ESTA A ÚLTIMA
    (QColor(0, 0, 0, 0), "Transparent"),
]

PEN_COLORS = LASER_COLORS[:-1]

# shade_colors = ["black", "dimgray", "gray", "lightgray", "gainsboro", "white"]
SHADE_COLORS = [
    (QColor(0, 0, 0), "Black"),
    (QColor(255, 255, 255), "White"),
]


# Reverter MODE_MAP para obter nome -> valor
MODE_NAME_TO_ID = {v: k for k, v in MODE_MAP.items()}

# Lista default com todos habilitados
DEFAULT_MODES = [(name, True) for name in MODE_NAME_TO_ID.keys()]


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        instance = cls._instances.get(cls)
        if instance is None:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return instance


class ObservableDict(dict):
    def __init__(self, *args, callback=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._callback = callback

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if self._callback:
            self._callback(key, value)


def pil_to_qimage(pil_img):
    pil_img = pil_img.convert("RGBA")
    data = pil_img.tobytes("raw", "RGBA")
    return QImage(data, pil_img.width, pil_img.height, QImage.Format_RGBA8888)


def get_screen_and_geometry(screen_index):
    app = QGuiApplication.instance()
    if not app:
        app = QGuiApplication([])

    screens = QGuiApplication.screens()
    if screen_index >= len(screens):
        screen_index = 0

    screen = screens[screen_index]
    geometry = screen.geometry()
    return screen, QRect(
        geometry.left(), geometry.top(), geometry.width(), geometry.height()
    )


def get_screen_geometry(screen_index):
    _, geometry = get_screen_and_geometry(screen_index)
    return geometry


def capture_monitor_screenshot(screen_index):
    screen, _ = get_screen_and_geometry(screen_index)
    screenshot = screen.grabWindow(0)  # pyright: ignore
    return screenshot.toImage()
