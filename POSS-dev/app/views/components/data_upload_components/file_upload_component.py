from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QFileDialog, QFrame
from PyQt5.QtGui import QCursor, QFont

import os
from app.models.common.file_store import FilePaths
from app.resources.fonts.font_manager import font_manager
from app.models.common.settings_store import SettingsStore
from app.models.common.screen_manager import *

"""
파일 업로드 컴포넌트
파일 선택, 표시, 제거 기능을 제공합니다.
"""
class FileUploadComponent(QWidget):
    file_selected = pyqtSignal(str)  # 파일이 선택되었을 때 발생하는 시그널
    file_removed = pyqtSignal(str)  # 파일이 제거되었을 때 발생하는 시그널

    def __init__(self, parent=None, label_text="Upload Data:", button_text="Browse"):
        super().__init__(parent)
        self.file_paths = []
        self.no_files_label = None
        self.label_text = label_text
        self.button_text = button_text
        self.init_ui()

    def init_ui(self):
        # 메인 레이아웃
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.layout.setSpacing(5)

        # 라벨
        upload_label = QLabel(self.label_text)
        upload_label.setFont(QFont(font_manager.get_just_font("SamsungOne-700").family()))
        upload_label.setStyleSheet("border: none")
        self.layout.addWidget(upload_label)

        # 파일명들을 표시할 영역
        files_container = QWidget()
        files_container.setStyleSheet(f" height: {h(30)}px;")
        self.files_display = QHBoxLayout(files_container)
        self.files_display.setContentsMargins(3, 3, 3, 3)
        self.files_display.setSpacing(5)
        self.files_display.setAlignment(Qt.AlignLeft)


        # 안내 텍스트 표시
        self.no_files_label = QLabel("No files selected")
        self.no_files_label.setFont(QFont(font_manager.get_just_font("SamsungOne-700").family()))
        self.no_files_label.setStyleSheet("color: #888888; border:none; background-color: transparent; margin-left:5px")
        self.files_display.addWidget(self.no_files_label)
        self.files_display.addStretch(1)

        # 파일 선택 버튼
        browse_btn = QPushButton(self.button_text)

        browse_btn.clicked.connect(self.on_file_btn_clicked)
        browse_btn.setCursor(QCursor(Qt.PointingHandCursor))
        browse_btn_font = font_manager.get_just_font("SamsungOne-700").family()
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #1428A0; 
                color: white; 
                border: none;
                border-radius: 0px;
                padding: {w(5)}px {h(8)}px;
                font-family : {browse_btn_font};
                font-size: {f(13)}px;
                font-weight: bold;
                min-width: {w(60)}px;
                height : {h(30)}px;
            }}
            QPushButton:hover {{
                background-color: #004C99;
            }}
            QPushButton:pressed {{
                background-color: #003366;
            }}
        """)

        self.layout.addWidget(files_container)
        self.layout.addWidget(browse_btn)

    """
    파일 라벨 추가
    """
    def add_file_label(self, file_path):
        if self.no_files_label:
            self.files_display.removeWidget(self.no_files_label)
            self.no_files_label.deleteLater()
            self.no_files_label = None

        for i in range(self.files_display.count() - 1, -1, -1):
            if self.files_display.itemAt(i).spacerItem():
                self.files_display.removeItem(self.files_display.itemAt(i))

        file_name = file_path.split('/')[-1]

        # 파일 라벨 생성
        file_frame = QFrame()
        file_frame.setStyleSheet("QFrame { background-color: #e0e0ff; border-radius: 0px; border:none; padding: 1px; }")
        file_frame.setFixedHeight(h(22))

        file_layout = QHBoxLayout(file_frame)
        file_layout.setContentsMargins(3, 0, 3, 0)
        file_layout.setSpacing(2)

        file_label = QLabel(file_name)
        file_label_font = font_manager.get_just_font("SamsungOne-700").family()
        file_label.setStyleSheet(f"border: none; font-size : {f(12)}px; font-family: {file_label_font};")

        remove_btn = QPushButton("X")
        remove_btn.setFixedSize(16, 16)
        remove_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #555; border: none; font-weight: bold; } "
            "QPushButton:hover { color: red; }")
        remove_btn.clicked.connect(lambda: self.remove_file(file_path, file_frame))
        remove_btn.setCursor(QCursor(Qt.PointingHandCursor))

        file_layout.addWidget(file_label)
        file_layout.addWidget(remove_btn)

        self.files_display.addWidget(file_frame)

        self.file_paths.append(file_path)

        self.file_selected.emit(file_path)

        self.files_display.addStretch(1)

        return file_frame

    """
    파일 제거
    """
    def remove_file(self, file_path, file_frame):
        self.files_display.removeWidget(file_frame)
        file_frame.deleteLater()

        # 남아있는 위젯 중 spacerItem(stretch)을 확인하고 제거
        if self.file_paths.count(file_path) == 1:  # 이 파일이 마지막으로 제거될 예정이라면
            # 모든 stretch 항목 찾아서 제거
            for i in range(self.files_display.count() - 1, -1, -1):
                if self.files_display.itemAt(i).spacerItem():
                    self.files_display.removeItem(self.files_display.itemAt(i))

        # 파일 경로 목록에서 제거
        if file_path in self.file_paths:
            self.file_paths.remove(file_path)
            self.file_removed.emit(file_path)

        # 파일이 남아 있으면 마지막에 다시 stretch 추가
        if self.file_paths and len(self.file_paths) > 0:
            self.files_display.addStretch(1)

        # 모든 파일이 제거되면 안내 텍스트 다시 표시
        if not self.file_paths and not self.no_files_label:
            while self.files_display.count():
                item = self.files_display.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            self.no_files_label = QLabel("No files selected")
            self.no_files_label.setFont(QFont(font_manager.get_just_font("SamsungOne-700").family()))
            self.no_files_label.setStyleSheet("color: #888888; border: none; background-color: transparent; margin-left:5px")

            self.files_display.addWidget(self.no_files_label)
            self.files_display.addStretch(1)

    """
    파일 선택 다이얼로그 표시 - 여러 파일 선택 가능
    """
    def on_file_btn_clicked(self):
        input_route = SettingsStore.get('op_InputRoute', '')

        initial_dir = input_route if input_route and os.path.isdir(input_route) else ''

        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Data File Select (Multiple file selection available)",  # 제목도 변경
            initial_dir,
            "Data Files (*.xlsx *.xls *.csv);;Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;All Files (*)"
        )

        # 선택된 파일들 처리
        for file_path in file_paths:
            file_name = os.path.basename(file_path).lower()
            file_type = None

            if "demand" in file_name:
                file_type = "demand_excel_file"
            elif "dynamic" in file_name:
                file_type = "dynamic_excel_file"
            elif "master" in file_name:
                file_type = "master_excel_file"
            elif "result" in file_name:
                file_type = "result_file"
            elif "pre_assign" in file_name:
                file_type = "pre_assign_excel_file"
            else:
                file_type = "etc_excel_file"

            old_file_path = None

            if file_type :
                old_file_path = FilePaths.get(file_type)

            if old_file_path and old_file_path in self.file_paths :
                self.file_removed.emit(old_file_path)

                for i in range(self.files_display.count()) :
                    item = self.files_display.itemAt(i)

                    if item and item.widget() :
                        widget = item.widget()

                        if hasattr(widget, 'findChild') :
                            label = widget.findChild(QLabel)

                            if label and os.path.basename(old_file_path) in label.text() :
                                self.files_display.removeWidget(widget)
                                widget.deleteLater()
                                break

                if old_file_path in self.file_paths :
                    self.file_paths.remove(old_file_path)

            if file_path not in self.file_paths :
                self.add_file_label(file_path)

    """
    선택된 파일 경로 리스트 반환
    """
    def get_file_paths(self):
        return self.file_paths