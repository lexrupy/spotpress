try:
    from PyQt6.QtCore import (
        Qt,
        QEvent,
        QRect,
        QRectF,
        QPoint,
        QPointF,
        pyqtSignal,
        pyqtSlot,
        QTimer,
        QObject,
        QThread,
        QMetaObject,
        Q_ARG,
    )
    from PyQt6.QtNetwork import QLocalServer, QLocalSocket
    from PyQt6.QtWidgets import (
        QApplication,
        QWidget,
        QMenu,
        QTabWidget,
        QMainWindow,
        QPushButton,
        QVBoxLayout,
        QHBoxLayout,
        QTextEdit,
        QFileDialog,
        QMessageBox,
        QSystemTrayIcon,
        QListWidget,
        QGroupBox,
        QComboBox,
        QRadioButton,
        QButtonGroup,
        QListWidgetItem,
        QDialog,
        QLabel,
        QFontDialog,
        QAbstractItemView,
        QSpinBox,
        QCheckBox,
        QGridLayout,
        QGraphicsScene,
        QGraphicsPixmapItem,
        QGraphicsBlurEffect,
        QSizePolicy,
    )
    from PyQt6.QtGui import (
        QIcon,
        QPixmap,
        QColor,
        QFont,
        QPainter,
        QPainterPath,
        QBrush,
        QCursor,
        QPen,
        QAction,
        QKeySequence,
        QClipboard,
        QImage,
        QGuiApplication,
        QFontMetrics,
    )

    Qt_ConnectionType_QueuedConnection = Qt.ConnectionType.QueuedConnection

    QPainter_CompositionMode_Clear = QPainter.CompositionMode.CompositionMode_Clear
    QPainter_CompositionMode_Source = QPainter.CompositionMode.CompositionMode_Source

    QSizePolicy_Preferred = QSizePolicy.Policy.Preferred
    QSizePolicy_Fixed = QSizePolicy.Policy.Fixed
    QSizePolicy_Expanding = QSizePolicy.Policy.Expanding

    QAbstractItemView_SelectionMode_SingleSelection = (
        QAbstractItemView.SelectionMode.SingleSelection
    )

    QAbstractItemView_DragDropMode_InternalMove = (
        QAbstractItemView.DragDropMode.InternalMove
    )

    # Enums e constantes adaptadas PyQt6
    Qt_FramelessWindowHint = Qt.WindowType.FramelessWindowHint
    Qt_WA_TranslucentBackground = Qt.WidgetAttribute.WA_TranslucentBackground
    Qt_BlankCursor = Qt.CursorShape.BlankCursor
    Qt_NoPen = Qt.PenStyle.NoPen
    Qt_Key_Escape = Qt.Key.Key_Escape
    Qt_AlignCenter = Qt.AlignmentFlag.AlignCenter
    Qt_AlignLeft = Qt.AlignmentFlag.AlignLeft
    Qt_SolidLine = Qt.PenStyle.SolidLine
    Qt_RoundCap = Qt.PenCapStyle.RoundCap
    Qt_Key_Tab = Qt.Key.Key_Tab
    Qt_Key_Control = Qt.Key.Key_Control
    Qt_Key_P = Qt.Key.Key_P
    Qt_Key_E = Qt.Key.Key_E
    Qt_Key_M = Qt.Key.Key_M
    Qt_Key_H = Qt.Key.Key_H
    Qt_Key_S = Qt.Key.Key_S
    Qt_Key_PageUp = Qt.Key.Key_PageUp
    Qt_Key_PageDown = Qt.Key.Key_PageDown
    Qt_Key_Shift = Qt.Key.Key_Shift
    Qt_Key_Escape = Qt.Key.Key_Escape
    Qt_Key_Return = Qt.Key.Key_Return
    Qt_Control_Modifier = Qt.KeyboardModifier.ControlModifier

    Qt_Event_KeyPress = QEvent.Type.KeyPress

    Qt_FontWeight_Bold = QFont.Weight.Bold

    Qt_Color_Transparent = Qt.GlobalColor.transparent

    Qt_DropAction_MoveAction = Qt.DropAction.MoveAction

    Qt_ItemFlag_ItemIsUserCheckable = Qt.ItemFlag.ItemIsUserCheckable
    Qt_ItemFlag_ItemIsEnabled = Qt.ItemFlag.ItemIsEnabled
    Qt_ItemFlag_ItemIsSelectable = Qt.ItemFlag.ItemIsSelectable
    Qt_ItemFlag_ItemIsDragEnabled = Qt.ItemFlag.ItemIsDragEnabled
    Qt_ItemFlag_ItemIsDropEnabled = Qt.ItemFlag.ItemIsDropEnabled

    Qt_ItemFlag_NoItemFlags = Qt.ItemFlag.NoItemFlags

    Qt_CheckState_Checked = Qt.CheckState.Checked
    Qt_CheckState_Unchecked = Qt.CheckState.Unchecked

    Qt_WindowMinimizeButtonHint = Qt.WindowType.WindowMinimizeButtonHint
    Qt_WindowType_Tool = Qt.WindowType.Tool
    Qt_WindowType_WindowStaysOnTopHint = Qt.WindowType.WindowStaysOnTopHint
    Qt_WindowType_X11BypassWindowManagerHint = Qt.WindowType.X11BypassWindowManagerHint
    Qt_WindowType_FramelessWindowHint = Qt.WindowType.FramelessWindowHint
    Qt_WindowType_WindowMinimizeButtonHint = Qt.WindowType.WindowMinimizeButtonHint

    Qt_WidgetAttribute_WA_TranslucentBackground = (
        Qt.WidgetAttribute.WA_TranslucentBackground
    )
    Qt_WidgetAttribute_WA_ShowWithoutActivating = (
        Qt.WidgetAttribute.WA_ShowWithoutActivating
    )
    Qt_WidgetAttribute_WA_TransparentForMouseEvents = (
        Qt.WidgetAttribute.WA_TransparentForMouseEvents
    )

    Qt_BrushStyle_NoBrush = Qt.BrushStyle.NoBrush
    Qt_PenJoinStyle_RoundJoin = Qt.PenJoinStyle.RoundJoin
    QPainter_Antialiasing = QPainter.RenderHint.Antialiasing

    QSystemTrayIcon_Trigger = QSystemTrayIcon.ActivationReason.Trigger
    QSystemTrayIcon_DoubleClick = QSystemTrayIcon.ActivationReason.DoubleClick
    QSystemTrayIcon_Context = QSystemTrayIcon.ActivationReason.Context

    QtItem_UserRole = Qt.ItemDataRole.UserRole

    QEvent_KeyPress = QEvent.Type.KeyPress
    QEvent_KeyRelease = QEvent.Type.KeyRelease
    QEvent_MouseButtonPress = QEvent.Type.MouseButtonPress
    QEvent_MouseButtonRelease = QEvent.Type.MouseButtonRelease
    QEvent_MouseMove = QEvent.Type.MouseMove

    SP_QT_VERSION = 6
