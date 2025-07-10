import configparser
from spotpress.qtcompat import (
    QAbstractItemView,
    QMessageBox,
    QSizePolicy,
    QListWidgetItem,
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
    QIcon,
    QPixmap,
    QColor,
    Qt_CheckState_Checked,
    Qt_CheckState_Unchecked,
    Qt_DropAction_MoveAction,
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
            #     "QGroupBox { background-color: #f0f0f0; border: 2px solid lightgray; margin-top: 1ex; }"
            # )
            box.setStyleSheet(
                "QGroupBox { background-color: #f4f4f4; border: 1px solid #ccc; border-radius: 4px; margin-top: 1ex; padding: 6px; }"
            )
            return box

        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Spotlight
        self.spotlight_shape = QComboBox()
        self.spotlight_shape.addItem("Elipse")
        self.spotlight_shape.addItem("Rectangle")
        self.spotlight_shape.currentIndexChanged.connect(
            self.on_spotlight_shape_changed
        )
        self.spotlight_size = QSpinBox()
        self.spotlight_size.setMaximum(99)
        self.spotlight_size.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.spotlight_size.valueChanged.connect(self.on_spotlight_size_changed)
        self.spotlight_shade = QCheckBox("Show shade")
        self.spotlight_shade.stateChanged.connect(self.on_spotlight_shade_changed)
        self.spotlight_border = QCheckBox("Show border")
        self.spotlight_border.stateChanged.connect(self.on_spotlight_border_changed)

        spotlight_group = make_group("Spotlight")
        spotlight_layout = QGridLayout()
        spotlight_layout.addWidget(QLabel("Shape:"), 0, 0)
        spotlight_layout.addWidget(self.spotlight_shape, 0, 1, 1, 2)
        spotlight_layout.addWidget(QLabel("Size:"), 1, 0)
        spotlight_layout.addWidget(self.spotlight_size, 1, 1)
        spotlight_layout.addWidget(QLabel("% of screen height"), 1, 2)
        spotlight_layout.addWidget(self.spotlight_shade, 2, 0, 1, 2)
        spotlight_layout.addWidget(self.spotlight_border, 2, 2)
        spotlight_group.setLayout(spotlight_layout)
        left_layout.addWidget(spotlight_group)

        # Magnifyer
        self.magnify_shape = QComboBox()

        self.magnify_shape.addItem("Elipse")
        self.magnify_shape.addItem("Rectangle")
        self.magnify_shape.currentIndexChanged.connect(self.on_magnify_shape_changed)
        self.magnify_size = QSpinBox()
        self.magnify_size.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.magnify_size.valueChanged.connect(self.on_magnify_size_changed)
        self.magnify_border = QCheckBox("Show border")
        self.magnify_border.stateChanged.connect(self.on_magnify_border_changed)
        self.magnify_zoom = QSpinBox()
        self.magnify_zoom.setMaximum(5)
        self.magnify_zoom.setMinimum(2)
        self.magnify_zoom.valueChanged.connect(self.on_magnify_zoom_changed)

        magnify_group = make_group("Magnifier")
        magnify_layout = QGridLayout()
        magnify_layout.addWidget(QLabel("Shape:"), 0, 0)
        magnify_layout.addWidget(self.magnify_shape, 0, 1, 1, 2)
        magnify_layout.addWidget(QLabel("Size:"), 1, 0)
        magnify_layout.addWidget(self.magnify_size, 1, 1)
        magnify_layout.addWidget(QLabel("% of screen height"), 1, 2)
        magnify_layout.addWidget(self.magnify_border, 2, 0, 1, 3)
        magnify_layout.addWidget(QLabel("Zoom level:"), 3, 0)
        magnify_layout.addWidget(self.magnify_zoom, 3, 1, 1, 2)
        magnify_group.setLayout(magnify_layout)
        left_layout.addWidget(magnify_group)

        # Laser
        self.laser_dot_size = QSpinBox()

        self.laser_dot_size.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.laser_dot_size.valueChanged.connect(self.on_laser_dot_size_changed)
        self.laser_color = create_color_combobox(LASER_COLORS)
        self.laser_color.currentIndexChanged.connect(self.on_laser_color_changed)
        self.laser_opacity = QSpinBox()

        self.laser_opacity.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        self.laser_opacity.valueChanged.connect(self.on_laser_opacity_changed)
        self.laser_reflection = QCheckBox("Show reflection")
        self.laser_reflection.stateChanged.connect(self.on_laser_reflection_changed)

        laser_group = make_group("Laser")
        laser_layout = QGridLayout()
        laser_layout.addWidget(QLabel("Dot size:"), 0, 0)
        laser_layout.addWidget(self.laser_dot_size, 0, 1)
        laser_layout.addWidget(QLabel("% of screen height"), 0, 2)
        laser_layout.addWidget(QLabel("Dot color:"), 1, 0)
        laser_layout.addWidget(self.laser_color, 1, 1, 1, 2)
        laser_layout.addWidget(QLabel("Opacity:"), 2, 0)
        laser_layout.addWidget(self.laser_opacity, 2, 1)
        laser_layout.addWidget(QLabel("%"), 2, 2)
        laser_layout.addWidget(self.laser_reflection, 3, 0, 1, 3)
        laser_group.setLayout(laser_layout)
        left_layout.addWidget(laser_group)

        # Marker
        self.marker_width = QSpinBox()

        self.marker_width.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.marker_width.valueChanged.connect(self.on_marker_width_changed)
        self.marker_color = create_color_combobox(PEN_COLORS)
        self.marker_color.currentIndexChanged.connect(self.on_marker_color_changed)
        self.marker_opacity = QSpinBox()

        self.marker_opacity.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.marker_opacity.valueChanged.connect(self.on_marker_opacity_changed)

        marker_group = make_group("Marker")
        marker_layout = QGridLayout()
        marker_layout.addWidget(QLabel("Width:"), 0, 0)
        marker_layout.addWidget(self.marker_width, 0, 1)
        marker_layout.addWidget(QLabel("pixels"), 0, 2)
        marker_layout.addWidget(QLabel("Color:"), 1, 0)
        marker_layout.addWidget(self.marker_color, 1, 1, 1, 2)
        marker_layout.addWidget(QLabel("Opacity:"), 2, 0)
        marker_layout.addWidget(self.marker_opacity, 2, 1)
        marker_layout.addWidget(QLabel("%"), 2, 2)
        marker_group.setLayout(marker_layout)
        right_layout.addWidget(marker_group)

        # Shade
        self.shade_color = create_named_color_combobox(SHADE_COLORS)
        self.shade_color.currentIndexChanged.connect(self.on_shade_color_changed)
        self.shade_opacity = QSpinBox()

        self.shade_opacity.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.shade_opacity.valueChanged.connect(self.on_shade_opacity_changed)

        shade_group = make_group("Shade")
        shade_layout = QGridLayout()
        shade_layout.addWidget(QLabel("Color:"), 0, 0)
        shade_layout.addWidget(self.shade_color, 0, 1, 1, 2)
        shade_layout.addWidget(QLabel("Opacity:"), 1, 0)
        shade_layout.addWidget(self.shade_opacity, 1, 1)
        shade_layout.addWidget(QLabel("%"), 1, 2)
        shade_group.setLayout(shade_layout)
        right_layout.addWidget(shade_group)

        # Border
        self.border_color = create_color_combobox(PEN_COLORS)
        self.border_color.currentIndexChanged.connect(self.on_border_color_changed)
        self.border_opacity = QSpinBox()

        self.border_opacity.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.border_opacity.valueChanged.connect(self.on_border_opacity_changed)
        self.border_width = QSpinBox()

        self.border_width.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.border_width.valueChanged.connect(self.on_border_width_changed)

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

        checkbox_layout = QHBoxLayout()
        self.general_always_capture_screenshot = QCheckBox("Always capture screenshot")
        self.general_always_capture_screenshot.stateChanged.connect(
            self.on_general_always_capture_screenshot_changed
        )
        self.general_enable_auto_mode = QCheckBox("Enable AUTO mode if supported")
        self.general_enable_auto_mode.stateChanged.connect(
            self.on_general_enable_auto_mode_changed
        )
        checkbox_layout.addWidget(self.general_always_capture_screenshot)
        checkbox_layout.addWidget(self.general_enable_auto_mode)

        button_layout = QHBoxLayout()
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
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.modes_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
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
            cfg["spotlight_shade"] = self.spotlight_shade.isChecked()
            cfg["spotlight_border"] = self.spotlight_border.isChecked()
            cfg["magnify_shape"] = self.magnify_shape.currentText()
            cfg["magnify_size"] = self.magnify_size.value()
            cfg["magnify_border"] = self.magnify_border.isChecked()
            cfg["magnify_zoom"] = self.magnify_zoom.value()
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
        name = item.text()
        mode_id = MODE_NAME_TO_ID.get(name)
        if mode_id is not None and mode_id != self._ctx.current_mode:
            self._ctx.current_mode = mode_id
            self._ctx.log(f"> Modo alterado para: {name} (ID: {mode_id})")
            self.update_context_config()

    def on_context_mode_changed(self, mode_id):
        for i in range(self.modes_list.count()):
            item = self.modes_list.item(i)
            name = item.text()
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

    def on_spotlight_shape_changed(self):
        self.update_context_config()

    def on_spotlight_size_changed(self):
        self.update_context_config()

    def on_spotlight_shade_changed(self):
        self.update_context_config()

    def on_spotlight_border_changed(self):
        self.update_context_config()

    def on_magnify_shape_changed(self):
        self.update_context_config()

    def on_magnify_size_changed(self):
        self.update_context_config()

    def on_magnify_border_changed(self):
        self.update_context_config()

    def on_magnify_zoom_changed(self):
        self.update_context_config()

    def on_laser_dot_size_changed(self):
        self.update_context_config()

    def on_laser_color_changed(self):
        self.update_context_config()

    def on_laser_opacity_changed(self):
        self.update_context_config()

    def on_laser_reflection_changed(self):
        self.update_context_config()

    def on_marker_width_changed(self):
        self.update_context_config()

    def on_marker_color_changed(self):
        self.update_context_config()

    def on_marker_opacity_changed(self):
        self.update_context_config()

    def on_shade_color_changed(self):
        self.update_context_config()

    def on_shade_opacity_changed(self):
        self.update_context_config()

    def on_border_color_changed(self):
        self.update_context_config()

    def on_border_opacity_changed(self):
        self.update_context_config()

    def on_border_width_changed(self):
        self.update_context_config()

    def on_general_always_capture_screenshot_changed(self):
        self.update_context_config()

    def on_general_enable_auto_mode_changed(self):
        self.update_context_config()

    def on_reset_clicked(self):
        resposta = QMessageBox.question(
            self,
            "Confirmation",
            "Are you sure to reset configuration to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if resposta == QMessageBox.StandardButton.Yes:
            self.spotlight_size.setValue(35)
            self.spotlight_shade.setChecked(True)
            self.spotlight_shape.setCurrentIndex(0)
            self.magnify_size.setValue(35)
            self.magnify_border.setChecked(True)
            self.magnify_shape.setCurrentIndex(1)
            self.laser_dot_size.setValue(20)
            self.laser_opacity.setValue(10)
            self.laser_reflection.setChecked(True)
            self.marker_width.setValue(20)
            self.marker_opacity.setValue(0)
            self.marker_color.setCurrentIndex(1)
            self.shade_opacity.setValue(5)
            self.border_opacity.setValue(90)
            self.border_width.setValue(16)
            self.border_color.setCurrentIndex(7)  # White
            self.general_always_capture_screenshot.setChecked(True)
            self.general_enable_auto_mode.setChecked(True)

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
        self.spotlight_shade.setChecked(getbool("Spotlight", "shade", True))
        self.spotlight_border.setChecked(getbool("Spotlight", "border", True))

        self.magnify_shape.setCurrentIndex(
            getindex_by_text(
                self.magnify_shape,
                config.get("Magnify", "shape", fallback="rectangle"),
            )
        )
        self.magnify_size.setValue(getint("Magnify", "size", 35))
        self.magnify_border.setChecked(getbool("Magnify", "border", True))
        self.magnify_zoom.setValue(getint("Magnify", "zoom", 2))

        self.laser_dot_size.setValue(getint("Laser", "dot_size", 20))
        self.laser_color.setCurrentIndex(getint("Laser", "color_index", 0))
        self.laser_opacity.setValue(getint("Laser", "opacity", 10))
        self.laser_reflection.setChecked(getbool("Laser", "reflection", True))

        self.marker_width.setValue(getint("Marker", "width", 20))
        self.marker_color.setCurrentIndex(getint("Marker", "color_index", 1))
        self.marker_opacity.setValue(getint("Marker", "opacity", 0))

        self.shade_color.setCurrentIndex(getint("Shade", "color_index", 0))
        self.shade_opacity.setValue(getint("Shade", "opacity", 5))

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
            name = item.text()
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
            "shade": str(self.spotlight_shade.isChecked()),
            "border": str(self.spotlight_border.isChecked()),
        }
        config["Magnify"] = {
            "shape": self.magnify_shape.currentText(),
            "size": str(self.magnify_size.value()),
            "border": str(self.magnify_border.isChecked()),
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
            name = item.text()
            mode_id = MODE_NAME_TO_ID.get(name)
            if mode_id is not None:
                enabled = item.checkState() == Qt_CheckState_Checked
                config["Modes"][f"mode{i}"] = f"{mode_id}|{int(enabled)}"

        selected_items = self.modes_list.selectedItems()
        if selected_items:
            selected_name = selected_items[0].text()
            current_id = MODE_NAME_TO_ID.get(selected_name)
            if current_id is not None:
                config["Modes"]["current_mode"] = str(current_id)
