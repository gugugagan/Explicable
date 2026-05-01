from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .ai_client import AIClient
from .csv_loader import load_words_from_csv, preview_words
from .grouper import group_words
from .json_exporter import export_group_configs
from .markdown_exporter import export_markdown
from .models import GenerationResult, VocabWord, WordGroup
from .prompt_builder import build_prompt


class CsvDropLineEdit(QLineEdit):
    file_dropped = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setReadOnly(True)
        self.setPlaceholderText("选择或拖拽 CSV 文件")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if _first_local_csv(event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        path = _first_local_csv(event.mimeData().urls())
        if path:
            self.file_dropped.emit(path)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.words: list[VocabWord] = []
        self.groups: list[WordGroup] = []
        self.results: list[GenerationResult] = []

        self.project_root = get_app_root()
        self.output_dir = self.project_root / "output"
        self.config_dir = self.output_dir / "configs"
        self.markdown_path = self.output_dir / "vocabulary_plan.md"

        self.setWindowTitle("Anki Vocabulary Sentence Generator")
        self.resize(980, 720)
        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)

        file_row = QHBoxLayout()
        self.csv_path_edit = CsvDropLineEdit()
        self.csv_path_edit.file_dropped.connect(self.load_csv)
        browse_button = QPushButton("选择 CSV 文件")
        browse_button.clicked.connect(self.select_csv)
        file_row.addWidget(QLabel("CSV 文件"))
        file_row.addWidget(self.csv_path_edit, stretch=1)
        file_row.addWidget(browse_button)
        layout.addLayout(file_row)

        self.summary_label = QLabel("尚未导入 CSV。")
        layout.addWidget(self.summary_label)

        self.preview_table = QTableWidget(0, 3)
        self.preview_table.setHorizontalHeaderLabels(["Word", "POS", "Chinese Meaning"])
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.preview_table, stretch=1)

        form = QFormLayout()
        self.daily_count_spin = QSpinBox()
        self.daily_count_spin.setRange(1, 500)
        self.daily_count_spin.setValue(10)
        form.addRow("每日背词数量", self.daily_count_spin)

        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["easy", "medium", "hard"])
        self.difficulty_combo.setCurrentText("medium")
        form.addRow("AI 难度", self.difficulty_combo)
        layout.addLayout(form)

        action_row = QHBoxLayout()
        self.config_button = QPushButton("生成配置文件")
        self.config_button.clicked.connect(self.generate_configs)
        self.markdown_button = QPushButton("生成 Markdown")
        self.markdown_button.clicked.connect(self.generate_markdown)
        action_row.addWidget(self.config_button)
        action_row.addWidget(self.markdown_button)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        output_row = QHBoxLayout()
        self.output_path_edit = QLineEdit(str(self.output_dir))
        self.output_path_edit.setReadOnly(True)
        open_output_button = QPushButton("打开输出文件夹")
        open_output_button.clicked.connect(self.open_output_folder)
        output_row.addWidget(QLabel("输出路径"))
        output_row.addWidget(self.output_path_edit, stretch=1)
        output_row.addWidget(open_output_button)
        layout.addLayout(output_row)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(120)
        layout.addWidget(self.log_text)

        self.setCentralWidget(central)

    def select_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 CSV 文件",
            str(self.project_root),
            "CSV Files (*.csv);;All Files (*)",
        )
        if path:
            self.load_csv(path)

    def load_csv(self, path: str) -> None:
        try:
            words = load_words_from_csv(path)
        except Exception as exc:
            self._show_error("CSV 导入失败", str(exc))
            return

        self.words = words
        self.groups = []
        self.results = []
        self.csv_path_edit.setText(path)
        self.summary_label.setText(
            f"已解析 {len(words)} 个单词，预览前 {min(len(words), 20)} 条。"
        )
        self._fill_preview(words)
        self._log(f"CSV 导入成功：{path}")

    def generate_configs(self) -> None:
        if self._generate_configs(show_message=True):
            self._log(f"配置文件已输出到：{self.config_dir}")

    def generate_markdown(self) -> None:
        if not self._generate_configs(show_message=False):
            return

        difficulty = self.difficulty_combo.currentText()
        client = AIClient()
        self._log(f"开始生成 Markdown，AI 模式：{client.mode_name}")

        self.markdown_button.setEnabled(False)
        self.config_button.setEnabled(False)
        results: list[GenerationResult] = []

        try:
            for group in self.groups:
                QApplication.processEvents()
                result = client.generate_for_group(group, difficulty)
                results.append(result)
                if result.error:
                    self._log(f"Day {group.group_id}: {result.error}")
                else:
                    self._log(f"Day {group.group_id}: 生成完成")

            markdown_path = export_markdown(results, self.markdown_path)
            self.results = results
            self.output_path_edit.setText(str(markdown_path))
            self._log(f"Markdown 已输出：{markdown_path}")
            QMessageBox.information(self, "完成", f"Markdown 已生成：\n{markdown_path}")
        except Exception as exc:
            self._show_error("Markdown 生成失败", str(exc))
        finally:
            self.markdown_button.setEnabled(True)
            self.config_button.setEnabled(True)

    def open_output_folder(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.output_dir)))

    def _generate_configs(self, show_message: bool) -> bool:
        if not self.words:
            self._show_error("缺少 CSV", "请先导入包含 word 和 pos 字段的 CSV 文件。")
            return False

        daily_count = self.daily_count_spin.value()
        difficulty = self.difficulty_combo.currentText()

        try:
            groups = group_words(self.words, daily_count)
            for group in groups:
                group.prompt = build_prompt(group, difficulty)
            paths = export_group_configs(groups, self.config_dir)
        except Exception as exc:
            self._show_error("配置文件生成失败", str(exc))
            return False

        self.groups = groups
        self.output_path_edit.setText(str(self.output_dir))
        self._log(f"已生成 {len(paths)} 个配置文件。")
        if show_message:
            QMessageBox.information(
                self,
                "完成",
                f"已生成 {len(paths)} 个配置文件：\n{self.config_dir}",
            )
        return True

    def _fill_preview(self, words: list[VocabWord]) -> None:
        rows = preview_words(words)
        self.preview_table.setRowCount(len(rows))
        for row_index, word in enumerate(rows):
            self.preview_table.setItem(row_index, 0, QTableWidgetItem(word.word))
            self.preview_table.setItem(row_index, 1, QTableWidgetItem(word.pos))
            self.preview_table.setItem(
                row_index,
                2,
                QTableWidgetItem(word.chinese_meaning),
            )
        self.preview_table.resizeColumnsToContents()
        self.preview_table.horizontalHeader().setStretchLastSection(True)

    def _show_error(self, title: str, message: str) -> None:
        self._log(f"{title}: {message}")
        QMessageBox.critical(self, title, message)

    def _log(self, message: str) -> None:
        self.log_text.append(message)


def _first_local_csv(urls: list[QUrl]) -> str | None:
    for url in urls:
        if not url.isLocalFile():
            continue
        path = Path(url.toLocalFile())
        if path.suffix.lower() == ".csv":
            return str(path)
    return None


def get_app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def run_app() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
