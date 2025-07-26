from PyQt5.QtWidgets import QLabel, QFrame, QVBoxLayout, QComboBox, QCheckBox
from PyQt5.QtGui import QFont
from .base_tab import BaseTabComponent
from .settings_section import ModernSettingsSectionComponent
from app.models.common.settings_store import SettingsStore
from app.resources.fonts.font_manager import font_manager


"""
Pre-Option 탭 컴포넌트
"""
class ModernPreOptionTabComponent(BaseTabComponent):

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
        header_layout.setSpacing(8)

        # 제목 레이블
        title_label = QLabel("Pre-Option Settings")
        title_font = font_manager.get_font("SamsungSharpSans-Bold", 20, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1428A0; border: none;")
        header_layout.addWidget(title_label)

        self.content_layout.addWidget(header_frame)

        # 날짜 선택 옵션 (1~14일)
        days = [str(i) for i in range(1, 15)]

        # 계획 유지율 섹션 1
        plan_retention1_section = ModernSettingsSectionComponent("Plan Retention Rate 1")
        plan_retention1_section.setting_changed.connect(self.on_setting_changed)

        plan_retention1_section.add_setting_item(
            "Plan Retention Rate 1", "op_timeset_1", "button_group",
            items=days, default=SettingsStore.get("op_timeset_1", []),
            columns=7
        )

        plan_retention1_section.add_setting_item(
            "SKU Plan Retention Rate 1", "op_SKU_1", "input",
            min=0, max=100, default=SettingsStore.get("op_SKU_1", 100),
            suffix="%"
        )

        plan_retention1_section.add_setting_item(
            "RMC Plan Retention Rate 1", "op_RMC_1", "input",
            min=0, max=100, default=SettingsStore.get("op_RMC_1", 100),
            suffix="%"
        )

        # 계획 유지율 섹션 2
        plan_retention2_section = ModernSettingsSectionComponent("Plan Retention Rate 2")
        plan_retention2_section.setting_changed.connect(self.on_setting_changed)

        plan_retention2_section.add_setting_item(
            "Plan Retention Rate 2", "op_timeset_2", "button_group",
            items=days, default=SettingsStore.get("op_timeset_2", []),
            columns=7
        )

        plan_retention2_section.add_setting_item(
            "SKU Plan Retention Rate 2", "op_SKU_2", "input",
            min=0, max=100, default=SettingsStore.get("op_SKU_2", 100),
            suffix="%"
        )

        plan_retention2_section.add_setting_item(
            "RMC Plan Retention Rate 2", "op_RMC_2", "input",
            min=0, max=100, default=SettingsStore.get("op_RMC_2", 100),
            suffix="%"
        )

        # 사전 할당 섹션
        pre_allocation_section = ModernSettingsSectionComponent("Pre-Assignment")
        pre_allocation_section.setting_changed.connect(self.on_setting_changed)

        checkbox_widget = pre_allocation_section.add_setting_item(
            "Apply Pre-Assignment Ratio", "max_min_ratio_ox", "checkbox",
            default=bool(SettingsStore.get("max_min_ratio_ox", 0))
        )

        margins = [str(i) for i in range(0, 51)]

        default_margin = SettingsStore.get("max_min_margin", 0)
        combobox_widget = pre_allocation_section.add_setting_item(
            "Pre-Assignment Ratio for Primary Execution", "max_min_margin", "combobox",
            items=margins,
            default_index=default_margin
        )

        # 체크박스와 콤보박스 연결
        if isinstance(checkbox_widget, QCheckBox) and isinstance(combobox_widget, QComboBox):
            combobox_widget.setEnabled(checkbox_widget.isChecked())

            if not checkbox_widget.isChecked():
                combobox_widget.setStyleSheet(self._get_disabled_combobox_style())

            # 체크박스 상태 변경 시 콤보박스 활성/비활성화
                # 체크박스 상태 변경 시 콤보박스 활성/비활성화
                def on_checkbox_state_changed(state):
                    is_checked = bool(state)
                    combobox_widget.setEnabled(is_checked)

                    # 활성화/비활성화에 따른 스타일 변경
                    if is_checked:
                        combobox_widget.setStyleSheet(self._get_enabled_combobox_style())
                    else:
                        combobox_widget.setStyleSheet(self._get_disabled_combobox_style())
                        # 비활성화되어도 값은 그대로 유지

            checkbox_widget.stateChanged.connect(on_checkbox_state_changed)

        # 섹션 추가
        self.content_layout.addWidget(pre_allocation_section)
        self.content_layout.addWidget(plan_retention1_section)
        self.content_layout.addWidget(plan_retention2_section)


        self.content_layout.addStretch(1)

    """
    활성화된 콤보박스 스타일
    """
    def _get_enabled_combobox_style(self):
        return """
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 14px;
                font-family: Arial;
            }
            QComboBox:focus {
                border-color: #1428A0;
            }
            QComboBox:hover {
                border-color: #adb5bd;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(none);
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #dee2e6;
                background-color: white;
                selection-background-color: #e9ecef;
                selection-color: #1428A0;
            }
        """

    """
    비활성화된 콤보박스 스타일
    """
    def _get_disabled_combobox_style(self):
        return """
            QComboBox {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                color: #888;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 14px;
                font-family: Arial;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(none);
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #888;
            }
        """

    """
    설정 변경 시 호출되는 콜백
    """
    def on_setting_changed(self, key, value):
        SettingsStore.set(key, value)
        self.settings_changed.emit(key, value)