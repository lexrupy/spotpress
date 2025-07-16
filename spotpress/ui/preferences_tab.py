import configparser
from spotpress.qtcompat import (
    QAbstractItemView_DragDropMode_InternalMove,
    QAbstractItemView_SelectionMode_SingleSelection,
    QMessageBox,
    QListWidgetItem,
    QSizePolicy_Expanding,
    QSizePolicy_Fixed,
    QWidget,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QListWidget,
    QGroupBox,
    QRadioButton,
    QIcon,
    QPixmap,
    QColor,
    Qt_CheckState_Checked,
    Qt_CheckState_Unchecked,
    Qt_DropAction_MoveAction,
    Qt_ItemFlag_ItemIsDragEnabled,
    Qt_ItemFlag_ItemIsDropEnabled,
    Qt_ItemFlag_ItemIsEnabled,
    Qt_ItemFlag_ItemIsSelectable,
    Qt_ItemFlag_ItemIsUserCheckable,
    Qt_ItemFlag_NoItemFlags,
)
from spotpress.utils import (
    DEFAULT_MODES,
    LASER_COLORS,
    MODE_MAP,
    MODE_NAME_TO_ID,
    PEN_COLORS,
    SHADE_COLORS,
)


def create_color_combobox(colors):
    combo = QComboBox()
    for color, name in colors:
        pixmap = QPixmap(16, 16)
        pixmap.fill(color)
        combo.addItem(QIcon(pixmap), name)
    return combo


def create_named_color_combobox(named_colors):
    combo = QComboBox()
    for value in named_colors:
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(value[0]))
        combo.addItem(QIcon(pixmap), value[1])
    return combo


