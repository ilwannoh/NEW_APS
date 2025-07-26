from PyQt5.QtWidgets import QLabel, QFrame, QVBoxLayout
from PyQt5.QtGui import QFont
from .base_tab import BaseTabComponent
from .help_section_component import HelpSectionComponent
from app.resources.fonts.font_manager import font_manager
from app.models.common.screen_manager import *

"""
데이터 입력 탭 컴포넌트
"""
class DataInputTabComponent(BaseTabComponent):

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
        bold_font = font_manager.get_just_font("SamsungSharpSans-Bold").family()
        normal_font = font_manager.get_just_font("SamsungOne-700").family()

        # 콘텐츠 프레임 레이아웃
        frame_layout = QVBoxLayout(self.content_frame)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        frame_layout.setSpacing(h(10))

        # 제목 레이블
        title_label = QLabel("Data Entry Guidelines")
        title_label.setStyleSheet(
            f"color: #1428A0; border:none; padding-bottom: 10px; border-bottom: 2px solid #1428A0; background-color: transparent; font-family: {bold_font}; font-size: {f(21)}px;")
        title_label.setMinimumHeight(40)

        # 설명 레이블
        desc_label = QLabel("This page provides instructions for entering and managing data in the system.")
        desc_label.setStyleSheet(f"margin-bottom: 15px; background-color: transparent; border:none; font-family: {normal_font}; font-size: {f(16)}px;")

        # 섹션들을 담을 프레임
        sections_frame = QFrame()
        sections_frame.setStyleSheet("background-color: transparent; border:none;")
        sections_layout = QVBoxLayout(sections_frame)
        sections_layout.setContentsMargins(0, 0, 0, 0)
        sections_layout.setSpacing(h(10))  # 섹션간 간격

        # 섹션 1 - 날짜 범위 선택
        section1 = HelpSectionComponent(
            number=1,
            title="Date Range Selection",
            description="The planning period can be set using the date selector located in the top-left corner.",
            image_path="app/resources/help_images/select_date.png"
        )

        # 섹션 2 - 파일 업로드
        section2 = HelpSectionComponent(
            number=2,
            title="Upload File",
            description="Click the 'Browse' button to upload the required Excel file.",
            image_path="app/resources/help_images/browse_btn.png"
        )

        section2.add_list_item("master_*.xlsx ")
        section2.add_list_item("demand_*.xlsx ")
        section2.add_list_item("dynamic_*.xlsx ")

        # 섹션 3 - 파일 내용 확인
        section3 = HelpSectionComponent(
            number=3,
            title="Verify File Contents",
            description="Select a file or sheet from the file explorer on the left to review its contents. Data can be edited as needed.",
            image_path="app/resources/help_images/data_content.png"
        )
        section3.add_list_item("The user can edit the content and run it with the modified values.")

        section3_1 = HelpSectionComponent(
            number="3-1",
            title="Edit File Contents",
            description="If any edits are made, the modified files and sheets will be highlighted in red.",
            image_path="app/resources/help_images/edit_data.png"
        )

        section3_2 = HelpSectionComponent(
            number="3-2",
            title="Save modified files",
            description="If you click the Save button, the original file will be overwritten with the modified content.",
            image_path="app/resources/help_images/save_btn.png"
        )

        # 섹션 4 - 파라미터 설정
        section4 = HelpSectionComponent(
            number=4,
            title="Adjust Settings",
            description="You need to adjust the settings in the settings window before running.",
            image_path = "app/resources/help_images/settings.png"
        )
        section4.add_list_item("Once you set it, the same settings will be saved for the next time as well.")


        # 섹션 5 - 실행
        section5_1 = HelpSectionComponent(
            number="5-1",
            title="Run without any modifications.",
            description="Initiate the optimization process by clicking the 'Run' button.",
            image_path="app/resources/help_images/run_btn.png"
        )

        section5_2 = HelpSectionComponent(
            number="5-2",
            title="Run with modifications.",
            description="If you run without saving the modifications, you will be given the option to either save and run or run without saving.",
            image_path="app/resources/help_images/save_change.png"
        )



        # 섹션 프레임에 모든 섹션 추가
        sections_layout.addWidget(section1)
        sections_layout.addWidget(section2)
        sections_layout.addWidget(section3)
        sections_layout.addWidget(section3_1)
        sections_layout.addWidget(section3_2)
        sections_layout.addWidget(section4)
        sections_layout.addWidget(section5_1)
        sections_layout.addWidget(section5_2)

        # 메모 레이블
        note_label = QLabel("Ensure all required files are uploaded before starting the optimization process.")
        note_label.setStyleSheet(
            "font-style: italic; color: #666; margin-top: 20px; background-color: transparent; border:none;")

        # 프레임 레이아웃에 위젯 추가
        frame_layout.addWidget(title_label)
        frame_layout.addWidget(desc_label)
        frame_layout.addWidget(sections_frame)
        frame_layout.addWidget(note_label)
        frame_layout.addStretch(1)

        self.content_layout.addWidget(self.content_frame)