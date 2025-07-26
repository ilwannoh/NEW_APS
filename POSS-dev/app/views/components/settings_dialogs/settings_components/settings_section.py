from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QFormLayout, QLabel,
                             QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
                             QComboBox, QPushButton, QFileDialog, QWidget, QHBoxLayout,
                             QGraphicsDropShadowEffect, QGridLayout)
from PyQt5.QtGui import QFont, QColor, QCursor, QIntValidator, QDoubleValidator
from PyQt5.QtCore import Qt, pyqtSignal
from app.models.common.screen_manager import *
from app.resources.fonts.font_manager import font_manager

"""
Settings 섹션 컴포넌트
"""
class ModernSettingsSectionComponent(QFrame):
    setting_changed = pyqtSignal(str, object)

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.init_ui()

    """
    UI 초기화
    """
    def init_ui(self):
        self.setStyleSheet("""
            ModernSettingsSectionComponent {
                background-color: white;
                border: none;
                border-left: 4px solid #1428A0;
                border-radius: 0 8px 8px 0;

            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)

        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 12, 24, 12)
        main_layout.setSpacing(0)

        # 제목 레이블
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet(
            "color: #1428A0; border: none; margin-bottom: 10px; background: rgba(20, 40, 160, 0.05);")

        self.settings_widget = QWidget()
        self.settings_widget.setStyleSheet("border: none; background-color: transparent;")

        # QFormLayout
        self.settings_layout = QFormLayout(self.settings_widget)
        self.settings_layout.setContentsMargins(0, 0, 0, 0)
        self.settings_layout.setSpacing(20)
        self.settings_layout.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        self.settings_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.settings_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)

        main_layout.addWidget(title_label)
        main_layout.addWidget(self.settings_widget)

    """
    모던한 스타일의 설정 항목 추가
    """
    def add_setting_item(self, label_text, setting_key, widget_type, **kwargs):
        label = QLabel(label_text)
        label.setFont(QFont("Arial", 11, QFont.Medium))
        label.setStyleSheet("color: #333; padding: 0px; margin: 0px; font-weight: 500; ")
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setMinimumWidth(250)

        widget = None

        # 텍스트 입력
        if widget_type == 'input':
            widget = QLineEdit()
            widget.setStyleSheet("""
                QLineEdit {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    padding: 10px 14px;
                    font-size: 14px;
                    font-family: Arial;
                }
                QLineEdit:focus {
                    border-color: #1428A0;
                }
                QLineEdit:hover {
                    border-color: #adb5bd;
                }
            """)
            widget.setMinimumWidth(300)
            widget.setMaximumWidth(400)
            widget.setFixedHeight(40)

            input_type = kwargs.get('type', 'text')

            if 'min' in kwargs and 'max' in kwargs:
                input_type = 'int'
                validator = QIntValidator(kwargs['min'], kwargs['max'])
                widget.setValidator(validator)

            elif 'suffix' in kwargs and kwargs['suffix'] == '%':
                input_type = 'int'
                validator = QIntValidator(0, 100)
                widget.setValidator(validator)

            # 타입이 명시적으로 지정된 경우
            elif input_type == 'int':
                validator = QIntValidator()

                if 'min' in kwargs:
                    validator.setBottom(kwargs['min'])

                if 'max' in kwargs:
                    validator.setTop(kwargs['max'])

                widget.setValidator(validator)
            elif input_type == 'float':
                validator = QDoubleValidator()

                if 'min' in kwargs:
                    validator.setBottom(kwargs['min'])

                if 'max' in kwargs:
                    validator.setTop(kwargs['max'])

                if 'decimals' in kwargs:
                    validator.setDecimals(kwargs['decimals'])

                widget.setValidator(validator)

            if 'default' in kwargs:
                widget.setText(str(kwargs['default']))

            # 텍스트 변경 시 타입에 맞게 변환하여 시그널 발생
            def on_text_changed(text):
                if text:
                    try:
                        if input_type == 'int':
                            value = int(text)
                        elif input_type == 'float':
                            value = float(text)
                        else:
                            value = text

                        self.setting_changed.emit(setting_key, value)
                    except ValueError:
                        self.setting_changed.emit(setting_key, text)
                else:
                    if input_type == 'int' and 'default' in kwargs:
                        self.setting_changed.emit(setting_key, kwargs['default'])
                    elif input_type == 'float' and 'default' in kwargs:
                        self.setting_changed.emit(setting_key, kwargs['default'])
                    else:
                        self.setting_changed.emit(setting_key, text)

            widget.textChanged.connect(on_text_changed)

        elif widget_type == 'shift_grid':
            container = QWidget()
            container.setStyleSheet("background-color: transparent; border: none;")
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(10)

            grid_widget = QWidget()
            grid_widget.setStyleSheet(f"""
                background-color: white;
                min-width: {w(50)}px;
                padding: 0px;
            """)

            grid_layout = QGridLayout(grid_widget)
            grid_layout.setContentsMargins(0, 0, 0, 0)
            grid_layout.setSpacing(8)

            # 날짜 레이블 (상단)
            for i in range(1, 15):
                day_label = QLabel(str(i))
                day_label.setAlignment(Qt.AlignCenter)
                day_label.setStyleSheet("""
                    color: #1428A0;
                    font-weight: bold;
                    background-color: #f0f0f0;
                    border-radius: 4px;
                    padding: 4px;
                """)
                # 홀수/짝수에 따라 행과 열 위치 결정
                if i % 2 == 1:  # 홀수
                    row = 0
                    col = (i - 1) // 2
                else:  # 짝수
                    row = 2
                    col = (i // 2) - 1

                grid_layout.addWidget(day_label, row, col)

            # 가중치 입력 스핀박스 (하단)
            spinboxes = []
            default_values = kwargs.get('default_values', [0.0001] * 14)

            for i in range(1, 15):
                spinbox = QDoubleSpinBox()
                spinbox.setMinimum(0.0001)
                spinbox.setMaximum(1.0000)
                spinbox.setDecimals(4)
                spinbox.setSingleStep(0.0001)
                spinbox.setValue(default_values[i - 1])
                spinbox.setStyleSheet(f"""
                    QDoubleSpinBox {{
                        background-color: #ffffff;
                        border: 1px solid #dee2e6;
                        border-radius: 4px;
                        padding: 4px;
                        font-size: {f(13)}px;
                    }}
                    QDoubleSpinBox:focus {{
                        border-color: #1428A0;
                    }}
                """)
                spinbox.setFixedWidth(90)
                spinbox.setFixedHeight(30)

                # 홀수/짝수에 따라 행과 열 위치 결정
                if i % 2 == 1:  # 홀수
                    row = 1
                    col = (i - 1) // 2
                else:  # 짝수
                    row = 3
                    col = (i // 2) - 1

                grid_layout.addWidget(spinbox, row, col)
                spinboxes.append(spinbox)

            container_layout.addWidget(grid_widget)

            # 값이 변경될 때 전체 리스트를 업데이트
            def on_value_changed(_):
                values = [spinbox.value() for spinbox in spinboxes]
                self.setting_changed.emit(setting_key, values)

            for spinbox in spinboxes:
                spinbox.valueChanged.connect(on_value_changed)

            widget = container

        # 정수 스핀박스
        elif widget_type == 'spinbox':
            widget = QSpinBox()
            widget.setStyleSheet("""
                QSpinBox {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    padding: 10px 14px;
                    font-size: 14px;
                    font-family: Arial;
                }
                QSpinBox:focus {
                    border-color: #1428A0;
                }
                QSpinBox:hover {
                    border-color: #adb5bd;
                }
            """)

            widget.setMinimumWidth(150)
            widget.setMaximumWidth(200)
            widget.setFixedHeight(40)

            widget.wheelEvent = lambda event: event.ignore()

            if 'min' in kwargs:
                widget.setMinimum(kwargs['min'])

            if 'max' in kwargs:
                widget.setMaximum(kwargs['max'])

            if 'default' in kwargs:
                widget.setValue(kwargs['default'])

            if 'suffix' in kwargs:
                widget.setSuffix(kwargs['suffix'])

            widget.valueChanged.connect(lambda value: self.setting_changed.emit(setting_key, value))

        # 실수 스핀박스
        elif widget_type == 'doublespinbox':
            widget = QDoubleSpinBox()
            widget.setStyleSheet("""
                QDoubleSpinBox {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 0px;
                    padding: 10px 14px;
                    font-size: 14px;
                    font-family: Arial;
                    border-top-left-radius: 6px;
                    border-bottom-left-radius: 6px;
                }
                QDoubleSpinBox:focus {
                    border-color: #1428A0;
                }
                QDoubleSpinBox:hover {
                    border-color: #adb5bd;
                }
            """)

            widget.setMinimumWidth(150)
            widget.setMaximumWidth(200)
            widget.setFixedHeight(40)

            widget.wheelEvent = lambda event: event.ignore()

            if 'min' in kwargs:
                widget.setMinimum(kwargs['min'])

            if 'max' in kwargs:
                widget.setMaximum(kwargs['max'])

            if 'default' in kwargs:
                widget.setValue(kwargs['default'])

            if 'decimals' in kwargs:
                widget.setDecimals(kwargs['decimals'])

            if 'step' in kwargs:
                widget.setSingleStep(kwargs['step'])

            if 'suffix' in kwargs:
                widget.setSuffix(kwargs['suffix'])

            widget.valueChanged.connect(lambda value: self.setting_changed.emit(setting_key, value))

        # 체크박스
        elif widget_type == 'checkbox':
            widget = QCheckBox()
            widget.setStyleSheet("""
                QCheckBox {
                    font-size: 14px;
                    spacing: 10px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border: 2px solid #dee2e6;
                    border-radius: 4px;
                    background: white;
                    
                }
                QCheckBox::indicator:checked {
                    background-color: #1428A0;
                    border-color: #1428A0;
                    color: white;
                }
                QCheckBox::indicator:hover {
                    border-color: #adb5bd;
                }
                QCheckBox::indicator:checked:hover {
                    background-color: #1a35cc;
                    border-color: #1a35cc;
                }
            """)
            widget.setFixedHeight(30)

            if 'default' in kwargs and kwargs['default']:
                widget.setChecked(True)

            widget.stateChanged.connect(lambda state: self.setting_changed.emit(setting_key, bool(state)))

        # 콤보박스
        elif widget_type == 'combobox':
            widget = QComboBox()
            widget.setStyleSheet("""
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
            """)

            widget.setMinimumWidth(200)
            widget.setMaximumWidth(300)
            widget.setFixedHeight(40)

            if 'items' in kwargs:
                widget.addItems(kwargs['items'])

            if 'default_index' in kwargs:
                widget.setCurrentIndex(kwargs['default_index'])

            widget.currentIndexChanged.connect(
                lambda index: self.setting_changed.emit(setting_key, widget.currentText() if kwargs.get('return_text',
                                                                                                        False) else index)
            )

        # 파일 경로 선택
        elif widget_type == 'filepath':
            container_file = QWidget()
            container_file.setStyleSheet("background-color: transparent; border: none;")
            container_file_layout = QHBoxLayout(container_file)
            container_file_layout.setContentsMargins(0, 0, 0, 0)
            container_file_layout.setSpacing(12)

            # 경로 표시 입력창
            path_input = QLineEdit()
            path_input.setStyleSheet("""
                QLineEdit {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    padding: 10px 14px;
                    font-size: 14px;
                    font-family: Arial;
                }
                QLineEdit:focus {
                    border-color: #1428A0;
                }
            """)

            path_input.setMinimumWidth(300)
            path_input.setMaximumWidth(400)
            path_input.setFixedHeight(40)

            if 'default' in kwargs:
                path_input.setText(kwargs['default'])

            path_input.setReadOnly(kwargs.get('readonly', True))

            # 찾아보기 버튼
            browse_button = QPushButton("Browse")
            browse_button.setStyleSheet("""
                QPushButton {
                    background-color: #1428A0;
                    color: white;
                    border-radius: 6px;
                    padding: 10px 20px;
                    border: none;
                    font-family: Arial;
                    font-weight: 500;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #1a35cc;
                }
                QPushButton:pressed {
                    background-color: #1e429f;
                }
            """)
            browse_button.setFixedHeight(40)
            browse_button.setCursor(QCursor(Qt.PointingHandCursor))

            
            """
            버튼 클릭 이벤트
            """
            def browse_file():
                dialog_type = kwargs.get('dialog_type', 'file')

                if dialog_type == 'file':
                    if kwargs.get('save_mode', False):
                        file_path, _ = QFileDialog.getSaveFileName(
                            self, "Save File", "", kwargs.get('filter', "All Files (*.*)"))
                    else:
                        file_path, _ = QFileDialog.getOpenFileName(
                            self, "Open File", "", kwargs.get('filter', "All Files (*.*)"))
                else:
                    file_path = QFileDialog.getExistingDirectory(
                        self, "Select Directory", "")

                if file_path:
                    path_input.setText(file_path)
                    self.setting_changed.emit(setting_key, file_path)

            browse_button.clicked.connect(browse_file)
            path_input.textChanged.connect(lambda text: self.setting_changed.emit(setting_key, text))

            container_file_layout.addWidget(path_input)
            container_file_layout.addWidget(browse_button)

            widget = container_file

        # 버튼 그룹으로 다중 선택
        elif widget_type == 'button_group':
            container = QWidget()
            container.setStyleSheet("background-color: transparent; border: none;")
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(12)

            # 선택된 항목들 표시 레이블
            selected_label = QLabel("Selected items: ")
            selected_label.setFont(QFont("Arial", 10))
            selected_label.setStyleSheet("""
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 6px 8px;
                color: #333;
            """)
            selected_label.setMinimumWidth(400)
            selected_label.setMaximumWidth(500)
            selected_label.setWordWrap(True)

            button_container = QWidget()
            button_container.setStyleSheet("background-color: transparent; border: none;")

            grid_layout = QGridLayout(button_container)
            grid_layout.setContentsMargins(0, 0, 0, 0)
            grid_layout.setSpacing(8)

            selected_items = []

            if 'default' in kwargs and isinstance(kwargs['default'], list):
                selected_items = kwargs['default'].copy()

            buttons = {}

            button_style_normal = """
                QPushButton {
                    background-color: #ffffff;
                    border: 2px solid #dee2e6;
                    border-radius: 6px;
                    padding: 4px 8px;
                    font-size: 14px;
                    font-family: Arial;
                    font-weight: 500;
                    min-width: 30px;
                    min-height: 25px;
                }
                QPushButton:hover {
                    background-color: #f8f9fa;
                    border-color: #adb5bd;
                }
            """

            button_style_selected = """
                QPushButton {
                    background-color: #1428A0;
                    border: 2px solid #1428A0;
                    border-radius: 6px;
                    padding: 4px 8px;
                    font-size: 14px;
                    font-family: Arial;
                    font-weight: 600;
                    color: white;
                    min-width: 30px;
                    min-height: 25px;
                }
                QPushButton:hover {
                    background-color: #1a35cc;
                    border-color: #1a35cc;
                }
            """

            """
            선택된 항목 표시 업데이트 함수
            """
            def update_selected_text():
                if selected_items:
                    sorted_items = sorted([int(item) for item in selected_items])
                    selected_label.setText("Selected Items: " + ", ".join(map(str, sorted_items)))
                else:
                    selected_label.setText("Selected Items: No items selected")

                self.setting_changed.emit(setting_key, [str(item) for item in selected_items])

            """
            버튼 클릭 이벤트 처리 함수
            """
            def toggle_button(item):
                if item in selected_items:
                    selected_items.remove(item)
                    buttons[item].setStyleSheet(button_style_normal)
                else:
                    selected_items.append(item)
                    buttons[item].setStyleSheet(button_style_selected)

                update_selected_text()

            # 버튼 생성
            if 'items' in kwargs:
                items = kwargs['items']
                cols = kwargs.get('columns', 7)

                for i, item in enumerate(items):
                    button = QPushButton(str(item))
                    button.setCursor(QCursor(Qt.PointingHandCursor))

                    # 기본 상태 또는 선택된 상태 설정
                    if item in selected_items:
                        button.setStyleSheet(button_style_selected)
                    else:
                        button.setStyleSheet(button_style_normal)

                    button.clicked.connect(lambda checked, val=item: toggle_button(val))

                    # 홀수/짝수에 따라 행과 열 위치 결정
                    num = int(item)  # 숫자로 변환
                    if num % 2 == 1:  # 홀수
                        row = 0
                        col = (num - 1) // 2
                    else:  # 짝수
                        row = 1
                        col = (num // 2) - 1

                    grid_layout.addWidget(button, row, col)

                    buttons[item] = button

            update_selected_text()

            container_layout.addWidget(selected_label)
            container_layout.addWidget(button_container)

            widget = container

        # 다중 선택 콤보박스
        elif widget_type == 'multiselect':
            container_multi = QWidget()
            container_multi.setStyleSheet("background-color: transparent; border: none;")
            container_multi_layout = QVBoxLayout(container_multi)
            container_multi_layout.setContentsMargins(0, 0, 0, 0)
            container_multi_layout.setSpacing(8)

            # 현재 선택된 항목들 표시
            selected_label = QLabel("Selected items: ")
            selected_label.setFont(QFont("Arial", 10))
            selected_label.setStyleSheet("""
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px 16px;
                color: #333;
            """)
            selected_label.setMinimumWidth(400)
            selected_label.setMaximumWidth(500)
            selected_label.setWordWrap(True)

            # 콤보박스와 버튼 컨테이너
            combo_container = QWidget()
            combo_container.setStyleSheet("background-color: transparent; border: none;")
            combo_layout = QHBoxLayout(combo_container)
            combo_layout.setContentsMargins(0, 0, 0, 0)
            combo_layout.setSpacing(8)

            # 콤보박스
            combo = QComboBox()
            combo.setStyleSheet("""
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
            """)

            combo.setMinimumWidth(150)
            combo.setFixedHeight(40)

            if 'items' in kwargs:
                combo.addItems(kwargs['items'])

            # 선택 버튼
            add_button = QPushButton("Add")
            add_button.setStyleSheet("""
                QPushButton {
                    background-color: #1428A0;
                    color: white;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-family: Arial;
                    font-weight: 500;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #1a35cc;
                }
                QPushButton:pressed {
                    background-color: #1e429f;
                }
            """)
            add_button.setFixedHeight(40)
            add_button.setCursor(QCursor(Qt.PointingHandCursor))

            selected_items = []

            if 'default' in kwargs and isinstance(kwargs['default'], list):
                selected_items = kwargs['default'].copy()

            """
            선택된 항목 표시 업데이트
            """
            def update_selected_text():
                if selected_items:
                    selected_label.setText("Selected Items: " + ", ".join(map(str, selected_items)))
                else:
                    selected_label.setText("Selected Items: No items selected")

                self.setting_changed.emit(setting_key, selected_items.copy())

            update_selected_text()

            """
            항목 추가 버튼 클릭 이벤트
            """
            def add_selected_item():
                current_item = combo.currentText()

                if current_item and current_item not in selected_items:
                    selected_items.append(current_item)
                    update_selected_text()

            add_button.clicked.connect(add_selected_item)

            # 삭제 버튼
            remove_button = QPushButton("Remove")
            remove_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-family: Arial;
                    font-weight: 500;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
                QPushButton:pressed {
                    background-color: #bd2130;
                }
            """)
            remove_button.setFixedHeight(40)
            remove_button.setCursor(QCursor(Qt.PointingHandCursor))

            # 항목 제거 버튼 클릭 이벤트
            def remove_selected_item():
                current_item = combo.currentText()

                if current_item in selected_items:
                    selected_items.remove(current_item)
                    update_selected_text()

            remove_button.clicked.connect(remove_selected_item)

            combo_layout.addWidget(combo)
            combo_layout.addWidget(add_button)
            combo_layout.addWidget(remove_button)
            combo_layout.addStretch(1)

            container_multi_layout.addWidget(selected_label)
            container_multi_layout.addWidget(combo_container)

            widget = container_multi

        if widget:
            self.settings_layout.addRow(label, widget)
            return widget

        return None