except ImportError:
    from PyQt5.QtCore import (  # pyright: ignore
        Qt,
        QThread,
        QMetaObject,
        QEvent,
        QObject,
        QPoint,
        QPointF,
        Qt,
        pyqtSignal,
        pyqtSlot,
        QTimer,
        QRect,
        QRectF,
        Q_ARG,
    )
    from PyQt5.QtNetwork import QLocalServer, QLocalSocket  # pyright: ignore
    from PyQt5.QtWidgets import (  # pyright: ignore
        QApplication,
        QMenu,
        QAction,
        QTabWidget,
        QMainWindow,
        QListWidget,
        QGroupBox,
        QWidget,
        QPushButton,
        QRadioButton,
        QButtonGroup,
        QVBoxLayout,
        QHBoxLayout,
        QTextEdit,
        QFileDialog,
        QMessageBox,
        QSystemTrayIcon,
        QComboBox,
        QListWidgetItem,
        QDialog,
        QLabel,
        QFontDialog,
        QAbstractItemView,
        QSizePolicy,
        QSpinBox,
        QCheckBox,
        QGridLayout,
        QGraphicsScene,
        QGraphicsPixmapItem,
        QGraphicsBlurEffect,
    )
    from PyQt5.QtGui import (  # pyright: ignore
        QGuiApplication,
        QIcon,
        QPixmap,
        QColor,
        QFont,
        QPainter,
        QPainterPath,
        QBrush,
        QCursor,
        QPen,
        QKeySequence,
        QClipboard,
        QImage,
        QFontMetrics,
    )

    Qt_ConnectionType_QueuedConnection = Qt.QueuedConnection

    QPainter_CompositionMode_Clear = QPainter.CompositionMode_Clear
    QPainter_CompositionMode_Source = QPainter.CompositionMode_Source

    QSizePolicy_Preferred = QSizePolicy.Preferred
    QSizePolicy_Fixed = QSizePolicy.Fixed
    QSizePolicy_Expanding = QSizePolicy.Expanding

    QAbstractItemView_SelectionMode_SingleSelection = (
        QAbstractItemView.SelectionMode.SingleSelection
    )

    QAbstractItemView_DragDropMode_InternalMove = (
        QAbstractItemView.DragDropMode.InternalMove
    )

    Qt_WindowMinimizeButtonHint = Qt.WindowMinimizeButtonHint
    Qt_WindowType_Tool = Qt.Tool
    Qt_WindowType_WindowStaysOnTopHint = Qt.WindowStaysOnTopHint
    Qt_WindowType_X11BypassWindowManagerHint = Qt.X11BypassWindowManagerHint
    Qt_WindowType_FramelessWindowHint = Qt.FramelessWindowHint
    Qt_WindowType_WindowMinimizeButtonHint = Qt.WindowMinimizeButtonHint

    Qt_WidgetAttribute_WA_TranslucentBackground = Qt.WA_TranslucentBackground
    Qt_WidgetAttribute_WA_ShowWithoutActivating = Qt.WA_ShowWithoutActivating
    Qt_WidgetAttribute_WA_TransparentForMouseEvents = Qt.WA_TransparentForMouseEvents

    Qt_FramelessWindowHint = Qt.FramelessWindowHint
    Qt_WA_TranslucentBackground = Qt.WA_TranslucentBackground
    Qt_BlankCursor = Qt.BlankCursor
    Qt_NoPen = Qt.NoPen
    Qt_Key_Escape = Qt.Key_Escape
    Qt_AlignCenter = Qt.AlignCenter
    Qt_AlignLeft = Qt.AlignLeft
    Qt_SolidLine = Qt.SolidLine
    Qt_RoundCap = Qt.RoundCap
    Qt_Key_Tab = Qt.Key_Tab
    Qt_Key_Control = Qt.Key_Control
    Qt_Key_P = Qt.Key_P
    Qt_Key_E = Qt.Key_E
    Qt_Key_M = Qt.Key_M
    Qt_Key_H = Qt.Key_H
    Qt_Key_S = Qt.Key_S
    Qt_Key_PageUp = Qt.Key_PageUp
    Qt_Key_PageDown = Qt.Key_PageDown
    Qt_Key_Shift = Qt.Key_Shift
    Qt_Key_Return = Qt.Key_Return
    Qt_Control_Modifier = Qt.ControlModifier

    Qt_Event_KeyPress = QEvent.KeyPress

    Qt_FontWeight_Bold = QFont.Bold

    Qt_Color_Transparent = Qt.transparent

    Qt_DropAction_MoveAction = Qt.MoveAction

    Qt_ItemFlag_ItemIsUserCheckable = Qt.ItemIsUserCheckable
    Qt_ItemFlag_ItemIsEnabled = Qt.ItemIsEnabled
    Qt_ItemFlag_ItemIsSelectable = Qt.ItemIsSelectable
    Qt_ItemFlag_ItemIsDragEnabled = Qt.ItemIsDragEnabled
    Qt_ItemFlag_ItemIsDropEnabled = Qt.ItemIsDropEnabled

    Qt_ItemFlag_NoItemFlags = Qt.NoItemFlags

    Qt_CheckState_Checked = Qt.Checked
    Qt_CheckState_Unchecked = Qt.Unchecked

    Qt_BrushStyle_NoBrush = Qt.NoBrush
    Qt_PenJoinStyle_RoundJoin = Qt.RoundJoin
    QPainter_Antialiasing = QPainter.Antialiasing

    Qt_WindowMinimizeButtonHint = Qt.WindowMinimizeButtonHint

    QSystemTrayIcon_Trigger = QSystemTrayIcon.Trigger
    QSystemTrayIcon_DoubleClick = QSystemTrayIcon.DoubleClick
    QSystemTrayIcon_Context = QSystemTrayIcon.Context

    QtItem_UserRole = Qt.UserRole

    QEvent_KeyPress = QEvent.KeyPress
    QEvent_KeyRelease = QEvent.KeyRelease
    QEvent_MouseButtonPress = QEvent.MouseButtonPress
    QEvent_MouseButtonRelease = QEvent.MouseButtonRelease
    QEvent_MouseMove = QEvent.MouseMove
    SP_QT_VERSION = 5

