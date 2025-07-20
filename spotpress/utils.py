import enum
import os
import getpass
import subprocess
from spotpress.qtcompat import (
    QColor,
    QImage,
    QPainter,
    QGuiApplication,
    QRect,
    QPixmap,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QGraphicsBlurEffect,
    Qt_Color_Transparent,
)


import uinput

try:
    import qdarktheme

    DARK_MODE_AVAILABLE = True
except:
    DARK_MODE_AVAILABLE = False


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


class Mode(enum.Enum):
    MOUSE = MODE_MOUSE
    SPOTLIGHT = MODE_SPOTLIGHT
    LASER = MODE_LASER
    PEN = MODE_PEN
    MAG_GLASS = MODE_MAG_GLASS


MODES_CMD_LINE_MAP = {
    "mouse": 0,
    "0": 0,
    "spotlight": 1,
    "1": 1,
    "laser": 2,
    "2": 2,
    "pen": 3,
    "3": 3,
    "mag_glass": 4,
    "4": 4,
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
    # Cores intermediárias: vibrantes mas não berrantes
    (QColor(173, 99, 255), "Soft Violet"),
    (QColor(0, 191, 255), "Deep Sky Blue"),
    (QColor(144, 238, 144), "Light Green"),
    (QColor(255, 140, 105), "Coral"),
    (QColor(160, 160, 255), "Periwinkle"),
    (QColor(255, 120, 203), "Medium Pink"),
    (QColor(100, 200, 200), "Dusty Teal"),
    (QColor(180, 130, 255), "Lilac"),
    (QColor(255, 200, 100), "Amber"),
    (QColor(120, 220, 120), "Spring Green"),
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


CONFIG_PATH = os.path.expanduser(
    os.path.join("~", ".config", "spotpress", "config.ini")
)

ICON_FILE = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "spotpress.png"
)


SOCKET_NAME = f"spotpress_socket_{getpass.getuser()}"


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
    return QImage(
        data, pil_img.width, pil_img.height, QImage.Format_RGBA8888  # pyright: ignore
    )


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


def set_debug_border(widget):
    widget.setStyleSheet("border: 1px solid blue;")
    if hasattr(widget, "layout") and widget.layout():
        layout = widget.layout()
        for i in range(layout.count()):
            item = layout.itemAt(i)
            child = item.widget()
            if child:
                set_debug_border(child)


def apply_blur(pixmap: QPixmap, radius: float = 5.0) -> QPixmap:

    # Configura cena gráfica
    scene = QGraphicsScene()
    item = QGraphicsPixmapItem(pixmap)
    blur = QGraphicsBlurEffect()
    blur.setBlurRadius(radius)
    item.setGraphicsEffect(blur)
    scene.addItem(item)

    # Renderiza o resultado
    result = QPixmap(pixmap.size())
    result.fill(Qt_Color_Transparent)
    painter = QPainter(result)
    scene.render(painter)
    painter.end()

    return result


def get_screen_geometry(screen_index):
    _, geometry = get_screen_and_geometry(screen_index)
    return geometry


def capture_monitor_screenshot(screen_index):
    screen, _ = get_screen_and_geometry(screen_index)
    screenshot = screen.grabWindow(0)  # pyright: ignore
    return screenshot.toImage()


def load_dark_theme(app):
    if DARK_MODE_AVAILABLE:
        app.setStyleSheet(qdarktheme.load_stylesheet())


WINDOW_HINTS = [
    {"class": "libreoffice-impress", "name": "Impress"},
    {"class": "soffice", "name": "Impress"},
    {"class": "onlyoffice", "name": "pptx|ppt|odp|pdf"},
    {"class": "wpsoffice", "name": "WPS Office"},
    {"class": "okular", "name": "Okular"},
    {"class": "evince", "name": "Apresentação"},
    {"class": "atril", "name": "pdf"},
    {"class": "google-chrome", "name": "Apresentações Google"},
    {"class": "firefox", "name": "Google Slides"},
]

PRESENTATION_SHORTCUTS = {
    "libreoffice-impress": [uinput.KEY_LEFTSHIFT, uinput.KEY_F5],
    "soffice": [uinput.KEY_LEFTSHIFT, uinput.KEY_F5],
    "onlyoffice": [uinput.KEY_LEFTCTRL, uinput.KEY_F5],
    "wpsoffice": [uinput.KEY_LEFTCTRL, uinput.KEY_F5],
    "google-chrome": [uinput.KEY_LEFTCTRL, uinput.KEY_F5],
    "atril": uinput.KEY_F5,
    "evince": uinput.KEY_F5,
    "okular": [uinput.KEY_LEFTCTRL, uinput.KEY_LEFTSHIFT, uinput.KEY_P],
    # Adicione outros conforme necessário
}


def get_open_window_classes():
    open_classes = set()
    for hint in WINDOW_HINTS:
        try:
            result = subprocess.run(
                ["xdotool", "search", "--class", hint["class"]],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                open_classes.add(hint["class"].lower())
        except Exception:
            pass
    return open_classes


def get_keychord_for_presentation_program():
    open_classes = get_open_window_classes()
    for app_class, keys in PRESENTATION_SHORTCUTS.items():
        if app_class.lower() in open_classes:
            return keys
    # Padrão se nada identificado: Shift+F5
    return [uinput.KEY_LEFTSHIFT, uinput.KEY_F5]


def get_window_property(window_id, prop):
    try:
        output = subprocess.check_output(["xprop", "-id", window_id, prop], text=True)
        return output
    except subprocess.CalledProcessError:
        return ""


def parse_xprop_value(output):
    if "=" in output:
        return output.split("=", 1)[1].strip().strip('"')
    return ""


def find_best_window(wids, class_name):
    # Encontra o item do WINDOW_HINTS para a classe dada
    hint = next((h for h in WINDOW_HINTS if h.get("class") == class_name), None)
    if not hint:
        return None

    name_keywords = hint.get("name", "")
    keywords = [k.strip().lower() for k in name_keywords.split("|")]

    for wid in wids:
        wm_name = get_window_property(wid, "_NET_WM_NAME") or get_window_property(
            wid, "WM_NAME"
        )
        name_value = parse_xprop_value(wm_name)

        # Verifica se alguma keyword está contida no nome
        if any(keyword in name_value for keyword in keywords):
            return wid


def refocus_presentation_window():
    for hint in WINDOW_HINTS:
        try:
            class_name = hint["class"]
            cmd = ["xdotool", "search"]
            cmd += ["--class", class_name]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                wids = result.stdout.strip().split("\n")
                wid = find_best_window(wids, class_name)
                if wid is not None:
                    subprocess.run(["xdotool", "windowactivate", wid])
                    return True  # PARA aqui, janela ativada
        except Exception as e:
            print(f"[WARN] Failed to focus {hint}: {e}")
    return False  # Nenhuma janela encontrada
