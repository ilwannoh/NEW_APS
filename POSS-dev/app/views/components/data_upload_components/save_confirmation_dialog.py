from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QWidget, QScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QCursor
from app.models.common.screen_manager import *
from app.resources.fonts.font_manager import font_manager


class SaveConfirmationDialog(QDialog):
    """변경 사항이 있을 때 저장 여부를 묻는 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Changes")

        # 화면 크기 비율로 설정 - 픽셀 값 전달
        self.setFixedSize(w(633), h(320))  # FHD에서 33%, 45% 크기에 해당하는 픽셀 값
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.result_choice = None
        self.init_ui()

    def init_ui(self):
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 제목 프레임
        title_frame = QFrame()
        title_frame.setFrameShape(QFrame.StyledPanel)
        title_frame.setStyleSheet(f"min-height : {h(45)}; background-color: #1428A0; border: none;")

        # 제목 프레임 레이아웃
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(w(20), 0, w(20), 0)
        title_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # 제목 레이블
        title_label = QLabel("Save Changes")
        title_font = font_manager.get_just_font("SamsungSharpSans-Bold").family()
        title_label.setStyleSheet(f"color: white; font-family:{title_font}; font-size : {f(20)}px;")
        title_layout.addWidget(title_label)

        # 메인 레이아웃에 제목 프레임 추가
        main_layout.addWidget(title_frame)

        # 콘텐츠 영역
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(w(30), h(30), w(30), h(30))
        content_layout.setSpacing(h(20))

        # 스크롤 영역 생성
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background-color: #F5F5F5; border: none;")
        scroll_area.setWidget(content_widget)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 데이터 표시 프레임
        data_frame = QFrame()
        data_frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: {w(10)}px;
                border: 1px solid #cccccc;
            }}
        """)
        data_layout = QVBoxLayout(data_frame)
        data_layout.setContentsMargins(w(20), h(20), w(20), h(20))
        data_layout.setSpacing(h(15))

        # 메시지 레이블
        message_label = QLabel("Modifications have been detected. Do you wish to save them to the original file?")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"color: #333333; border: none; font-size: {f(20)}px; font-family:{title_font};")

        # 설명 레이블
        description_label = QLabel(
            "Selecting 'Save and Run' will save your changes to the original file.\nSelecting 'Run without Saving' will keep the original file intact.")
        description_label_font = font_manager.get_just_font("SamsungOne-700").family()
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setWordWrap(True)
        description_label.setStyleSheet(f"color: #666666; border:none; font-size: {f(16)}px; font-family:{description_label_font}; ")

        # 데이터 레이아웃에 레이블 추가
        data_layout.addWidget(message_label)
        data_layout.addWidget(description_label)

        # 콘텐츠 레이아웃에 데이터 프레임 추가
        content_layout.addWidget(data_frame)
        content_layout.addStretch(1)  # 남은 공간 채우기

        # 메인 레이아웃에 스크롤 영역 추가
        main_layout.addWidget(scroll_area)

        # 버튼 프레임
        button_frame = QFrame()
        button_frame.setStyleSheet("background-color: #F0F0F0; border: none;")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, h(10), w(30), h(10))

        # 저장 후 실행 버튼
        save_and_run_btn = QPushButton("Save and Run")

        save_and_run_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #1428A0;
                border: none;
                color: white;
                border-radius: {w(10)}px;
                width: {w(150)}px;
                height: {h(40)}px;
                font-family:{description_label_font};
                font-size: {f(14)}px;
            }}
            QPushButton:hover {{
                background-color: #1e429f;
                border: none;
                color: white;
            }}
        """)
        save_and_run_btn.setCursor(QCursor(Qt.PointingHandCursor))
        save_and_run_btn.clicked.connect(self.on_save_and_run)

        # 저장 안하고 실행 버튼
        run_without_save_btn = QPushButton("Run without Save")
        run_without_save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #f0f0f0;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: {w(10)}px;
                width: {w(170)}px;
                height: {h(40)}px;
                font-family:{description_label_font};
                font-size: {f(14)}px;
            }}
            QPushButton:hover {{
                background-color: #e0e0e0;
            }}
        """)
        run_without_save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        run_without_save_btn.clicked.connect(self.on_run_without_save)

        # 취소 버튼
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #f0f0f0;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: {w(10)}px;
                width: {w(100)}px;
                height: {h(40)}px;
                font-family:{description_label_font};
                font-size: {f(14)}px;
            }}
            QPushButton:hover {{
                background-color: #e0e0e0;
            }}
        """)
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.clicked.connect(self.on_cancel)

        # 버튼 레이아웃에 버튼 추가
        button_layout.addStretch(1)  # 왼쪽 여백
        button_layout.addWidget(save_and_run_btn)
        button_layout.addWidget(run_without_save_btn)
        button_layout.addWidget(cancel_btn)

        # 메인 레이아웃에 버튼 프레임 추가
        main_layout.addWidget(button_frame)

    def on_save_and_run(self):
        """저장 후 실행 버튼 클릭 처리"""
        self.result_choice = "save_and_run"
        self.accept()

    def on_run_without_save(self):
        """저장 안하고 실행 버튼 클릭 처리"""
        self.result_choice = "run_without_save"
        self.accept()

    def on_cancel(self):
        """취소 버튼 클릭 처리"""
        self.result_choice = "cancel"
        self.reject()

    @staticmethod
    def show_dialog(parent=None):
        """다이얼로그 표시 및 결과 반환"""
        dialog = SaveConfirmationDialog(parent)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            return dialog.result_choice
        return "cancel"