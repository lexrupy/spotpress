import os
import time
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import (
    QPainter,
    QColor,
    QPixmap,
    QCursor,
    QPainterPath,
    QPen,
    QBrush,
    QGuiApplication,
)
from PyQt5.QtCore import Qt, QRect, QTimer, QPointF, QRectF, QPoint, QEvent

from .utils import (
    LASER_COLORS,
    MODE_MAP,
    PEN_COLORS,
    SHADE_COLORS,
    capture_monitor_screenshot,
    MODE_SPOTLIGHT,
    MODE_PEN,
    MODE_LASER,
    MODE_MAG_GLASS,
    MODE_MOUSE,
)


DEBUG = True


CONFIG_PATH = os.path.expanduser("~/.config/pyspotlight/config.ini")


class SpotlightOverlayWindow(QWidget):
    def __init__(self, context, screenshot, screen_geometry):
        super().__init__()

        self._ctx = context

        if self._ctx.windows_os:
            QApplication.instance().installEventFilter(self)

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.X11BypassWindowManagerHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setCursor(Qt.BlankCursor)

        self._ctx.current_mode = MODE_MOUSE

        self._auto_mode_enabled = True
        self._always_take_screenshot = False
        self.mag_aspect_ratio = 0.65

        self.last_key_time = 0
        self.last_key_pressed = 0

        self.zoom_max = 5
        self.zoom_min = 2
        self.overlay_alpha = 200
        self.overlay_color = QColor(10, 10, 10, self.overlay_alpha)

        self.pen_paths = []  # Lista de listas de pontos (QPoint)
        self.current_path = []  # Caminho atual
        self.drawing = False  # Se está atualmente desenhando
        self.current_line_width = 3

        self.setGeometry(screen_geometry)

        # self.pixmap = QPixmap.fromImage(screenshot)
        self.clear_pixmap()

        self.pen_color = PEN_COLORS[self._ctx.config.get("marker_color_index", 0)][0]

        self.cursor_pos = None  # Usado para exibir a caneta

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(16)

        self.center_screen = self.geometry().center()

        QCursor.setPos(self.center_screen)

    def get_screen_index_under_cursor(self):
        cursor_pos = QCursor.pos()
        for i, screen in enumerate(QGuiApplication.screens()):
            if screen.geometry().contains(cursor_pos):
                return i
        return 0  # fallback

    def eventFilter(self, a0, a1):
        if a1.type() == QEvent.KeyPress:
            self.do_keypress(a1)
            return True  # impede propagação se quiser
        return False

    def do_keypress(self, event):
        key = event.key()
        now = time.time()

        if key == Qt.Key_Escape:
            if (
                now - self.last_key_time < 1.0
                and self.last_key_pressed == Qt.Key_Escape
            ):
                self.quit()
        elif key == Qt.Key_P:
            self.capture_screenshot(a="keypress")
            self.update()
        elif key == Qt.Key_M:
            self.switch_mode(step=1)
            self.update()

        self.last_key_time = now
        self.last_key_pressed = key

    def clear_pixmap(self):
        if self._always_take_screenshot:
            return
        self.pixmap = QPixmap(self.size())
        self.pixmap.fill(Qt.transparent)

    def change_overlay_color(self, dir=1):
        new_index = self._ctx.config["shade_color_index"] + dir
        if new_index > len(SHADE_COLORS) - 1:
            new_index = 0
        elif new_index < 0:
            new_index = len(SHADE_COLORS) - 1
        self._ctx.config["shade_color_index"] = new_index

    def laser_inverted(self):
        return self._ctx.config["laser_color_index"] == len(LASER_COLORS) - 1

    def auto_mode_enabled(self):
        return self._auto_mode_enabled and self._ctx.support_auto_mode

    def set_spotlight_mode(self):
        self.switch_mode(direct_mode=MODE_SPOTLIGHT)

    def set_mouse_mode(self):
        self.switch_mode(direct_mode=MODE_MOUSE)

    def set_laser_mode(self):
        self.switch_mode(direct_mode=MODE_LASER)

    def set_pen_mode(self):
        self.switch_mode(direct_mode=MODE_PEN)

    def hide_overlay(self):
        self.clear_pixmap()
        self.hide()
        # self.close()

    def show_overlay(self):
        if not self.isVisible():
            if self._ctx.current_mode == MODE_MAG_GLASS:
                if self._ctx.config["magnify_zoom"] <= self.zoom_min:
                    self._ctx.config["magnify_zoom"] = self.zoom_min
                self.capture_screenshot(a="showoverlay modeglass")
            elif self._ctx.current_mode == MODE_LASER and self.laser_inverted():
                self.capture_screenshot(a="showoverlay modelaser")
            elif self._ctx.current_mode != MODE_MOUSE:
                if self._always_take_screenshot:
                    self.capture_screenshot(a="showoverlay always")
                else:
                    self.showFullScreen()

        self.update()

    def set_auto_mode(self, enable=True):
        if not self._ctx.support_auto_mode:
            return
        self._auto_mode_enabled = enable
        if enable:
            self._ctx.show_info(f"Auto Mode")
            self.hide_overlay()
        else:
            self.show_overlay()
            self._ctx.show_info(f"{MODE_MAP[self._ctx.current_mode]}")

    def switch_mode(self, step=1, direct_mode=-1):
        # screen_index = self.get_screen_index_under_cursor()
        # self._ctx.change_screen(screen_index)

        compatible = self._ctx.compatible_modes
        all_modes = list(MODE_MAP.keys())  # usa ordem de definição dos modos

        if not compatible:
            return

        if direct_mode >= 0:
            if direct_mode in compatible and not (
                direct_mode == MODE_PEN and self.auto_mode_enabled()
            ):
                self.apply_mode_change(direct_mode)
            return

        # Busca o próximo modo compatível
        current_index = (
            all_modes.index(self._ctx.current_mode)
            if self._ctx.current_mode in all_modes
            else 0
        )
        total_modes = len(all_modes)

        for i in range(1, total_modes + 1):  # evita loop infinito
            next_index = (current_index + step * i) % total_modes
            next_mode = all_modes[next_index]
            if next_mode == MODE_PEN and self.auto_mode_enabled():
                continue  # pula MODE_PEN
            if next_mode in compatible:
                self.apply_mode_change(next_mode)
                return

    def apply_mode_change(self, new_mode):
        last_mode = self._ctx.current_mode
        if last_mode != new_mode and last_mode == MODE_MAG_GLASS:
            self.clear_pixmap()
        self._ctx.current_mode = new_mode
        if new_mode == MODE_MOUSE:
            self.hide_overlay()
        else:
            if new_mode == MODE_MAG_GLASS:
                self.capture_screenshot(a="apply_mode_change modeglass")
            self.show_overlay()

        self._ctx.show_info(f"Modo {MODE_MAP[self._ctx.current_mode]}")

    def change_laser_size(self, delta: int):
        min_size = 1
        max_size = 99
        new_size = self._ctx.config["laser_dot_size"] + delta
        if new_size < min_size:
            new_size = min_size
        elif new_size > max_size:
            new_size = max_size

        if new_size != self._ctx.config["laser_dot_size"]:
            self._ctx.config["laser_dot_size"] = new_size
            self.update()

    def change_spot_radius(self, increase=1):
        min_size = 5
        max_size = 99

        if self._ctx.current_mode == MODE_SPOTLIGHT:
            key = "spotlight_size"
        elif self._ctx.current_mode == MODE_MAG_GLASS:
            key = "magnify_size"
        else:
            return

        current = self._ctx.config.get(key, 10)
        new_value = max(min_size, min(current + increase, max_size))
        self._ctx.config[key] = new_value

        self.update()

    def zoom(self, direction):
        if self._ctx.current_mode == MODE_MAG_GLASS:
            if direction > 0:
                self._ctx.config["magnify_zoom"] = min(
                    self.zoom_max, self._ctx.config["magnify_zoom"] + 1
                )
            else:
                self._ctx.config["magnify_zoom"] = max(
                    self.zoom_min, self._ctx.config["magnify_zoom"] - 1
                )
            self.update()

    def next_laser_color(self, step=1):
        self._ctx.config["laser_color_index"] = (
            self._ctx.config["laser_color_index"] + step
        ) % len(LASER_COLORS)
        if self.laser_inverted():
            self.capture_screenshot(a="next_laser_color")
        else:
            self.clear_pixmap()
        self.update()

    def next_pen_color(self, step=1):
        self._ctx.config["marker_color_index"] = (
            self._ctx.config["marker_color_index"] + step
        ) % len(PEN_COLORS)
        self.pen_color = PEN_COLORS[self._ctx.config["marker_color_index"]]
        self.update()

    def clear_drawing(self, all=False):
        if all:
            self.pen_paths.clear()
        if self.pen_paths:
            self.pen_paths.pop()  # Remove o último caminho desenhado
        self.current_path = []
        self.update()

    def change_line_width(self, delta: int):
        min_width = 1
        max_width = 20

        new_width = self.current_line_width + delta
        if new_width < min_width:
            new_width = min_width
        elif new_width > max_width:
            new_width = max_width

        if new_width != self.current_line_width:
            self.current_line_width = new_width
            self.update()  # atualiza a tela para refletir a mudança, se necessário

    def capture_screenshot(self, a="!"):
        self._ctx.log(f"Capture Screenshot-{a}")
        do_hide = self.isVisible()
        if do_hide:
            # Esconde a janela overlay
            self.hide_overlay()

        QApplication.processEvents()
        time.sleep(0.5)  # aguardar atualização da tela

        # Captura a tela limpa usando seu método externo
        qimage, rect = capture_monitor_screenshot(self._ctx.screen_index)

        # Atualiza o pixmap do overlay (converter QImage para QPixmap)
        self.pixmap = QPixmap.fromImage(qimage)

        # Mostra a janela overlay novamente se foi ocultada
        if do_hide:
            self.showFullScreen()

    def drawMagnifyingGlass(self, painter, cursor_pos):

        radius = int(self._ctx.current_screen_height) * (
            self._ctx.config["magnify_size"] / 100.0
        )
        PADDING = 100  # pixels extras de borda

        if self._ctx.config["magnify_shape"].lower() == "rectangle":
            width = radius * 2
            height = int(width * self.mag_aspect_ratio)
            is_ellipse = False
        else:
            width = height = radius * 2
            is_ellipse = True

        # Cálculo da área de origem (reduzida pela ampliação)
        src_width = int(width / self._ctx.config["magnify_zoom"])
        src_height = int(height / self._ctx.config["magnify_zoom"])

        # Cria imagem com borda transparente
        padded_pixmap = QPixmap(
            self.pixmap.width() + PADDING * 2, self.pixmap.height() + PADDING * 2
        )
        padded_pixmap.fill(Qt.transparent)

        painter_pad = QPainter(padded_pixmap)
        painter_pad.drawPixmap(PADDING, PADDING, self.pixmap)
        painter_pad.end()

        # Corrige a posição do cursor no espaço com padding
        cursor_pos_padded = QPoint(cursor_pos.x() + PADDING, cursor_pos.y() + PADDING)

        # Calcula retângulo de origem (recorte ampliado)
        x = cursor_pos_padded.x() - src_width // 2
        y = cursor_pos_padded.y() - src_height // 2
        src_rect = QRect(x, y, src_width, src_height)

        # Retângulo de destino (onde será desenhado o zoom)
        dest_rect = QRect(
            int(cursor_pos.x() - width // 2),
            int(cursor_pos.y() - height // 2),
            int(width),
            int(height),
        )

        # Clipping para formato oval ou quadrado
        if is_ellipse:
            clip_path = QPainterPath()
            clip_path.addEllipse(QRectF(dest_rect))
            painter.setClipPath(clip_path)

        # Desenha a imagem ampliada
        painter.drawPixmap(dest_rect, padded_pixmap, src_rect)

        if is_ellipse:
            painter.setClipping(False)

        # Borda branca
        border_color = QColor(255, 255, 255, 180)
        pen = QPen(border_color, 2 if not is_ellipse else 4)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.setRenderHint(QPainter.Antialiasing)

        if is_ellipse:
            painter.drawEllipse(dest_rect)
        else:
            painter.drawRect(dest_rect)

    def drawSpotlight(self, painter, cursor_pos):

        size = int(self._ctx.current_screen_height) * (
            self._ctx.config["spotlight_size"] / 100.0
        )
        # Spotlight tradicional com overlay escuro
        overlay_color = SHADE_COLORS[self._ctx.config["shade_color_index"]][0]
        overlay_color.setAlpha(int(self._ctx.config["shade_opacity"] * 255 / 100))
        painter.setBrush(overlay_color)
        painter.setPen(Qt.NoPen)

        spotlight_path = QPainterPath()
        spotlight_path.addRect(QRectF(self.rect()))
        spotlight_path.addEllipse(cursor_pos, size, size)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPath(spotlight_path)

    def drawLaser(self, painter, cursor_pos):
        size = int(self._ctx.current_screen_height) * (
            self._ctx.config["laser_dot_size"] / 100.0
        )

        half_size = size // 2
        # Laser pointer com sombras e círculo central

        color = LASER_COLORS[self._ctx.config["laser_color_index"]][0]

        if color == LASER_COLORS[-1][0]:
            laser_rect = QRect(
                int(cursor_pos.x() - half_size),
                int(cursor_pos.y() - half_size),
                int(size),
                int(size),
            )

            region = self.pixmap.copy(laser_rect)
            image = region.toImage()
            image.invertPixels()
            inverted_pixmap = QPixmap.fromImage(image)

            # Clipa o círculo para desenhar só o laser invertido dentro dele
            clip_path = QPainterPath()
            clip_path.addEllipse(cursor_pos, half_size, half_size)
            painter.setClipPath(clip_path)
            painter.drawPixmap(laser_rect, inverted_pixmap)
            painter.setClipping(False)

            if self._ctx.config["laser_reflection"]:
                # Agora desenha as sombras ao redor, mas **fora** do círculo
                for margin, alpha in [(12, 50), (8, 80), (4, 110)]:
                    outer_radius = half_size + margin
                    outer_path = QPainterPath()
                    outer_path.addEllipse(cursor_pos, outer_radius, outer_radius)

                    # subtrai o círculo central
                    outer_path -= clip_path

                    shadow_color = QColor(255, 255, 255, alpha)
                    painter.setBrush(shadow_color)
                    painter.setPen(Qt.NoPen)
                    painter.drawPath(outer_path)

                # borda branca (opcional)
                pen = QPen(QColor(255, 255, 255, 200))
                pen.setWidth(2)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.drawEllipse(cursor_pos, half_size, half_size)

        else:

            center_x = int(cursor_pos.x() - size // 2)
            center_y = int(cursor_pos.y() - size // 2)

            # Agora desenha as sombras ao redor, mas **fora** do círculo
            if self._ctx.config["laser_reflection"]:
                shadow_levels = [(12, 30), (8, 60), (4, 90)]
                for margin, alpha in shadow_levels:
                    shadow_color = QColor(color)
                    shadow_color.setAlpha(alpha)
                    painter.setBrush(shadow_color)
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(
                        int(center_x - margin),
                        int(center_y - margin),
                        int(size + 2 * margin),
                        int(size + 2 * margin),
                    )

            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(center_x, center_y, int(size), int(size))

    def drawLines(self, painter, cursor_pos):
        painter.setRenderHint(QPainter.Antialiasing)

        # Desenha paths antigos
        for path in self.pen_paths:
            pen = QPen(
                path["color"],
                path["width"],
                Qt.SolidLine,
                Qt.RoundCap,
                Qt.RoundJoin,
            )
            painter.setPen(pen)
            if len(path["points"]) > 1:
                for i in range(len(path["points"]) - 1):
                    painter.drawLine(path["points"][i], path["points"][i + 1])

        # Desenha o path atual (se estiver desenhando)
        if self.drawing and len(self.current_path) > 1:
            pen = QPen(
                self.pen_color,
                self.current_line_width,
                Qt.SolidLine,
                Qt.RoundCap,
                Qt.RoundJoin,
            )
            painter.setPen(pen)
            for i in range(len(self.current_path) - 1):
                painter.drawLine(self.current_path[i], self.current_path[i + 1])

        cursor_pos = self.mapFromGlobal(QCursor.pos())
        brush = QBrush(self.pen_color)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        self.draw_pen_tip(painter, cursor_pos, size=self.current_line_width * 4)

    def paintEvent(self, event):
        painter = QPainter(self)
        cursor_pos = self.mapFromGlobal(QCursor.pos())
        # Fundo: sempre desenha o screenshot completo
        painter.drawPixmap(0, 0, self.pixmap)
        if self._ctx.current_mode == MODE_SPOTLIGHT:
            self.drawSpotlight(painter, cursor_pos)
        elif self._ctx.current_mode == MODE_LASER:
            self.drawLaser(painter, cursor_pos)
        elif self._ctx.current_mode == MODE_PEN:
            self.drawLines(painter, cursor_pos)
        elif self._ctx.current_mode == MODE_MAG_GLASS:
            self.drawMagnifyingGlass(painter, cursor_pos)

    def draw_pen_tip(self, painter, pos, size=20):
        # Pontos do SVG com a ponta em (0, 0)
        original_points = [
            (0.0, 0.0),  # ponta inferior
            (43.989, -75.561),  # canto superior esquerdo
            (57.999, -66.870),  # canto superior direito
            (11.352, 6.918),  # lado inferior direito
            (-1.241, 14.013),  # lado inferior esquerdo
        ]

        # Escala total proporcional ao "size" do traço
        # Consideramos que o SVG foi feito com largura base ~10 → ajustamos para isso
        base_line_width = 20  # ajuste este valor se quiser outra espessura padrão
        scale = size / base_line_width

        points = [
            QPointF(pos.x() + x * scale, pos.y() + y * scale)
            for (x, y) in original_points
        ]

        path = QPainterPath()
        path.moveTo(points[0])
        for p in points[1:]:
            path.lineTo(p)
        path.closeSubpath()

        painter.setBrush(QBrush(self.pen_color))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)

    def start_pen_path(self):
        self.drawing = True
        self.current_path = []

    def finish_pen_path(self):
        if len(self.current_path) > 1:
            self.pen_paths.append(
                {
                    "points": self.current_path[:],
                    "color": self.pen_color,
                    "width": self.current_line_width,
                }
            )
        self.current_path = []
        self.drawing = False
        self.update()

    def handle_draw_command(self, command):
        match command:
            case "start_move":
                if self._ctx.current_mode == MODE_PEN:
                    self.start_pen_path()

            case "stop_move":
                if self._ctx.current_mode == MODE_PEN and self.drawing:
                    self.finish_pen_path()

            case "line_width_increase":
                self.current_line_width = min(self.current_line_width + 1, 20)

            case "line_width_decrease":
                self.current_line_width = max(self.current_line_width - 1, 1)

    def mousePressEvent(self, event):
        if self._ctx.current_mode == MODE_PEN:
            self.start_pen_path()
            self.current_path.append(event.pos())

    def mouseMoveEvent(self, event):
        if self._ctx.current_mode == MODE_PEN and self.drawing:
            self.current_path.append(event.pos())
        self.update()

    def mouseReleaseEvent(self, event):
        if self._ctx.current_mode == MODE_PEN and self.drawing:
            self.finish_pen_path()

    def keyPressEvent(self, event):
        self.do_keypress(event)

    def closeEvent(self, event):
        # self.save_config()
        event.accept()

    def quit(self):
        # self.save_config()
        self.set_mouse_mode()
