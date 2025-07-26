# splash_start.py - 새로운 스플래시 화면 파일
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient
from app.resources.fonts.font_manager import font_manager
from app.models.common.screen_manager import *


class SplashStart(QWidget):
    """스레드 기반 스플래시 화면"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Samsung Production Planning System")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        screen = self.screen()
        screen_size = screen.availableGeometry()

        self.resize(int(screen_size.width() * 0.5), int(screen_size.height() * 0.4))
        self.center()

        # 배경 설정
        self.backgroundColor = QColor(255, 255, 255)  # 흰색
        self.accentColor = QColor(20, 40, 160)  # 파란색

        self.setup_ui()

        # 초기 진행률
        self.progress_value = 0

    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        try:
            bold_font = font_manager.get_just_font("SamsungSharpSans-Bold").family()
            normal_font = font_manager.get_just_font("SamsungOne-700").family()
        except:
            # 폰트 로드 실패 시 기본 폰트 사용
            bold_font = "Arial"
            normal_font = "Arial"

        # 로고 텍스트
        logo_label = QLabel("SAMSUNG")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet(
            f"font-family: {bold_font}; font-size: {f(40)}px; font-weight:bold; "
            f"color: rgb({self.accentColor.red()}, {self.accentColor.green()}, {self.accentColor.blue()});")

        # 부제목
        subtitle_label = QLabel("Production Planning Optimization System")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet(f"font-family:{normal_font}; font-size: {f(21)}px; color: #555555;")

        # 로딩 상태 메시지
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"font-family:{normal_font}; font-size: {f(16)}px; color: #888888;")

        # 프로그레스 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: #F0F0F0;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: rgb({self.accentColor.red()}, {self.accentColor.green()}, {self.accentColor.blue()});
                border-radius: 3px;
            }}
        """)

        # 버전 정보
        version_label = QLabel("Version 1.0.0")
        version_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        version_label.setStyleSheet(f"font-family:{normal_font}; font-size: {f(11)}px; color: #AAAAAA;")

        layout.addStretch(1)
        layout.addWidget(logo_label)
        layout.addWidget(subtitle_label)
        layout.addStretch(1)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addStretch(1)
        layout.addWidget(version_label)

    def center(self):
        """창을 화면 중앙에 배치"""
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(int((screen.width() - size.width()) / 2),
                  int((screen.height() - size.height()) / 2))

    @pyqtSlot(int, str)
    def update_progress_external(self, progress, message):
        """외부에서 진행률 업데이트 (스레드 안전)"""
        self.progress_value = progress
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)

        # UI 강제 업데이트
        self.repaint()
        QApplication.processEvents()  # 이벤트 처리 강제 실행

    def paintEvent(self, event):
        """배경 그라데이션 및 테두리 그리기"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 배경
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(255, 255, 255))  # 흰색
        gradient.setColorAt(1, QColor(245, 245, 250))  # 연한 파란색

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 15, 15)

        # 테두리
        painter.setPen(QPen(QColor(230, 230, 240), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(0, 0, self.width() - 1, self.height() - 1, 15, 15)