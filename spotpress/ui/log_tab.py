from datetime import datetime
from spotpress.qtcompat import (
    QApplication,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QFileDialog,
    QMessageBox,
)


class LogTab(QWidget):
    def __init__(self, parent, ctx):
        super().__init__(parent)
        self._ctx = ctx
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Log...")
        clear_btn = QPushButton("Clear Log")
        copy_btn = QPushButton("Copy to clipboard!")
        save_btn.setToolTip("Salvar o log em um arquivo")
        clear_btn.setToolTip("Limpar o conteúdo do log")
        copy_btn.setToolTip("Copiar log para a área de transferência")
        button_layout.addWidget(copy_btn)
        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        button_layout.addWidget(clear_btn)
        clear_btn.clicked.connect(self.on_clear_log_clicked)
        save_btn.clicked.connect(self.on_save_log_clicked)
        copy_btn.clicked.connect(self.on_copy_to_clipboard_clicked)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def append_log_message(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        # timestamp = f"{time.time():.3f}"
        self.log_text.append(f"{timestamp} - {message}")

    def on_clear_log_clicked(self):
        self.log_text.clear()

    def on_save_log_clicked(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Log File", "", "Text Files (*.txt);;All Files (*)"
        )
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as file:
                    file.write(self.log_text.toPlainText())
            except Exception as e:
                QMessageBox.critical(
                    self, "Erro ao salvar", f"Não foi possível salvar o log:\n{e}"
                )

    def on_copy_to_clipboard_clicked(self):
        if not self.log_text.toPlainText().strip():
            QMessageBox.information(self, "Sem conteúdo", "O log está vazio.")
            return
        clipboard = QApplication.clipboard()
        clipboard.setText(self.log_text.toPlainText())
