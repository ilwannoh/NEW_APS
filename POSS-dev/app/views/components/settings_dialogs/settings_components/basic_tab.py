from PyQt5.QtWidgets import QLabel, QFrame, QVBoxLayout
from PyQt5.QtGui import QFont
from .base_tab import BaseTabComponent
from .settings_section import ModernSettingsSectionComponent
from app.models.common.settings_store import SettingsStore
from app.resources.fonts.font_manager import font_manager


"""
Basic 탭 컴포넌트
"""
class ModernBasicTabComponent(BaseTabComponent):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_content()

    """
    콘텐츠 초기화
    """
    def init_content(self):
        # 헤더 섹션
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                padding-bottom: 5px;
                border-bottom: 2px solid #1428A0;
            }
        """)

        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # 제목 레이블
        title_label = QLabel("Basic Settings")
        title_font = font_manager.get_font("SamsungSharpSans-Bold", 20, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1428A0; border: none;")
        header_layout.addWidget(title_label)

        self.content_layout.addWidget(header_frame)

        # 러닝 타임 섹션
        running_section = ModernSettingsSectionComponent("Running Time")
        running_section.setting_changed.connect(self.on_setting_changed)

        running_section.add_setting_item(
            "First Processing Time(s)", "time_limit1", "input",
            min=1, max=86400, default=SettingsStore.get("time_limit1", 10),
        )

        running_section.add_setting_item(
            "Second Processing Time(s)", "time_limit2", "input",
            min=1, max=86400, default=SettingsStore.get("time_limit2", 300),
        )

        # 가중치 섹션
        weight_section = ModernSettingsSectionComponent("Weight")
        weight_section.setting_changed.connect(self.on_setting_changed)

        weight_section.add_setting_item(
            "SOP Weight", "weight_sop_ox", "doublespinbox",
            min=0.0, max=10.0, default=SettingsStore.get("weight_sop_ox", 1.0),
            decimals=4, step=0.0001
        )

        weight_section.add_setting_item(
            "Weight by Material Quantity", "weight_mat_qty", "doublespinbox",
            min=0.0, max=10.0, default=SettingsStore.get("weight_mat_qty", 1.0),
            decimals=4, step=0.0001
        )

        weight_section.add_setting_item(
            "Weight Distributed by Project", "weight_linecnt_bypjt", "doublespinbox",
            min=0.0, max=10.0, default=SettingsStore.get("weight_linecnt_bypjt", 1.0),
            decimals=4, step=0.0001
        )

        weight_section.add_setting_item(
            "Weight Distributed per Item", "weight_linecnt_byitem", "doublespinbox",
            min=0.0, max=10.0, default=SettingsStore.get("weight_linecnt_byitem", 1.0),
            decimals=4, step=0.0001
        )

        weight_section.add_setting_item(
            "Operation Rate Weight", "weight_operation", "doublespinbox",
            min=0.0, max=10.0, default=SettingsStore.get("weight_operation", 1.0),
            decimals=4, step=0.0001
        )

        self.content_layout.addWidget(running_section)
        self.content_layout.addWidget(weight_section)

        self.content_layout.addStretch(1)

    """
    설정 변경 시 호출되는 콜백
    """
    def on_setting_changed(self, key, value):
        SettingsStore.set(key, value)
        self.settings_changed.emit(key, value)