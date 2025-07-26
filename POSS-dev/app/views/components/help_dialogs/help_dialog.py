from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget, QFrame
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtCore import Qt

from app.views.components.help_dialogs import (
    OverviewTabComponent,
    DataInputTabComponent,
    PlanningTabComponent,
    ResultTabComponent
)

from app.resources.fonts.font_manager import font_manager
from app.models.common.screen_manager import *

"""
도움말 다이얼로그 창
"""
class HelpDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Samsung Production Planning Optimization System")
        screen = self.screen()
        screen_size = screen.availableGeometry()
        self.resize(int(screen_size.width()* 0.45), int(screen_size.height()* 0.6))
        self.init_ui()

    def init_ui(self):
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 제목 레이블
        title_frame = QFrame()
        title_frame.setFrameShape(QFrame.StyledPanel)
        title_frame.setStyleSheet(f"background-color: #1428A0; border: none; min-height: {h(45)}px;")

        # 프레임 레이아웃
        title_frame_layout = QVBoxLayout(title_frame)
        title_frame_layout.setContentsMargins(20, 0, 10, 0)
        title_frame_layout.setAlignment(Qt.AlignLeft)

        # 제목 레이블
        title_label = QLabel("Help Guide")
        title_font = font_manager.get_just_font("SamsungSharpSans-Bold").family()
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: white; font-size: {f(20)}px; font-family: {title_font}; font-weight: bold;")

        title_frame_layout.addWidget(title_label)

        main_layout.addWidget(title_frame)

        # 탭 위젯
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet(
           f"""
                QTabWidget::pane {{
                background-color: #ffffff;
                border: none;
                border-top: 1px solid #e9ecef;
                border-radius: 0px;
            }}

            QTabBar {{
                background-color: #f8f9fa;
                border: none;
                border-radius: 0px;
            }}

            QTabBar::tab {{
                background: transparent;
                color: #666;
                padding: 8px 12px;
                font-family: {font_manager.get_just_font("SamsungOne-700").family()};
                font-size: {f(13)}px;
                font-weight: 600;
                border-bottom: 3px solid transparent;
                margin-right: 2px;
            }}

            QTabBar::tab:hover {{
                color: #1428A0;
                background: rgba(20, 40, 160, 0.05);
            }}

            QTabBar::tab:selected {{
                color: #1428A0;
                font-weight: 700;
                border-bottom: 3px solid #1428A0;
                background: rgba(20, 40, 160, 0.05);
            }}
        """)


        overview_tab = OverviewTabComponent()
        data_input_tab = DataInputTabComponent()
        planning_tab = PlanningTabComponent()
        result_tab = ResultTabComponent()

        tab_widget.addTab(overview_tab, "OverView")
        tab_widget.addTab(data_input_tab, "Data Input")
        tab_widget.addTab(planning_tab, "Pre-Assigned")
        tab_widget.addTab(result_tab, "Results")

        # 버튼 레이아웃
        button_frame = QFrame()
        button_frame.setStyleSheet("background-color: #F0F0F0; border: none;")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 0, 30, 10)

        close_button = QPushButton("Close")
        close_button_font = font_manager.get_just_font("SamsungOne-700").family()
        close_button.setStyleSheet(f"""
        QPushButton {{
            font-family : {close_button_font};
            font-size : {f(16)}px;
            background-color: #1428A0;
            border: none;
            color: white;
            border-radius: 10px;
            width: {w(100)}px;
            height: {h(40)}px;
        }}
        QPushButton:hover {{
            background-color: #1e429f;
            border: none;
            color: white;
        }}
        """)
        close_button.setCursor(QCursor(Qt.PointingHandCursor))
        close_button.clicked.connect(self.accept)

        button_layout.addStretch(1)
        button_layout.addWidget(close_button)

        main_layout.addWidget(tab_widget)
        main_layout.addWidget(button_frame)