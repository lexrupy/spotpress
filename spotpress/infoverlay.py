# infooverlay.py

from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtGui import QFont, QColor, QPen
from PyQt6.QtCore import Qt

from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtGui import QFont, QColor, QPainter, QFontMetrics
from PyQt6.QtCore import Qt, QRect, QPoint


class InfOverlayWindow(QWidget):
    def __init__(self, screen_geometry):
        super().__init__()
        self.screen_geometry = screen_geometry

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.X11BypassWindowManagerHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: white;")
        self.font = QFont("Arial", 44, QFont.Weight.Bold)
        self.label.setFont(self.font)

    def show_message(self, text):
        self.label.setText(text)

        # Calcula o tamanho da janela com base no texto
        metrics = QFontMetrics(self.font)
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
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(0, 0, 0, 180))  # preto translúcido
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawRoundedRect(self.rect(), 20, 20)