class PreferencesTab(QWidget):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self._ctx = ctx
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        def make_group(title):
            box = QGroupBox(title)
            # box.setStyleSheet(
            #     "QGroupBox { background-color: #f4f4f4; border: 1px solid #ccc; border-radius: 4px; margin-top: 1ex; padding: 6px; }"
            # )
            return box

        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        self.spotlight_shape = QComboBox()
        self.spotlight_shape.addItem("Elipse")
        self.spotlight_shape.addItem("Rectangle")
        self.spotlight_shape.currentIndexChanged.connect(self.update_context_config)
        self.spotlight_size = QSpinBox()
        self.spotlight_size.setMaximum(99)
        self.spotlight_size.setSizePolicy(QSizePolicy_Expanding, QSizePolicy_Fixed)
        self.spotlight_size.valueChanged.connect(self.update_context_config)
        self.spotlight_border = QCheckBox("Border")
        self.spotlight_border.stateChanged.connect(self.update_context_config)

        self.spotlight_bg_mode = QComboBox()
        self.spotlight_bg_mode.addItem("Blur")
        self.spotlight_bg_mode.addItem("Shade")

        self.spotlight_bg_mode.currentIndexChanged.connect(self.update_context_config)

        self.spotlight_bg_blur = QSpinBox()
        self.spotlight_bg_blur.setMaximum(20)
        self.spotlight_bg_blur.setMinimum(1)
        self.spotlight_bg_blur.valueChanged.connect(self.update_context_config)

        spotlight_bg_mode = QHBoxLayout()
        spotlight_bg_mode.addWidget(QLabel("Background mode:"))
        spotlight_bg_mode.addWidget(self.spotlight_bg_mode)

        spotlight_group = make_group("Spotlight")
        spotlight_layout = QGridLayout()
        spotlight_layout.addWidget(QLabel("Shape:"), 0, 0)
        spotlight_layout.addWidget(self.spotlight_shape, 0, 1)
        spotlight_layout.addWidget(self.spotlight_border, 0, 2)
        spotlight_layout.addWidget(QLabel("Size:"), 1, 0)
        spotlight_layout.addWidget(self.spotlight_size, 1, 1)
        spotlight_layout.addWidget(QLabel("% of screen"), 1, 2)
        spotlight_layout.addLayout(spotlight_bg_mode, 2, 0, 1, 3)

        spotlight_layout.addWidget(QLabel("Background blur level:"), 3, 0, 1, 2)
        spotlight_layout.addWidget(self.spotlight_bg_blur, 3, 2)
        spotlight_group.setLayout(spotlight_layout)
        left_layout.addWidget(spotlight_group)

        # Magnifyer
        self.magnify_shape = QComboBox()

        self.magnify_shape.addItem("Elipse")
        self.magnify_shape.addItem("Rectangle")
        self.magnify_shape.currentIndexChanged.connect(self.update_context_config)
        self.magnify_size = QSpinBox()
        self.magnify_size.setSizePolicy(QSizePolicy_Expanding, QSizePolicy_Fixed)
        self.magnify_size.valueChanged.connect(self.update_context_config)
        self.magnify_border = QCheckBox("Border")
        self.magnify_border.stateChanged.connect(self.update_context_config)

        self.magnify_bg_mode = QComboBox()
        self.magnify_bg_mode.addItem("Blur")
        self.magnify_bg_mode.addItem("Shade")
        self.magnify_bg_mode.addItem("None")

        self.magnify_bg_mode.currentIndexChanged.connect(self.update_context_config)

        magnify_bg_mode = QHBoxLayout()

        magnify_bg_mode.addWidget(QLabel("Background mode:"))
        magnify_bg_mode.addWidget(self.magnify_bg_mode)

        self.magnify_zoom = QSpinBox()
        self.magnify_zoom.setMaximum(5)
        self.magnify_zoom.setMinimum(2)
        self.magnify_zoom.valueChanged.connect(self.update_context_config)

        self.magnify_bg_blur = QSpinBox()
        self.magnify_bg_blur.setMaximum(20)
        self.magnify_bg_blur.setMinimum(1)
        self.magnify_bg_blur.valueChanged.connect(self.update_context_config)

        magnify_group = make_group("Magnifier")
        magnify_layout = QGridLayout()
        magnify_layout.addWidget(QLabel("Shape:"), 0, 0)
        magnify_layout.addWidget(self.magnify_shape, 0, 1)
        magnify_layout.addWidget(self.magnify_border, 0, 2)
        magnify_layout.addWidget(QLabel("Size:"), 1, 0)
        magnify_layout.addWidget(self.magnify_size, 1, 1)
        magnify_layout.addWidget(QLabel("% of screen"), 1, 2)
        magnify_layout.addLayout(magnify_bg_mode, 2, 0, 1, 3)
        magnify_layout.addWidget(QLabel("Zoom level:"), 3, 0)
        magnify_layout.addWidget(self.magnify_zoom, 3, 1)
        magnify_layout.addWidget(QLabel("Background blur Level:"), 4, 0, 1, 2)
        magnify_layout.addWidget(self.magnify_bg_blur, 4, 2)

        magnify_group.setLayout(magnify_layout)
        left_layout.addWidget(magnify_group)

        # Laser
        self.laser_dot_size = QSpinBox()

        self.laser_dot_size.setSizePolicy(QSizePolicy_Expanding, QSizePolicy_Fixed)
        self.laser_dot_size.valueChanged.connect(self.update_context_config)
        self.laser_color = create_color_combobox(LASER_COLORS)
        self.laser_color.currentIndexChanged.connect(self.update_context_config)
        self.laser_opacity = QSpinBox()

        self.laser_opacity.setSizePolicy(QSizePolicy_Expanding, QSizePolicy_Fixed)

        self.laser_opacity.valueChanged.connect(self.update_context_config)
        self.laser_reflection = QCheckBox("Reflection")
        self.laser_reflection.stateChanged.connect(self.update_context_config)

        laser_group = make_group("Laser")
        laser_layout = QGridLayout()
        laser_layout.addWidget(QLabel("Dot size:"), 0, 0)
        laser_layout.addWidget(self.laser_dot_size, 0, 1)
        laser_layout.addWidget(QLabel("% of screen"), 0, 2)
        laser_layout.addWidget(QLabel("Dot color:"), 1, 0)
        laser_layout.addWidget(self.laser_color, 1, 1)
        laser_layout.addWidget(self.laser_reflection, 1, 2)
        laser_layout.addWidget(QLabel("Opacity:"), 2, 0)
        laser_layout.addWidget(self.laser_opacity, 2, 1)
        laser_layout.addWidget(QLabel("%"), 2, 2)
        laser_group.setLayout(laser_layout)
        right_layout.addWidget(laser_group)

        # Marker
        self.marker_width = QSpinBox()

        self.marker_width.setSizePolicy(QSizePolicy_Expanding, QSizePolicy_Fixed)
        self.marker_width.valueChanged.connect(self.update_context_config)
        self.marker_color = create_color_combobox(PEN_COLORS)
        self.marker_color.currentIndexChanged.connect(self.update_context_config)
        self.marker_opacity = QSpinBox()

        self.marker_opacity.setSizePolicy(QSizePolicy_Expanding, QSizePolicy_Fixed)
        self.marker_opacity.valueChanged.connect(self.update_context_config)

        marker_group = make_group("Marker")
        marker_layout = QGridLayout()
        marker_layout.addWidget(QLabel("Width:"), 0, 0)
        marker_layout.addWidget(self.marker_width, 0, 1)
        marker_layout.addWidget(QLabel("pixels"), 0, 2)
        marker_layout.addWidget(QLabel("Color:"), 1, 0)
        marker_layout.addWidget(self.marker_color, 1, 1)
        marker_layout.addWidget(QLabel("Opacity:"), 2, 0)
        marker_layout.addWidget(self.marker_opacity, 2, 1)
        marker_layout.addWidget(QLabel("%"), 2, 2)
        marker_group.setLayout(marker_layout)
        right_layout.addWidget(marker_group)

        # Shade
        self.shade_color = create_named_color_combobox(SHADE_COLORS)
        self.shade_color.currentIndexChanged.connect(self.update_context_config)
        self.shade_opacity = QSpinBox()

        self.shade_opacity.setSizePolicy(QSizePolicy_Expanding, QSizePolicy_Fixed)
        self.shade_opacity.valueChanged.connect(self.update_context_config)

        shade_group = make_group("Shade")
        shade_layout = QGridLayout()
        shade_layout.addWidget(QLabel("Color:"), 0, 0)
        shade_layout.addWidget(self.shade_color, 0, 1)
        shade_layout.addWidget(QLabel("Opacity:"), 1, 0)
        shade_layout.addWidget(self.shade_opacity, 1, 1)
        shade_layout.addWidget(QLabel("%"), 1, 2)
        shade_group.setLayout(shade_layout)
        left_layout.addWidget(shade_group)

        # Border
        self.border_color = create_color_combobox(PEN_COLORS)
        self.border_color.currentIndexChanged.connect(self.update_context_config)
        self.border_opacity = QSpinBox()

        self.border_opacity.setSizePolicy(QSizePolicy_Expanding, QSizePolicy_Fixed)
        self.border_opacity.valueChanged.connect(self.update_context_config)
        self.border_width = QSpinBox()

        self.border_width.setSizePolicy(QSizePolicy_Expanding, QSizePolicy_Fixed)
        self.border_width.valueChanged.connect(self.update_context_config)

        border_group = make_group("Border")
        border_layout = QGridLayout()
        border_layout.addWidget(QLabel("Color:"), 0, 0)
        border_layout.addWidget(self.border_color, 0, 1, 1, 2)
        border_layout.addWidget(QLabel("Opacity:"), 1, 0)
        border_layout.addWidget(self.border_opacity, 1, 1)
        border_layout.addWidget(QLabel("%"), 1, 2)
        border_layout.addWidget(QLabel("Width:"), 2, 0)
        border_layout.addWidget(self.border_width, 2, 1)
        border_layout.addWidget(QLabel("pixels"), 2, 2)
        border_group.setLayout(border_layout)
        right_layout.addWidget(border_group)

        # General abaixo
        general_group = make_group("General")
        general_layout = QHBoxLayout()

        # Lado esquerdo com checkboxes e botões
        left_side = QVBoxLayout()

        checkbox_layout = QVBoxLayout()
        self.general_always_capture_screenshot = QCheckBox("Always capture screenshot")
        self.general_always_capture_screenshot.stateChanged.connect(
            self.update_context_config
        )
        self.general_enable_auto_mode = QCheckBox("Enable AUTO mode if supported")
        self.general_enable_auto_mode.stateChanged.connect(self.update_context_config)
        checkbox_layout.addWidget(self.general_always_capture_screenshot)
        checkbox_layout.addWidget(self.general_enable_auto_mode)

        button_layout = QVBoxLayout()
        self.reset_button = QPushButton("Reset Settings")
        self.test_button = QPushButton("Show Test...")
        self.reset_button.setToolTip("Restaura as configurações padrão")
        self.test_button.setToolTip("Exibe a sobreposição de teste")
        self.reset_button.clicked.connect(self.on_reset_clicked)
        self.test_button.clicked.connect(self.on_test_clicked)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.test_button)

        left_side.addLayout(checkbox_layout)
        left_side.addLayout(button_layout)

        # Lado direito com a lista de modos
        self.modes_list = QListWidget()
        self.modes_list.setSelectionMode(
            QAbstractItemView_SelectionMode_SingleSelection
        )
        self.modes_list.setDragDropMode(QAbstractItemView_DragDropMode_InternalMove)
        self.modes_list.setDefaultDropAction(Qt_DropAction_MoveAction)
        self.modes_list.currentRowChanged.connect(self.on_mode_selected)

        if self.modes_list.count() == 0:
            for name, enabled in DEFAULT_MODES:
                item = QListWidgetItem(name)
                item.setFlags(
                    item.flags()
                    | Qt_ItemFlag_ItemIsUserCheckable
                    | Qt_ItemFlag_ItemIsEnabled
                    | Qt_ItemFlag_ItemIsSelectable
                    | Qt_ItemFlag_ItemIsDragEnabled
                    | Qt_ItemFlag_ItemIsDropEnabled
                )
                item.setCheckState(
                    Qt_CheckState_Checked if enabled else Qt_CheckState_Unchecked
                )
                self.modes_list.addItem(item)

        right_side = QVBoxLayout()
        right_side.addWidget(QLabel("Enabled Modes (drag to reorder):"))
        right_side.addWidget(self.modes_list)

        # Junta os lados
        general_layout.addLayout(left_side)
        general_layout.addLayout(right_side)
        general_group.setLayout(general_layout)

        main_layout.addLayout(self._side_by_side_layout(left_layout, right_layout))
        main_layout.addWidget(general_group)
        self.setLayout(main_layout)

        self._ctx.currentModeChanged.connect(self.on_context_mode_changed)

    def _side_by_side_layout(self, left, right):
        layout = QHBoxLayout()
        layout.addLayout(left)
        layout.addLayout(right)
        return layout

    def update_context_config(self):
        if self._ctx.ui_ready:
            cfg = self._ctx.config
            cfg["spotlight_shape"] = self.spotlight_shape.currentText()
            cfg["spotlight_size"] = self.spotlight_size.value()
            cfg["spotlight_border"] = self.spotlight_border.isChecked()
            cfg["spotlight_background_mode"] = self.spotlight_bg_mode.currentIndex()
            cfg["spotlight_background_blur_level"] = self.spotlight_bg_blur.value()
            cfg["magnify_shape"] = self.magnify_shape.currentText()
            cfg["magnify_size"] = self.magnify_size.value()
            cfg["magnify_border"] = self.magnify_border.isChecked()
            cfg["magnify_background_mode"] = self.magnify_bg_mode.currentIndex()
            cfg["magnify_zoom"] = self.magnify_zoom.value()
            cfg["magnify_background_blur_level"] = self.magnify_bg_blur.value()
            cfg["laser_dot_size"] = self.laser_dot_size.value()
            cfg["laser_color_index"] = self.laser_color.currentIndex()
            cfg["laser_opacity"] = self.laser_opacity.value()
            cfg["laser_reflection"] = self.laser_reflection.isChecked()
            cfg["marker_width"] = self.marker_width.value()
            cfg["marker_color_index"] = self.marker_color.currentIndex()
            cfg["marker_opacity"] = self.marker_opacity.value()
            cfg["shade_color_index"] = self.shade_color.currentIndex()
            cfg["shade_opacity"] = self.shade_opacity.value()
            cfg["border_color_index"] = self.border_color.currentIndex()
            cfg["border_opacity"] = self.border_opacity.value()
            cfg["border_width"] = self.border_width.value()
            cfg["general_always_capture"] = (
                self.general_always_capture_screenshot.isChecked()
            )
            cfg["general_auto_mode"] = self.general_enable_auto_mode.isChecked()
            cfg["modes_current_mode"] = self._ctx.current_mode

    def on_mode_selected(self, row):
        if row < 0 or row >= self.modes_list.count():
            return
        item = self.modes_list.item(row)
        name = item.text()  # pyright: ignore
        mode_id = MODE_NAME_TO_ID.get(name)
        if mode_id is not None and mode_id != self._ctx.current_mode:
            self._ctx.current_mode = mode_id
            self._ctx.log(f"> Modo alterado para: {name} (ID: {mode_id})")
            self.update_context_config()

    def on_context_mode_changed(self, mode_id):
        for i in range(self.modes_list.count()):
            item = self.modes_list.item(i)
            name = item.text()  # pyright: ignore
            mid = MODE_NAME_TO_ID.get(name)
            if mid == mode_id:
                self.modes_list.blockSignals(True)  # Evita disparar on_mode_selected
                self.modes_list.setCurrentRow(i)
                self.modes_list.blockSignals(False)
                break

    def update_modes_list_from_context(self):
        # Modo atual (para manter selecionado se ainda válido)
        current_mode_id = self._ctx.current_mode
        selected_row = -1

        self.modes_list.clear()

        for i, (name, mode_id) in enumerate(MODE_NAME_TO_ID.items()):
            item = QListWidgetItem(name)
            if mode_id in self._ctx.compatible_modes:
                # Modo compatível
                item.setFlags(
                    Qt_ItemFlag_ItemIsUserCheckable
                    | Qt_ItemFlag_ItemIsEnabled
                    | Qt_ItemFlag_ItemIsSelectable
                )
                item.setCheckState(Qt_CheckState_Checked)
            else:
                # Modo não compatível
                item.setFlags(
                    Qt_ItemFlag_NoItemFlags
                )  # total desativado (inclusive check)
            self.modes_list.addItem(item)

            if mode_id == current_mode_id:
                selected_row = i

        # Reposiciona a seleção para o modo atual
        if selected_row >= 0:
            self.modes_list.setCurrentRow(selected_row)

    def load_defaults(self):
        self.spotlight_size.setValue(35)
        self.spotlight_shape.setCurrentIndex(0)
        self.spotlight_bg_mode.setCurrentIndex(1)
        self.magnify_size.setValue(35)
        self.magnify_border.setChecked(True)
        self.magnify_shape.setCurrentIndex(0)
        self.magnify_bg_mode.setCurrentIndex(2)
        self.laser_dot_size.setValue(5)
        self.laser_opacity.setValue(60)
        self.laser_reflection.setChecked(True)
        self.marker_width.setValue(20)
        self.marker_opacity.setValue(90)
        self.marker_color.setCurrentIndex(1)
        self.shade_opacity.setValue(75)
        self.border_opacity.setValue(90)
        self.border_width.setValue(8)
        self.border_color.setCurrentIndex(7)  # White
        self.general_always_capture_screenshot.setChecked(False)
        self.general_enable_auto_mode.setChecked(True)

    def on_reset_clicked(self):
        resposta = QMessageBox.question(
            self,
            "Confirmation",
            "Are you sure to reset configuration to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            self.load_defaults()

    def on_test_clicked(self):
        if self._ctx.overlay_window is not None:
            self._ctx.overlay_window.show_overlay()

    def load_config(self, config: configparser.ConfigParser):
        def getint(section, key, fallback):
            return int(config.get(section, key, fallback=str(fallback)))

        def getbool(section, key, fallback):
            return config.getboolean(section, key, fallback=fallback)

        def getindex_by_text(combo, text):
            for i in range(combo.count()):
                if combo.itemText(i).lower() == text.lower():
                    return i
            return 0

        self.spotlight_shape.setCurrentIndex(
            getindex_by_text(
                self.spotlight_shape,
                config.get("Spotlight", "shape", fallback="elipse"),
            )
        )
        self.spotlight_size.setValue(getint("Spotlight", "size", 35))
        self.spotlight_border.setChecked(getbool("Spotlight", "border", True))
        self.spotlight_bg_blur.setValue(getint("Spotlight", "background_blur", 5))
        self.spotlight_bg_mode.setCurrentIndex(
            getint("Spotlight", "background_mode", 1)
        )

        self.magnify_shape.setCurrentIndex(
            getindex_by_text(
                self.magnify_shape,
                config.get("Magnify", "shape", fallback="rectangle"),
            )
        )
        self.magnify_size.setValue(getint("Magnify", "size", 35))
        self.magnify_border.setChecked(getbool("Magnify", "border", True))
        self.magnify_zoom.setValue(getint("Magnify", "zoom", 2))
        self.magnify_bg_blur.setValue(getint("Magnify", "background_blur", 5))

        self.magnify_bg_mode.setCurrentIndex(getint("Magnify", "background_mode", 2))

        self.laser_dot_size.setValue(getint("Laser", "dot_size", 5))
        self.laser_color.setCurrentIndex(getint("Laser", "color_index", 0))
        self.laser_opacity.setValue(getint("Laser", "opacity", 60))
        self.laser_reflection.setChecked(getbool("Laser", "reflection", True))

        self.marker_width.setValue(getint("Marker", "width", 20))
        self.marker_color.setCurrentIndex(getint("Marker", "color_index", 1))
        self.marker_opacity.setValue(getint("Marker", "opacity", 90))

        self.shade_color.setCurrentIndex(getint("Shade", "color_index", 0))
        self.shade_opacity.setValue(getint("Shade", "opacity", 95))

        self.border_color.setCurrentIndex(getint("Border", "color_index", 7))
        self.border_opacity.setValue(getint("Border", "opacity", 90))
        self.border_width.setValue(getint("Border", "width", 16))

        self.general_always_capture_screenshot.setChecked(
            getbool("General", "always_capture", True)
        )
        self.general_enable_auto_mode.setChecked(getbool("General", "auto_mode", True))

        # Carrega modos
        self.modes_list.clear()
        mode_id_to_name = MODE_MAP
        i = 0
        while True:
            key = f"mode{i}"
            if "Modes" not in config or key not in config["Modes"]:
                break
            try:
                raw = config["Modes"][key]
                mode_id_str, enabled_str = raw.split("|")
                mode_id = int(mode_id_str)
                enabled = bool(int(enabled_str))
                name = mode_id_to_name.get(mode_id, f"Unknown({mode_id})")
                item = QListWidgetItem(name)
                item.setFlags(
                    item.flags()
                    | Qt_ItemFlag_ItemIsUserCheckable
                    | Qt_ItemFlag_ItemIsEnabled
                    | Qt_ItemFlag_ItemIsSelectable
                )
                item.setCheckState(
                    Qt_CheckState_Checked if enabled else Qt_CheckState_Unchecked
                )
                self.modes_list.addItem(item)
            except Exception as e:
                self._ctx.log(f"Erro ao carregar modo '{raw}': {e}")
            i += 1

    def set_current_mode(self, current_mode: int):
        for i in range(self.modes_list.count()):
            item = self.modes_list.item(i)
            name = item.text()  # pyright: ignore
            mode_id = MODE_NAME_TO_ID.get(name)
            if mode_id == current_mode:
                self.modes_list.blockSignals(True)
                self.modes_list.setCurrentRow(i)
                self.modes_list.blockSignals(False)
                break

    def save_config(self, config: configparser.ConfigParser):
        config["Spotlight"] = {
            "shape": self.spotlight_shape.currentText(),
            "size": str(self.spotlight_size.value()),
            "border": str(self.spotlight_border.isChecked()),
            "background_mode": str(self.spotlight_bg_mode.currentIndex()),
            "background_blur": str(self.spotlight_bg_blur.value()),
        }
        config["Magnify"] = {
            "shape": self.magnify_shape.currentText(),
            "size": str(self.magnify_size.value()),
            "border": str(self.magnify_border.isChecked()),
            "background_mode": str(self.magnify_bg_mode.currentIndex()),
            "background_blur": str(self.magnify_bg_blur.value()),
            "zoom": str(self.magnify_zoom.value()),
        }
        config["Laser"] = {
            "dot_size": str(self.laser_dot_size.value()),
            "color_index": str(self.laser_color.currentIndex()),
            "opacity": str(self.laser_opacity.value()),
            "reflection": str(self.laser_reflection.isChecked()),
        }
        config["Marker"] = {
            "width": str(self.marker_width.value()),
            "color_index": str(self.marker_color.currentIndex()),
            "opacity": str(self.marker_opacity.value()),
        }
        config["Shade"] = {
            "color_index": str(self.shade_color.currentIndex()),
            "opacity": str(self.shade_opacity.value()),
        }
        config["Border"] = {
            "color_index": str(self.border_color.currentIndex()),
            "opacity": str(self.border_opacity.value()),
            "width": str(self.border_width.value()),
        }
        config["General"] = {
            "always_capture": str(self.general_always_capture_screenshot.isChecked()),
            "auto_mode": str(self.general_enable_auto_mode.isChecked()),
        }

        config["Modes"] = {}

        for i in range(self.modes_list.count()):
            item = self.modes_list.item(i)
            name = item.text()  # pyright: ignore
            mode_id = MODE_NAME_TO_ID.get(name)
            if mode_id is not None:
                enabled = item.checkState() == Qt_CheckState_Checked  # pyright: ignore
                config["Modes"][f"mode{i}"] = f"{mode_id}|{int(enabled)}"

        selected_items = self.modes_list.selectedItems()
        if selected_items:
            selected_name = selected_items[0].text()
            current_id = MODE_NAME_TO_ID.get(selected_name)
            if current_id is not None:
                config["Modes"]["current_mode"] = str(current_id)
