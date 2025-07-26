from PyQt5.QtWidgets import QLabel, QFrame, QVBoxLayout
from PyQt5.QtGui import QFont
from .base_tab import BaseTabComponent
from .help_section_component import HelpSectionComponent
from app.resources.fonts.font_manager import font_manager
from app.models.common.screen_manager import *


"""
계획 수립 탭 컴포넌트
"""
class PlanningTabComponent(BaseTabComponent):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_content()

    """
    콘텐츠 초기화
    """
    def init_content(self):
        # 콘텐츠 프레임
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet("""
            QFrame {
                background-color: #F9F9F9;
                border-radius: 10px;
                border: 1px solid #cccccc;
                margin: 10px;
            }
        """)


        # 콘텐츠 프레임 레이아웃
        frame_layout = QVBoxLayout(self.content_frame)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        frame_layout.setSpacing(h(10))

        bold_font = font_manager.get_just_font("SamsungSharpSans-Bold").family()
        normal_font = font_manager.get_just_font("SamsungOne-700").family()

        # 제목 레이블
        title_label = QLabel("Pre-Assigned Result")
        title_label.setStyleSheet(
            f"color: #1428A0; border:none; padding-bottom: 10px; border-bottom: 2px solid #1428A0; background-color: transparent; font-family: {bold_font}; font-size: {f(21)}px;")
        title_label.setMinimumHeight(40)

        # 설명 레이블
        desc_label = QLabel("This page allows you to review the pre-assigned results.")
        desc_label.setStyleSheet(f"margin-bottom: 15px; background-color: transparent; border:none; font-family: {normal_font}; font-size: {f(16)}px;")

        # 섹션들을 담을 프레임
        sections_frame = QFrame()
        sections_frame.setStyleSheet("background-color: transparent; border:none;")
        sections_layout = QVBoxLayout(sections_frame)
        sections_layout.setContentsMargins(0, 0, 0, 0)
        sections_layout.setSpacing(h(10))

        # 기능 섹션
        ### 사진 수정 필요
        section1 = HelpSectionComponent(
            number=1,
            title="View Assignment Results",
            description="The results are displayed in a calendar format.",
            image_path = "app/resources/help_images/pre_calendar.png"
        )

        # 팁 섹션
        section2 = HelpSectionComponent(
            number=2,
            title="View Summary Results",
            description="Here, you can see the quantified results of the output.",
            image_path = "app/resources/help_images/pre_summary.png"
        )

        section3 = HelpSectionComponent(
            number=3,
            title="Reset Results",
            description="This button resets the results when clicked.",
            image_path="app/resources/help_images/pre_reset.png"
        )

        section4 = HelpSectionComponent(
            number=4,
            title="Export Results",
            description="Clicking this button allows you to save the results as an Excel file.",
            image_path="app/resources/help_images/pre_export.png"
        )

        section5_1 = HelpSectionComponent(
            number="5-1",
            title="Run Second Optimization",
            description="By clicking this button, the secondary production scheduling algorithm will be executed.",
            image_path="app/resources/help_images/pre_run.png"
        )

        section5_2 = HelpSectionComponent(
            number="5-2",
            title="Select Project",
            description="Here, you can select the projects to be reflected in the results.",
            image_path="app/resources/help_images/pre_dialog.png"
        )



        # 섹션 프레임에 모든 섹션
        sections_layout.addWidget(section1)
        sections_layout.addWidget(section2)
        sections_layout.addWidget(section3)
        sections_layout.addWidget(section4)
        sections_layout.addWidget(section5_1)
        sections_layout.addWidget(section5_2)

        # 메모 레이블
        note_label = QLabel(
            "Review the pre-assigned results carefully before proceeding to the final optimization step.")
        note_label.setStyleSheet(
            "font-style: italic; color: #666; margin-top: 20px; background-color: transparent; border:none;")

        # 프레임 레이아웃에 위젯
        frame_layout.addWidget(title_label)
        frame_layout.addWidget(desc_label)
        frame_layout.addWidget(sections_frame)
        frame_layout.addWidget(note_label)
        frame_layout.addStretch(1)

        # 메인 레이아웃에 콘텐츠 프레임
        self.content_layout.addWidget(self.content_frame)