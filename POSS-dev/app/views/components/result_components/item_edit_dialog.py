from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QDialogButtonBox, QLabel, QSpinBox,
                             QComboBox, QHBoxLayout, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QCursor
import pandas as pd
from app.utils.field_filter import filter_internal_fields


"""
아이템 정보 수정 다이얼로그
"""
class ItemEditDialog(QDialog):

    # 아이템 정보가 수정되었을 때 발생하는 시그널 (변경된 데이터, 필드별 변경 정보)
    itemDataChanged = pyqtSignal(dict, dict)

    def __init__(self, item_data=None, parent=None):
        super().__init__(parent)
        # 원본 데이터 보존 
        self.original_data = item_data.copy() if item_data else {}

        # 화면에 표시할 데이터 필터링
        self.item_data = filter_internal_fields(item_data)

        # 다이얼로그 스타일시트에 margin 관련 속성 추가
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 1px solid #d0d0d0;
                margin: 0px;
                padding: 0px;
            }
        """)

        # 부모 위젯 찾기 시도 (유효한 Line 값들을 가져오기 위함)
        self.available_lines = self.get_available_lines()

        # 수정 불가능한 필드 추가
        self.readonly_fields = ['MFG', 'SOP']

        self.init_ui()


    """
    UI 초기화
    """
    def init_ui(self):
        self.setWindowTitle("아이템 정보 수정")
        self.setMinimumWidth(900)
        self.setMinimumHeight(300)

        # 메인 레이아웃에 마진 명시적으로 설정 (이 부분이 중요)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 마진 제거
        main_layout.setSpacing(0)

        # 제목 레이블
        title_label = QLabel("Edit Status")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            background-color: #1428A0;
            color:white; 
            border: none;
            padding: 8px;
            border-radius: 4px;
        """)
        main_layout.addWidget(title_label)

        # 폼 레이아웃 (입력 필드 컨테이너)
        form_container = QWidget()
        form_container.setStyleSheet("""

            QWidget {
                background-color: white;
                border-radius: 6px;
                border: 1px solid #d0d0d0;
                font-family: Arial;
            }
            QLabel {
                font-weight: bold;
                color: #333333;
                padding-right: 10px;
                border:none;
            }
            QLineEdit, QComboBox, QSpinBox {
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                min-height: 25px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 2px solid #1428A0;
            }
            QLineEdit[readOnly="true"] {
                background-color: #f0f0f0;
                color: #777777;
                border: 1px solid #dddddd;
            }
        """)

        form_layout = QFormLayout(form_container)
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFormAlignment(Qt.AlignLeft)
        form_layout.setContentsMargins(20, 20, 20, 20)  # 여백 추가
        form_layout.setSpacing(12)  # 필드 간 간격

        # 중요 필드를 먼저 정의 (Line, Time, Item, MFG)
        self.important_fields = ['Line', 'Time', 'Item', 'Qty', 'MFG', 'SOP']
        self.field_widgets = {}

        # 중요 필드부터 생성
        for field in self.important_fields:
            if field in self.item_data:
                self._create_field_widget(field, form_layout)

        # 나머지 필드 생성
        for field, value in self.item_data.items():
            # 이미 생성된 중요 필드는 건너뛰기
            if field not in self.important_fields:
                self._create_field_widget(field, form_layout)

        main_layout.addWidget(form_container)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.setCursor(QCursor(Qt.PointingHandCursor))

        # 버튼 폰트와 스타일 설정
        button_font = QFont("Arial", 10, QFont.Bold)
        button_style = """
            QPushButton {
                background-color: #1428A0;
                color: white;
                font-weight: bold;
                border-radius: 10px;
                min-width: 100px;
                min-height: 35px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #004C99;
            }
            QPushButton:pressed {
                background-color: #003366;
            }
        """

        # 버튼 박스의 각 버튼에 폰트와 스타일 적용
        for button in button_box.buttons():
            button.setFont(button_font)  # 폰트 직접 설정
            button.setCursor(QCursor(Qt.PointingHandCursor))  # 각 버튼에 커서 설정
            button.setStyleSheet(button_style)

        button_box.accepted.connect(self.accept_changes)
        button_box.rejected.connect(self.reject)

        # 버튼 컨테이너 생성 및 스타일 적용
        button_container = QWidget()
        button_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 4px;
                padding: 5px;
                margin: 0px;
            }
        """)

        button_layout = QHBoxLayout(button_container)
        button_layout.addStretch(1)
        button_layout.addWidget(button_box)
        button_layout.addStretch(1)
        button_layout.setContentsMargins(10, 10, 10, 10)

        main_layout.addWidget(button_container)

    """
    그리드 위젯에서 사용 가능한 Line 값들을 가져옵니다.
    """
    def get_available_lines(self):
        try:
            # 부모 위젯 계층을 탐색하여 ModifiedLeftSection 또는 row_headers를 가진 위젯 찾기
            parent = self.parent()
            while parent:
                if hasattr(parent, 'row_headers') and parent.row_headers:
                    # row_headers에서 Line 값 추출
                    lines = set()
                    for header in parent.row_headers:
                        if '_(' in header:  # Line_(교대) 형식 확인
                            line = header.split('_(')[0]
                            lines.add(line)
                    return sorted(list(lines))

                if hasattr(parent, 'grid_widget') and hasattr(parent.grid_widget, 'row_headers'):
                    # grid_widget을 통해 row_headers 접근
                    lines = set()
                    for header in parent.grid_widget.row_headers:
                        if '_(' in header:
                            line = header.split('_(')[0]
                            lines.add(line)
                    return sorted(list(lines))

                parent = parent.parent()

            # 기본값 제공
            return [f"Line {i}" for i in range(1, 6)]
        except Exception as e:
            print(f"사용 가능한 Line 가져오기 오류: {e}")
            return [f"Line {i}" for i in range(1, 6)]

    """
    필드에 맞는 위젯 생성
    """
    def _create_field_widget(self, field, layout):
        value = self.item_data.get(field)
        value_str = str(value) if pd.notna(value) else ""

        # 필드 타입에 따른 위젯 생성
        widget = None

        # Line 필드인 경우 (콤보박스)
        if field == 'Line':
            widget = QComboBox()

            # 사용 가능한 Line 값 추가
            for line in self.available_lines:
                widget.addItem(str(line))

            # 현재 값 설정
            if value_str:
                index = widget.findText(value_str)
                if index >= 0:
                    widget.setCurrentIndex(index)
                else:
                    widget.addItem(value_str)
                    widget.setCurrentText(value_str)

        # Time 필드인 경우 (스핀박스)
        elif field == 'Time':
            widget = QSpinBox()
            widget.setMinimum(1)
            widget.setMaximum(14)  # 예: 1~14 시간대
            if value_str.isdigit():
                widget.setValue(int(value_str))

        # MFG 또는 SOP 필드인 경우 (읽기 전용 텍스트 필드)
        elif field in self.readonly_fields:
            widget = QLineEdit(value_str)
            widget.setReadOnly(True)
            # 읽기 전용임을 시각적으로 표시
            widget.setStyleSheet("""
                background-color: #f0f0f0;
                color: #777777;
                border: 1px solid #dddddd;
            """)

        # 기본 텍스트 필드
        else:
            widget = QLineEdit(value_str)

        # 위젯 저장 및 폼에 추가
        self.field_widgets[field] = widget
        layout.addRow(f"{field}:", widget)

        return widget

    """
    변경 사항 적용
    """
    def accept_changes(self):
        try:
            # 수정된 데이터 수집
            updated_data = {}

            for field, widget in self.field_widgets.items():
                # 읽기 전용 필드는 수정하지 않음
                if field in self.readonly_fields:
                    updated_data[field] = self.original_data.get(field, '')
                    continue

                # 위젯 타입에 따라 값 가져오기
                if isinstance(widget, QLineEdit):
                    updated_data[field] = widget.text()
                elif isinstance(widget, QSpinBox):
                    updated_data[field] = str(widget.value())
                elif isinstance(widget, QComboBox):
                    updated_data[field] = widget.currentText()

            # 변경 사항이 있는지 확인하고 변경된 필드 정보 수집
            changes_made = False
            changed_fields = {}

            for field, value in updated_data.items():
                # 읽기 전용 필드는 검사하지 않음
                if field in self.readonly_fields:
                    continue

                original = str(self.original_data.get(field, ''))
                if value != original:
                    changes_made = True
                    # 변경된 필드 정보 저장 (원래 값과 새 값)
                    changed_fields[field] = {'from': original, 'to': value}

            if changes_made:
                # 내부 필드 보존하여 결과 데이터 생성
                result_data = self.original_data.copy()
                for key, value in updated_data.items():
                    result_data[key] = value

                # 검증 통과 또는 validator 없음 - 변경 사항 적용
                # 변경 사항이 있으면 시그널 발생 (변경된 필드 정보 포함)
                # self.item_data.update(updated_data)
                self.itemDataChanged.emit(result_data, changed_fields)

            # 다이얼로그 닫기
            self.accept()

        except Exception as e:
            print(f"[다이얼로그] 데이터 업데이트 중 오류 발생: {str(e)}")
        