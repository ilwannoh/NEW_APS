from PyQt5.QtWidgets import QFrame, QLabel, QPushButton, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QCursor, QFont
from app.resources.fonts.font_manager import font_manager
from app.models.common.screen_manager import *


class Navbar(QFrame):
    # 시그널 정의
    help_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #1428A0;
                min-height: {h(50)}px;
                max-height: {h(50)}px;
            }}
            QLabel {{
                color: white;
            }}
            QPushButton {{
                color: white;
                border: {w(2)}px solid white;
                padding: {w(4)}px {w(8)}px;
                background-color: transparent;
                border-radius: {w(5)}px;
                min-width: {w(60)}px;
                min-height: {h(20)}px;
            }}
            QPushButton:hover {{
                background-color: #1e429f;
            }}
        """)

        navbar_layout = QHBoxLayout(self)
        navbar_layout.setContentsMargins(w(20), 0, w(20), 0)
        navbar_layout.setSpacing(w(10))  # 버튼 간격도 조정

        logo_label = QLabel("SAMSUNG Production Planning Optimization")
        logo_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # font_manager 사용
        logo_font = font_manager.get_just_font("SamsungOne-700").family()
        logo_label.setStyleSheet(f" QLabel {{font-family : {logo_font}; font-size: {f(20)}px; font-weight: bold; color: white;}}")

        navbar_layout.addWidget(logo_label)
        navbar_layout.addStretch()

        settings_btn = QPushButton("Settings")
        settings_btn.setCursor(QCursor(Qt.PointingHandCursor))

        # font_manager 사용
        btn_font = font_manager.get_just_font("SamsungOne-700").family()
        settings_btn.setStyleSheet(f" QPushButton {{ font-family : {btn_font}; font-size: {f(10)}; font-weight: bold; color: white;}}")

        help_btn = QPushButton("Help")
        help_btn.setCursor(QCursor(Qt.PointingHandCursor))
        help_btn.setStyleSheet(f" QPushButton {{ font-family : {btn_font}; font-size: {f(10)}; font-weight: bold; color: white;}}")

        # 시그널 연결
        help_btn.clicked.connect(self.help_clicked.emit)
        settings_btn.clicked.connect(self.settings_clicked.emit)

        navbar_layout.addWidget(settings_btn)
        navbar_layout.addWidget(help_btn)