from PyQt5.QtWidgets import QLabel, QFrame, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from .base_tab import BaseTabComponent
from .help_section_component import HelpSectionComponent
from app.resources.fonts.font_manager import font_manager
from app.models.common.screen_manager import *


"""
결과 분석 탭 컴포넌트
"""
class ResultTabComponent(BaseTabComponent):

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
        title_label = QLabel("Results Analysis")
        title_label.setStyleSheet(
            f"color: #1428A0; border:none; padding-bottom: 10px; border-bottom: 2px solid #1428A0; background-color: transparent; font-family: {bold_font}; font-size: {f(21)}px;")
        title_label.setMinimumHeight(40)

        # 설명 레이블
        desc_label = QLabel("This page allows you to analyze and visualize the optimization results.")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("margin-bottom: 15px; background-color: transparent; border:none; font-family: {normal_font}; font-size: {f(16)}px;")

        # 섹션들을 담을 프레임
        sections_frame = QFrame()
        sections_frame.setStyleSheet("background-color: transparent; border:none;")
        sections_layout = QVBoxLayout(sections_frame)
        sections_layout.setContentsMargins(0, 0, 0, 0)
        sections_layout.setSpacing(h(10))

        section1 = HelpSectionComponent(
            number=1,
            title="View Planning Results",
            description="The results are displayed in a calendar format.",
            image_path="app/resources/help_images/result_calendar.png"
        )

        # 팁 섹션
        section2 = HelpSectionComponent(
            number=2,
            title="View Visualization Results",
            description="Here, you can see the quantified results of the output.",
            image_path="app/resources/help_images/result_visual.png"
        )

        section3 = HelpSectionComponent(
            number=3,
            title="Drag & Drop",
            description="Here, you can drag and drop items to move them to your desired location.",
            image_path="app/resources/help_images/result_drag.png"
        )
        section3.add_list_item("If the movement affects the plan, it will be reported in the error section.")
        section3.add_list_item("If you hold the Control key while moving, the item will be copied with a quantity of zero.")

        section3_1 = HelpSectionComponent(
            number="3-1",
            title="Error Section",
            description="Here, it will notify you of the incorrect part, and if you click on the selected area, you will be taken to that issue",
            image_path="app/resources/help_images/result_error.png"
        )
        section3_1.add_list_item("If corrected properly, this log will disappear.")

        section3_2 = HelpSectionComponent(
            number="3-2",
            title="Item Delete",
            description="If you right-click the mouse, you can delete the item.",
            image_path="app/resources/help_images/result_delete.png"
        )

        section4 = HelpSectionComponent(
            number=4,
            title="Export Results",
            description="Clicking this button allows you to save the results as an Excel file.",
            image_path="app/resources/help_images/result_export.png"
        )

        section5_1 = HelpSectionComponent(
            number="5-1",
            title="Item Filtering",
            description="Here, you can view the filtered results.",
            image_path="app/resources/help_images/result_filter.png"
        )

        section5_2 = HelpSectionComponent(
            number="5-2",
            title="Item Search",
            description="If you search for the model name here, the corresponding item will be found.",
            image_path="app/resources/help_images/result_search.png"
        )

        # 섹션 프레임에 모든 섹션
        sections_layout.addWidget(section1)
        sections_layout.addWidget(section2)
        sections_layout.addWidget(section3)
        sections_layout.addWidget(section3_1)
        sections_layout.addWidget(section3_2)
        sections_layout.addWidget(section4)
        sections_layout.addWidget(section5_1)
        sections_layout.addWidget(section5_2)

        # 메모 레이블
        note_label = QLabel(
            "Switch between visualization types to gain comprehensive insights into your optimization results.")
        note_label.setStyleSheet(
            "font-family: Arial; color: #666; margin-top: 20px; background-color: transparent; border:none;")

        frame_layout.addWidget(title_label)
        frame_layout.addWidget(desc_label)
        frame_layout.addWidget(sections_frame)
        frame_layout.addWidget(note_label)
        frame_layout.addStretch(1)

        self.content_layout.addWidget(self.content_frame)