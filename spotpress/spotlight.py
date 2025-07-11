import time
from spotpress.qtcompat import (
    QApplication,
    QPainter_Antialiasing,
    QPainter_CompositionMode_Clear,
    QPainter_CompositionMode_Source,
    QWidget,
    QPainter,
    QColor,
    QPixmap,
    QCursor,
    QPainterPath,
    QPen,
    QBrush,
    QGuiApplication,
    QRect,
    QTimer,
    QPointF,
    QRectF,
    QPoint,
    QPixmap,
    Qt_BlankCursor,
    Qt_BrushStyle_NoBrush,
    Qt_Color_Transparent,
    Qt_Event_KeyPress,
    Qt_Key_Escape,
    Qt_Key_M,
    Qt_Key_P,
    Qt_Key_H,
    Qt_NoPen,
    Qt_PenJoinStyle_RoundJoin,
    Qt_RoundCap,
    Qt_SolidLine,
    Qt_WidgetAttribute_WA_ShowWithoutActivating,
    Qt_WidgetAttribute_WA_TranslucentBackground,
    Qt_WidgetAttribute_WA_TransparentForMouseEvents,
    Qt_WindowType_FramelessWindowHint,
    Qt_WindowType_Tool,
    Qt_WindowType_WindowStaysOnTopHint,
    Qt_WindowType_X11BypassWindowManagerHint,
)

from .utils import (
    LASER_COLORS,
    MODE_MAP,
    PEN_COLORS,
    SHADE_COLORS,
    apply_blur,
    capture_monitor_screenshot,
    MODE_SPOTLIGHT,
    MODE_PEN,
    MODE_LASER,
    MODE_MAG_GLASS,
    MODE_MOUSE,
)


DEBUG = True