# Opcional: expose tudo em um namespace para importar facilmente
__all__ = [
    "Qt",
    "QLocalServer",
    "QLocalSocket",
    "QEvent",
    "QObject",
    "QThread",
    "QMetaObject",
    "Qt_ConnectionType_QueuedConnection",
    "QApplication",
    "QGuiApplication",
    "QMenu",
    "QTabWidget",
    "QMainWindow",
    "QWidget",
    "QTimer",
    "QPushButton",
    "QVBoxLayout",
    "QHBoxLayout",
    "QTextEdit",
    "QFileDialog",
    "QMessageBox",
    "QListWidget",
    "QButtonGroup",
    "QRadioButton",
    "QGroupBox",
    "QSystemTrayIcon",
    "QComboBox",
    "QListWidgetItem",
    "QFontMetrics",
    "QSizePolicy_Fixed",
    "QSizePolicy_Preferred",
    "QPainter_CompositionMode_Clear",
    "QPainter_CompositionMode_Source",
    "QSpinBox",
    "QCheckBox",
    "QGraphicsScene",
    "QGraphicsPixmapItem",
    "QGraphicsBlurEffect",
    "QGridLayout",
    "QDialog",
    "QLabel",
    "QFontDialog",
    "QIcon",
    "QPixmap",
    "QImage",
    "QColor",
    "QFont",
    "QPainter",
    "QCursor",
    "QPoint",
    "QPointF",
    "QRect",
    "QRectF",
    "QPen",
    "QAction",
    "QKeySequence",
    "QClipboard",
    "QPainterPath",
    "QBrush",
    "Qt_FramelessWindowHint",
    "Qt_WA_TranslucentBackground",
    "Qt_BlankCursor",
    "Qt_NoPen",
    "Qt_Key_Escape",
    "Qt_AlignCenter",
    "Qt_SolidLine",
    "Qt_RoundCap",
    "Qt_Key_Tab",
    "Qt_Key_Control",
    "Qt_Key_P",
    "Qt_Key_E",
    "Qt_Key_M",
    "Qt_Key_H",
    "Qt_Key_S",
    "Qt_Key_PageUp",
    "Qt_Key_PageDown",
    "Qt_Key_Shift",
    "Qt_Key_Return",
    "QSystemTrayIcon_Trigger",
    "QSystemTrayIcon_DoubleClick",
    "QSystemTrayIcon_Context",
    "QEvent_KeyPress",
    "QEvent_KeyRelease",
    "QEvent_MouseButtonPress",
    "QEvent_MouseButtonRelease",
    "QEvent_MouseMove",
    "QtItem_UserRole",
    "Qt_ItemFlag_ItemIsUserCheckable",
    "Qt_ItemFlag_ItemIsEnabled",
    "Qt_ItemFlag_ItemIsSelectable",
    "Qt_ItemFlag_ItemIsDragEnabled",
    "Qt_ItemFlag_ItemIsDropEnabled",
    "pyqtSignal",
    "pyqtSlot",
    "Q_ARG",
    "SP_QT_VERSION",
]
