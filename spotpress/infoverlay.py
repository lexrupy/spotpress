# infooverlay.py
from spotpress.qtcompat import (
    QPainter_Antialiasing,
    QPen,
    QWidget,
    QLabel,
    QFont,
    QColor,
    QPainter,
    QFontMetrics,
    QRect,
    QPoint,
    Qt_AlignCenter,
    Qt_FontWeight_Bold,
    Qt_NoPen,
    Qt_WidgetAttribute_WA_ShowWithoutActivating,
    Qt_WidgetAttribute_WA_TranslucentBackground,
    Qt_WindowType_FramelessWindowHint,
    Qt_WindowType_Tool,
    Qt_WindowType_WindowStaysOnTopHint,
    Qt_WindowType_X11BypassWindowManagerHint,
)


class InfOverlayWindow(QWidget):
    def __init__(self, screen_geometry):
        super().__init__()
        self.screen_geometry = screen_geometry

        self.setWindowFlags(
            Qt_WindowType_FramelessWindowHint
            | Qt_WindowType_WindowStaysOnTopHint
            | Qt_WindowType_X11BypassWindowManagerHint
            | Qt_WindowType_Tool
        )
        self.setAttribute(Qt_WidgetAttribute_WA_TranslucentBackground)
        self.setAttribute(Qt_WidgetAttribute_WA_ShowWithoutActivating)

        self.label = QLabel(self)
        self.label.setAlignment(Qt_AlignCenter)
        self.label.setStyleSheet("color: white;")
        self.font = QFont("Arial", 44, Qt_FontWeight_Bold)  # pyright: ignore
        self.label.setFont(self.font)  # pyright: ignore

    def show_message(self, text):
        self.label.setText(text)

        # Calcula o tamanho da janela com base no texto
        metrics = QFontMetrics(self.font)  # pyright: ignore
        text_width = metrics.horizontalAdvance(text)
        text_height = metrics.height()

        padding_x = 100
        padding_y = 60

        window_width = text_width + padding_x
        window_height = text_height + padding_y

        # Centraliza no monitor de destino
        screen_center = self.screen_geometry.center()
        top_left = QPoint(
            screen_center.x() - window_width // 2,
            screen_center.y() - window_height // 2,
        )

        self.setGeometry(QRect(top_left, self.size()))
        self.resize(window_width, window_height)
        self.label.resize(window_width, window_height)
        self.show()

    def paintEvent(self, event):
        # Desenha fundo preto translúcido
        painter = QPainter(self)
        painter.setRenderHint(QPainter_Antialiasing)
        painter.setBrush(QColor(0, 0, 0, 180))  # preto translúcido
        painter.setPen(QPen(Qt_NoPen))
        painter.drawRoundedRect(self.rect(), 20, 20)