class SpotlightOverlayWindow(QWidget):

    def __init__(self, context, screen_geometry):
        super().__init__()

        self._ctx = context

        if self._ctx.windows_os:
            instance = QApplication.instance()
            if instance:
                instance.installEventFilter(self)

        self.setWindowFlags(
            Qt_WindowType_FramelessWindowHint
            | Qt_WindowType_WindowStaysOnTopHint
            | Qt_WindowType_X11BypassWindowManagerHint
            | Qt_WindowType_Tool
        )
        self.setAttribute(Qt_WidgetAttribute_WA_TranslucentBackground)
        self.setAttribute(Qt_WidgetAttribute_WA_ShowWithoutActivating)
        self.setAttribute(Qt_WidgetAttribute_WA_TransparentForMouseEvents)
        self.setCursor(Qt_BlankCursor)

        self.overlay_hidden = False

        self._last_show_overlay_time = 0

        self.mag_aspect_ratio = 0.65

        self.last_key_time = 0
        self.last_key_pressed = 0
        self._showing_overlay = False
        self._capturing_screenshot = False

        self.zoom_max = 5
        self.zoom_min = 2
        self.overlay_alpha = 200
        self.overlay_color = QColor(10, 10, 10, self.overlay_alpha)

        self.pen_paths = []  # Lista de listas de pontos (QPoint)
        self.current_path = []  # Caminho atual
        self.drawing = False  # Se está atualmente desenhando
        self.current_line_width = 3

        self.setGeometry(screen_geometry)

        self._pixmap_cleared = False
        self.clear_pixmap()

        # self.pen_color = PEN_COLORS[self._ctx.config.get("marker_color_index", 0)][0]

        # self.cursor_pos = None  # Usado para exibir a caneta

        # Timer de Atualização da Tela
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
        if a1 and a1.type() == Qt_Event_KeyPress:
            self.do_keypress(a1)
            return True  # impede propagação se quiser
        return False

    def do_keypress(self, event):
        key = event.key()
        now = time.time()

        if key == Qt_Key_Escape:

            if (
                now - self.last_key_time < 1.0
                and self.last_key_pressed == Qt_Key_Escape
            ):
                self.quit()
        elif key == Qt_Key_P:
            self.capture_screenshot()
            self.update()
        elif key == Qt_Key_M:
            self.switch_mode(step=1)
            self.update()
        elif key == Qt_Key_H:
            self.hide_overlay()

        self.last_key_time = now
        self.last_key_pressed = key

    def clear_pixmap(self):
        if self._pixmap_cleared or self._ctx.config.get(
            "general_always_capture", False
        ):
            return
        self.pixmap = QPixmap(self.size())
        self.pixmap.fill(Qt_Color_Transparent)
        self.blurred_pixmap = QPixmap(self.size())
        self.blurred_pixmap.fill(Qt_Color_Transparent)
        self._pixmap_cleared = True

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
        return (
            self._ctx.config.get("general_auto_mode", False)
            and self._ctx.support_auto_mode
        )

    def set_spotlight_mode(self):
        self.switch_mode(direct_mode=MODE_SPOTLIGHT)

    def set_mouse_mode(self):
        self.switch_mode(direct_mode=MODE_MOUSE)

    def set_laser_mode(self):
        self.switch_mode(direct_mode=MODE_LASER)

    def set_pen_mode(self):
        self.switch_mode(direct_mode=MODE_PEN)

    def set_mag_glass_mode(self):
        self.switch_mode(direct_mode=MODE_MAG_GLASS)

    def hide_overlay(self):
        self.overlay_hidden = True
        self.clear_pixmap()
        self.hide()

    def is_overlay_actually_visible(self):
        return not self.overlay_hidden and self.isVisible()

    def show_overlay(self):
        if (
            self._showing_overlay
            or self._capturing_screenshot
            or self._ctx.current_mode == MODE_MOUSE
            or self.is_overlay_actually_visible()
        ):
            return  # Ignora chamadas repetidas enquanto estiver processando

        self._showing_overlay = True
        try:
            if not self.is_overlay_actually_visible():

                if self._ctx.current_mode == MODE_MAG_GLASS:
                    if self._ctx.config["magnify_zoom"] <= self.zoom_min:
                        self._ctx.config["magnify_zoom"] = self.zoom_min

                    self.capture_screenshot(
                        show_after=True,
                        blur_level=self._ctx.config["magnify_background_blur_level"],
                    )
                elif self._ctx.current_mode == MODE_LASER and self.laser_inverted():
                    self.capture_screenshot(show_after=True)
                elif (
                    self._ctx.current_mode == MODE_SPOTLIGHT
                    and self._ctx.config["spotlight_background_mode"] == 0
                ):
                    self.capture_screenshot(
                        fill_pixmap=False,
                        show_after=True,
                        blur_level=self._ctx.config["spotlight_background_blur_level"],
                    )
                elif self._ctx.current_mode != MODE_MOUSE:
                    if self._ctx.config.get("general_always_capture", False):
                        self.capture_screenshot(show_after=True)
                    else:
                        self.clear_pixmap()
                        self.showFullScreen()
            self.update()
            self.overlay_hidden = False
        finally:
            self._showing_overlay = False

    def set_auto_mode(self, enable=True):
        if not self._ctx.support_auto_mode:
            return
        self._ctx.config["general_auto_mode"] = enable
        if enable:
            self._ctx.show_info(f"Auto Mode")
            self.hide_overlay()
        else:
            self.show_overlay()
            self._ctx.show_info(f"{MODE_MAP[self._ctx.current_mode]}")

    def switch_mode(self, step=1, direct_mode=-1):
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
                self.capture_screenshot()
            if (
                new_mode == MODE_SPOTLIGHT
                and self._ctx.config["spotlight_background_mode"] == 0
            ):
                self.capture_screenshot(
                    fill_pixmap=False,
                    blur_level=self._ctx.config["spotlight_background_blur_level"],
                )
            if not self.auto_mode_enabled():
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
            self.capture_screenshot(show_after=True)
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
        current_width = self._ctx.config["marker_width"]
        new_width = current_width + delta
        if new_width < min_width:
            new_width = min_width
        elif new_width > max_width:
            new_width = max_width

        if new_width != current_width:
            self._ctx.config["marker_width"] = new_width
            self.update()  # atualiza a tela para refletir a mudança, se necessário

    def capture_screenshot(self, show_after=False, fill_pixmap=True, blur_level=0):
        self._capturing_screenshot = True
        try:
            self.hide_overlay()

            QApplication.processEvents()
            time.sleep(0.5)  # aguardar atualização da tela

            # Captura a tela limpa usando seu método externo
            qimage = capture_monitor_screenshot(self._ctx.screen_index)

            pixmap = QPixmap.fromImage(qimage)

            # Atualiza o pixmap do overlay (converter QImage para QPixmap)
            if fill_pixmap:
                self.pixmap = pixmap
            if blur_level != 0:
                self.blurred_pixmap = apply_blur(pixmap, blur_level)

            self._pixmap_cleared = False

            # Mostra a janela overlay novamente se foi ocultada
            if show_after:
                self.showFullScreen()
        finally:
            self._capturing_screenshot = False

    def drawMagnifyingGlass(self, painter, cursor_pos):
        radius = int(self._ctx.current_screen_height) * (
            self._ctx.config["magnify_size"] / 100.0
        )
        PADDING = 100

        shape = self._ctx.config["magnify_shape"].lower()
        if shape == "rectangle":
            width = radius * 2
            height = int(width * self.mag_aspect_ratio)
            is_ellipse = False
        else:
            width = height = radius * 2
            is_ellipse = True

        zoom = self._ctx.config["magnify_zoom"]

        bg_mode = int(self._ctx.config.get("magnify_background_mode", 2))

        if bg_mode == 0:  # Blur
            if self.blurred_pixmap:
                painter.drawPixmap(0, 0, self.blurred_pixmap)
            else:
                painter.drawPixmap(0, 0, self.pixmap)
        elif bg_mode == 1:  # Shade
            # Spotlight tradicional com overlay escuro
            shade_color = SHADE_COLORS[self._ctx.config["shade_color_index"]][0]
            shade_color.setAlpha(int(self._ctx.config["shade_opacity"] * 255 / 100))
            painter.fillRect(self.rect(), shade_color)
        elif bg_mode == 2:  # None
            painter.drawPixmap(0, 0, self.pixmap)

        # Área nítida (ampliada)
        padded_pixmap = QPixmap(
            self.pixmap.width() + PADDING * 2, self.pixmap.height() + PADDING * 2
        )
        padded_pixmap.fill(Qt_Color_Transparent)
        painter_pad = QPainter(padded_pixmap)
        painter_pad.drawPixmap(PADDING, PADDING, self.pixmap)
        painter_pad.end()

        cursor_pos_padded = QPoint(cursor_pos.x() + PADDING, cursor_pos.y() + PADDING)

        src_width = int(width / zoom)
        src_height = int(height / zoom)
        x = cursor_pos_padded.x() - src_width // 2
        y = cursor_pos_padded.y() - src_height // 2
        src_rect = QRect(x, y, src_width, src_height)

        dest_rect = QRect(
            int(cursor_pos.x() - width // 2),
            int(cursor_pos.y() - height // 2),
            int(width),
            int(height),
        )

        # Clip da lente
        if is_ellipse:
            clip_path = QPainterPath()
            clip_path.addEllipse(QRectF(dest_rect))
            painter.setClipPath(clip_path)

        # Desenha a lente ampliada (sem blur)
        painter.drawPixmap(dest_rect, padded_pixmap, src_rect)

        if is_ellipse:
            painter.setClipping(False)

        if self._ctx.config.get("magnify_border", False):

            # Desneho da borda
            color_index = int(self._ctx.config.get("border_color_index", 0))
            opacity = int(self._ctx.config.get("border_opacity", 255))
            border_width = int(self._ctx.config.get("border_width", 3))
            border_color = PEN_COLORS[color_index][0]
            border_color.setAlpha(opacity)

            pen = QPen(border_color, border_width)
            painter.setPen(pen)
            painter.setBrush(Qt_BrushStyle_NoBrush)
            painter.setRenderHint(QPainter_Antialiasing)
            border_rect = dest_rect.adjusted(
                border_width // 2,
                border_width // 2,
                -border_width // 2,
                -border_width // 2,
            )

            if is_ellipse:
                painter.drawEllipse(border_rect)
            else:
                painter.drawRect(border_rect)

    def drawSpotlight(self, painter, cursor_pos):

        size = int(self._ctx.current_screen_height) * (
            self._ctx.config["spotlight_size"] / 100.0
        )

        bg_mode = int(self._ctx.config.get("spotlight_background_mode", 1))

        if bg_mode == 0 and self.blurred_pixmap:
            # Desenha o fundo borrado
            painter.drawPixmap(0, 0, self.blurred_pixmap)

            # Desenha a camada shade (escurecida) por cima do blur
            shade_color = SHADE_COLORS[self._ctx.config["shade_color_index"]][0]
            # Neste caso desenha um alpha Fixo só para fazer um efeito além do blur
            shade_color.setAlpha(100)
            # shade_color = QColor(0, 0, 0, 50)
            painter.fillRect(self.rect(), shade_color)

            # Muda modo de composição para "furar"
            painter.setCompositionMode(QPainter_CompositionMode_Clear)

            spotlight_rect = QRectF(
                cursor_pos.x() - size,
                cursor_pos.y() - size,
                size * 2,
                size * 2,
            )
            painter.setRenderHint(QPainter_Antialiasing)
            painter.setBrush(QBrush(Qt_Color_Transparent))
            painter.setPen(QPen(Qt_NoPen))
            painter.drawEllipse(spotlight_rect)

            # Restaura modo padrão
            painter.setCompositionMode(QPainter_CompositionMode_Source)

        elif bg_mode == 1:  # Shade
            shade_color = SHADE_COLORS[self._ctx.config["shade_color_index"]][0]
            shade_color.setAlpha(int(self._ctx.config["shade_opacity"] * 255 / 100))
            painter.setBrush(shade_color)
            painter.setPen(QPen(Qt_NoPen))

            spotlight_path = QPainterPath()
            spotlight_path.addRect(QRectF(self.rect()))
            spotlight_path.addEllipse(QPointF(cursor_pos), size, size)

            painter.setRenderHint(QPainter_Antialiasing)
            painter.drawPath(spotlight_path)

        if self._ctx.config.get("spotlight_border", False):
            color_index = int(self._ctx.config.get("border_color_index", 0))
            opacity = int(self._ctx.config.get("border_opacity", 255))
            width = int(self._ctx.config.get("border_width", 3))

            color = PEN_COLORS[color_index][0]
            color.setAlpha(opacity)
            border_radius = size - width / 2

            pen = QPen(color, width)
            painter.setPen(pen)
            painter.setBrush(Qt_BrushStyle_NoBrush)
            painter.drawEllipse(QPointF(cursor_pos), border_radius, border_radius)

    def drawLaser(self, painter, cursor_pos):
        size = int(self._ctx.current_screen_height) * (
            self._ctx.config["laser_dot_size"] / 100.0
        )

        color = LASER_COLORS[self._ctx.config["laser_color_index"]][0]
        half_size = size // 2

        # Se for a cor transparente desenha invertido
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
            clip_path.addEllipse(QPointF(cursor_pos), half_size + 0.5, half_size + 0.5)

            painter.setClipPath(clip_path)
            painter.drawPixmap(laser_rect, inverted_pixmap)
            painter.setClipping(False)
            if self._ctx.config["laser_reflection"]:
                for margin, alpha in [(12, 50), (8, 80), (4, 110)]:
                    outer_radius = half_size + margin
                    outer_size = size + 2 * margin
                    outer_rect = QRect(
                        int(cursor_pos.x() - outer_radius),
                        int(cursor_pos.y() - outer_radius),
                        int(outer_size),
                        int(outer_size),
                    )

                    # Recorta e inverte a imagem da região
                    region = self.pixmap.copy(outer_rect)
                    image = region.toImage()
                    image.invertPixels()
                    inverted = QPixmap.fromImage(image)

                    # Cria máscara circular para aplicar apenas na borda (anel)
                    clip_path = QPainterPath()
                    clip_path.addEllipse(
                        QPointF(cursor_pos), outer_radius, outer_radius
                    )
                    clip_path_inner = QPainterPath()
                    clip_path_inner.addEllipse(
                        QPointF(cursor_pos), half_size, half_size
                    )
                    clip_path -= clip_path_inner

                    # Aplica clipping e opacidade
                    painter.save()
                    painter.setClipPath(clip_path)
                    painter.setOpacity(alpha / 255.0)
                    painter.drawPixmap(outer_rect, inverted)
                    painter.restore()

        else:

            opacity = max(1, int(self._ctx.config["laser_opacity"] * 255 / 100))
            color.setAlpha(opacity)

            center_x = int(cursor_pos.x() - size // 2)
            center_y = int(cursor_pos.y() - size // 2)

            # Agora desenha as sombras ao redor, mas **fora** do círculo
            if self._ctx.config["laser_reflection"]:
                shadow_levels = [(12, 30), (8, 60), (4, 90)]
                for margin, alpha in shadow_levels:
                    shadow_color = QColor(color)
                    shadow_color.setAlpha(alpha)
                    painter.setBrush(shadow_color)
                    painter.setPen(QPen(Qt_NoPen))

                    painter.drawEllipse(
                        int(center_x - margin),
                        int(center_y - margin),
                        int(size + 2 * margin),
                        int(size + 2 * margin),
                    )

            painter.setBrush(color)
            painter.setPen(QPen(Qt_NoPen))

            painter.drawEllipse(center_x, center_y, int(size), int(size))

    def drawLines(self, painter, cursor_pos):
        painter.setRenderHint(QPainter_Antialiasing)

        # Desenha paths antigos
        for path in self.pen_paths:
            pen = QPen(
                path["color"],
                path["width"],
                Qt_SolidLine,
                Qt_RoundCap,
                Qt_PenJoinStyle_RoundJoin,
            )
            painter.setPen(pen)
            if len(path["points"]) > 1:
                for i in range(len(path["points"]) - 1):
                    painter.drawLine(path["points"][i], path["points"][i + 1])

        color = PEN_COLORS[self._ctx.config["marker_color_index"]][0]
        opacity = max(1, int(self._ctx.config["marker_opacity"] * 255 / 100))
        line_width = int(self._ctx.config["marker_width"])
        color.setAlpha(opacity)

        # Desenha o path atual (se estiver desenhando)
        if self.drawing and len(self.current_path) > 1:
            pen = QPen(
                color,
                line_width,
                Qt_SolidLine,
                Qt_RoundCap,
                Qt_PenJoinStyle_RoundJoin,
            )
            painter.setPen(pen)
            for i in range(len(self.current_path) - 1):
                painter.drawLine(self.current_path[i], self.current_path[i + 1])

        cursor_pos = self.mapFromGlobal(QCursor.pos())
        brush = QBrush(color)
        painter.setBrush(brush)
        painter.setPen(QPen(Qt_NoPen))

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

        color = PEN_COLORS[self._ctx.config["marker_color_index"]][0]

        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt_NoPen))

        painter.drawPath(path)

    def start_pen_path(self):
        self.drawing = True
        self.current_path = []

    def finish_pen_path(self):
        if len(self.current_path) > 1:
            color = PEN_COLORS[self._ctx.config["marker_color_index"]][0]
            opacity = max(1, int(self._ctx.config["marker_opacity"] * 255 / 100))
            line_width = int(self._ctx.config["marker_width"])
            color.setAlpha(opacity)
            self.pen_paths.append(
                {
                    "points": self.current_path[:],
                    "color": color,
                    "width": line_width,
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
        event.accept()

    def quit(self):
        self.set_mouse_mode()
