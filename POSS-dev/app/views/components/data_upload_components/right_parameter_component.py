from PyQt5.QtGui import QFont, QColor, QIcon
from PyQt5.QtWidgets import (
    QWidget, QPushButton,
    QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QHBoxLayout,
    QFrame
)
from PyQt5.QtCore import pyqtSignal, Qt
from app.utils.error_handler import (
    error_handler, safe_operation, DataError, ValidationError, AppError
)
from app.resources.fonts.font_manager import font_manager
from app.models.common.screen_manager import *
from app.models.common.settings_store import SettingsStore


class RightParameterComponent(QWidget):
    show_failures = pyqtSignal(dict)
    close_button_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._init_ui()

        try:
            self.show_failures.connect(self._on_failures)
        except Exception as e:
            raise AppError(f'Failed to connect signals : {str(e)}')

    """
    UI 요소 초기화 및 배치
    """

    @error_handler(
        show_dialog=False,
        default_return=None
    )
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 전체 배경색 설정
        self.setStyleSheet("background-color: white; border: none;")

        # 제목 영역을 위한 프레임
        title_frame = QFrame()
        title_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #F5F5F5;
                border: none;
                border-bottom: {h(1)}px solid #E0E0E0;
            }}
        """)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(w(10), h(8), w(10), h(8))

        title_label = QLabel("Problems")
        title_font = font_manager.get_just_font("SamsungOne-700").family()
        title_label.setStyleSheet(f"color: #333333; background-color: transparent; border: none; font-family: {title_font}; font-weight: bold; font-size: {f(24)}px;")

        minimize_button = QPushButton()
        minimize_button.setIcon(self.style().standardIcon(self.style().SP_TitleBarMinButton))
        minimize_button.setFixedSize(w(24), h(24))
        minimize_button.setCursor(Qt.PointingHandCursor)
        minimize_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: {h(4)}px;
                padding: {w(4)}px;
            }}
            QPushButton:hover {{
                background-color: #F5F5F5;
                border-color: #1428A0;
            }}
            QPushButton:pressed {{
                background-color: #E0E0E0;
            }}
        """)
        minimize_button.clicked.connect(self.close_button_clicked.emit)

        # Problems 와 최소화버튼
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(minimize_button)

        layout.addWidget(title_frame)

        # 컨텐츠 영역
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: none;
            }
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # 리스트 컨테이너
        list_container = QFrame()
        list_container.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: {h(8)}px;
            }}
        """)
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{ 
                border: none; 
                outline: none;
                background-color: white;
                border-radius: {w(8)}px;
                font-family: {font_manager.get_just_font("SamsungOne-700").family()};
                font-size: {f(20)}px;
            }}
            QListWidget::item {{
                padding: {h(10)}px {w(15)}px;
                border: none;
                border-bottom: 1px solid #F5F5F5;
                margin: 0px;
            }}
            QListWidget::item:selected {{
                background-color: #E8ECFF;
                color: black;
            }}
            QListWidget::item:hover {{
                background-color: #F8F9FA;
            }}
            QScrollBar:vertical {{
                        border: none;
                        width: 10px;
                        margin: 0px;
                    }}
                    QScrollBar::handle:vertical {{
                        background: #CCCCCC;
                        min-height: 20px;
                        border-radius: 5px;
                    }}
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                        border: none;
                        background: none;
                        height: 0px;
                    }}
                    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                        background: none;
                    }}
                    QScrollBar:horizontal {{
                        border: none;
                        height: 10px;
                        margin: 0px;
                    }}
                    QScrollBar::handle:horizontal {{
                        background: #CCCCCC;
                        min-width: 20px;
                        border-radius: 5px;
                    }}
                    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                        border: none;
                        background: none;
                        width: 0px;
                    }}
                    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                        background: none;
                    }}
        """)

        list_layout.addWidget(self.list_widget)
        content_layout.addWidget(list_container)
        layout.addWidget(content_frame)

    """
    파일 선택 이벤트 처리
    """

    @error_handler(
        default_return=None
    )
    def on_file_selected(self, filepath: str):
        pass

    """
    실패 정보 표시 처리
    """

    @error_handler(
        default_return=None
    )
    def _on_failures(self, failures: dict):
        if not isinstance(failures, dict):
            raise DataError('Failures must be a dictionary', {'type': type(failures)})

        safe_operation(
            self.list_widget.clear,
            'Error clearing list widget'
        )

        # Production Capacity Issues
        try:
            production_capacity_issues = failures.get('production_capacity', [])

            if production_capacity_issues:
                # 섹션 헤더 추가
                header_item = QListWidgetItem("Production Capacity Issues")
                header_item.setFont(font_manager.get_font('SamsungOne-700', 11))
                header_item.setBackground(QColor('#F8F9FA'))
                header_item.setForeground(QColor('#1428A0'))
                header_item.setFlags(Qt.ItemIsEnabled)  # 선택 불가능하게
                self.list_widget.addItem(header_item)

                for issue in production_capacity_issues:
                    line = issue.get('line', 'Unknown')
                    reason = issue.get('reason', 'capacity exceeded')
                    available = issue.get('available', 0)
                    excess = issue.get('excess', 0)
                    center = issue.get('center', '')

                    center_info = f'({center})' if center else ''
                    item_text = f'{reason} : {line}{center_info}, Available capacity : {available}, Excess amount : {excess}'

                    item = QListWidgetItem(item_text)
                    item_font = font_manager.get_font('SamsungOne-700', 9)
                    item.setFont(item_font)

                    # 에러 아이템 스타일링
                    item.setForeground(QColor('#E74C3C'))

                    safe_operation(
                        self.list_widget.addItem,
                        'Error adding capacity issue item',
                        item
                    )
        except Exception as e:
            raise DataError(f'Error processing production capacity issues : {str(e)}')

        # Plan Retention
        try:
            if failures.get('plan_retention') is not None:
                plan_retention = failures.get('plan_retention', {})
                if plan_retention:
                    # 섹션 헤더 추가
                    header_item = QListWidgetItem("Plan Retention")
                    header_item.setFont(font_manager.get_font('SamsungOne-700', 11))
                    header_item.setBackground(QColor('#F8F9FA'))
                    header_item.setForeground(QColor('#1428A0'))
                    header_item.setFlags(Qt.ItemIsEnabled)
                    self.list_widget.addItem(header_item)
                    for error in plan_retention:
                        item = QListWidgetItem(error['reason'])
                        item_font = font_manager.get_font('SamsungOne-700', 9)
                        item.setFont(item_font)
                        item.setForeground(QColor('#E74C3C'))
                        self.list_widget.addItem(item)


            
        except Exception as e:
            raise DataError(f'Error processing plan retention data : {str(e)}')

        # Preassign Failures
        try:
            preassign_failures = failures.get('preassign', [])

            if preassign_failures:
                # 섹션 헤더 추가
                header_item = QListWidgetItem("Preassignment Issues")
                header_item.setFont(font_manager.get_font('SamsungOne-700', 11))
                header_item.setBackground(QColor('#F8F9FA'))
                header_item.setForeground(QColor('#1428A0'))
                header_item.setFlags(Qt.ItemIsEnabled)
                self.list_widget.addItem(header_item)

                for error in preassign_failures:
                    tgt = error.get('Target', 'Unknown')
                    sh = error.get('Shift', 'Unknown')
                    reason = error.get('Reason', 'Unknown')
                    amt = error.get('ViolationAmt', 'Unknown')

                    reason_to_phrase = {
                        'equipment capacity': 'equipment capacity',
                        'number of concurrent lines': 'concurrent line count',
                        'maximum production quantity': 'maximum production quantity'
                    }

                    if amt is not None:
                        phrase = reason_to_phrase.get(reason, reason)
                        text = f"Line {tgt} has exceeded its {phrase} by {amt} at shift {sh}."
                    else:
                        text = f"{reason} for item {tgt}."

                    item = QListWidgetItem(text)
                    item_font = font_manager.get_font('SamsungOne-700', 9)
                    item.setFont(item_font)
                    item.setForeground(QColor('#E74C3C'))

                    safe_operation(
                        self.list_widget.addItem,
                        'Error adding preassign failure item',
                        item
                    )
        except Exception as e:
            raise DataError(f'Error processing preassign failures : {str(e)}')

        # Materials Negative Stock
        # try:
        #     if failures.get('materials_negative_stock'):
        #         negative_stock_materials = failures.get('materials_negative_stock', {})
        #
        #         # 섹션 헤더 추가
        #         header_item = QListWidgetItem("Materials - Negative Stock")
        #         header_item.setFont(font_manager.get_font('SamsungOne-700', 11))
        #         header_item.setBackground(QColor('#F8F9FA'))
        #         header_item.setForeground(QColor('#1428A0'))
        #         header_item.setFlags(Qt.ItemIsEnabled)
        #         self.list_widget.addItem(header_item)
        #
        #         for date, materials in negative_stock_materials.items():
        #             # 날짜 헤더
        #             date_item = QListWidgetItem(f'Negative initial stock materials:')
        #             date_item.setFont(font_manager.get_font('SamsungOne-700', 10))
        #             date_item.setForeground(QColor('#E74C3C'))
        #             self.list_widget.addItem(date_item)
        #
        #             for material in materials:
        #                 material_id = material.get('material_id', 'Unknown')
        #                 stock = material.get('stock', 0)
        #
        #                 detail_item = QListWidgetItem(f'  • {material_id} : {stock}')
        #                 detail_item.setFont(font_manager.get_font('SamsungOne-700', 10))
        #                 detail_item.setForeground(QColor('#E74C3C'))
        #
        #                 safe_operation(
        #                     self.list_widget.addItem,
        #                     'Error adding material item',
        #                     detail_item
        #                 )
        # except Exception as e:
        #     raise DataError(f'Error processing negative stock materials : {str(e)}')