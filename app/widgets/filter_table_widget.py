"""
필터링 기능이 포함된 테이블 위젯
엑셀 스타일의 필터링 기능 제공
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                           QPushButton, QMenu, QCheckBox, QLineEdit, QFrame,
                           QWidgetAction, QHeaderView, QTableWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from typing import Dict, List, Set


class FilterMenu(QMenu):
    """필터 메뉴"""
    
    # 시그널
    filter_changed = pyqtSignal(int, set)  # column, selected_values
    
    def __init__(self, column: int, parent=None):
        super().__init__(parent)
        self.column = column
        self.all_values = set()
        self.selected_values = set()
        self.check_boxes = {}
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        # 검색 입력
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("검색...")
        self.search_input.textChanged.connect(self.filter_items)
        search_layout.addWidget(self.search_input)
        
        search_action = QWidgetAction(self)
        search_action.setDefaultWidget(search_widget)
        self.addAction(search_action)
        
        self.addSeparator()
        
        # 전체 선택/해제 버튼
        select_widget = QWidget()
        select_layout = QHBoxLayout(select_widget)
        
        select_all_btn = QPushButton("전체 선택")
        select_all_btn.clicked.connect(self.select_all)
        select_layout.addWidget(select_all_btn)
        
        clear_btn = QPushButton("전체 해제")
        clear_btn.clicked.connect(self.clear_all)
        select_layout.addWidget(clear_btn)
        
        select_action = QWidgetAction(self)
        select_action.setDefaultWidget(select_widget)
        self.addAction(select_action)
        
        self.addSeparator()
    
    def set_values(self, values: Set[str]):
        """필터 값 설정"""
        self.all_values = values
        self.selected_values = values.copy()
        
        # 기존 체크박스 제거
        for action in self.actions()[4:]:  # 검색, 구분선, 버튼 이후
            self.removeAction(action)
        self.check_boxes.clear()
        
        # 정렬된 값으로 체크박스 생성
        for value in sorted(values):
            checkbox = QCheckBox(str(value))
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.on_filter_changed)
            
            checkbox_action = QWidgetAction(self)
            checkbox_action.setDefaultWidget(checkbox)
            self.addAction(checkbox_action)
            
            self.check_boxes[value] = checkbox
    
    def filter_items(self, text: str):
        """항목 필터링"""
        for value, checkbox in self.check_boxes.items():
            checkbox.setVisible(text.lower() in str(value).lower())
    
    def select_all(self):
        """전체 선택"""
        for checkbox in self.check_boxes.values():
            if checkbox.isVisible():
                checkbox.setChecked(True)
        self.on_filter_changed()
    
    def clear_all(self):
        """전체 해제"""
        for checkbox in self.check_boxes.values():
            if checkbox.isVisible():
                checkbox.setChecked(False)
        self.on_filter_changed()
    
    def on_filter_changed(self):
        """필터 변경"""
        self.selected_values.clear()
        for value, checkbox in self.check_boxes.items():
            if checkbox.isChecked():
                self.selected_values.add(value)
        
        self.filter_changed.emit(self.column, self.selected_values)


class FilterTableWidget(QTableWidget):
    """필터링 기능이 포함된 테이블 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_menus = {}
        self.column_filters = {}  # column -> selected_values
        self.all_rows_data = []  # 전체 데이터 저장
        
        # 헤더 클릭 이벤트
        self.horizontalHeader().sectionClicked.connect(self.show_filter_menu)
        self.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                padding-right: 20px;
            }
        """)
    
    def setHorizontalHeaderLabels(self, labels: List[str]):
        """헤더 라벨 설정"""
        # 필터 아이콘 추가
        filter_labels = []
        for label in labels:
            filter_labels.append(f"{label} ▼")
        super().setHorizontalHeaderLabels(filter_labels)
    
    def show_filter_menu(self, column: int):
        """필터 메뉴 표시"""
        # 해당 열의 고유 값 수집
        values = set()
        for row in range(self.rowCount()):
            item = self.item(row, column)
            if item:
                values.add(item.text())
        
        # 필터 메뉴 생성 또는 가져오기
        if column not in self.filter_menus:
            menu = FilterMenu(column, self)
            menu.filter_changed.connect(self.apply_filter)
            self.filter_menus[column] = menu
        else:
            menu = self.filter_menus[column]
        
        menu.set_values(values)
        
        # 메뉴 표시
        header_pos = self.horizontalHeader().sectionViewportPosition(column)
        menu_pos = self.mapToGlobal(self.horizontalHeader().pos())
        menu_pos.setX(menu_pos.x() + header_pos)
        menu_pos.setY(menu_pos.y() + self.horizontalHeader().height())
        menu.exec_(menu_pos)
    
    def apply_filter(self, column: int, selected_values: Set[str]):
        """필터 적용"""
        self.column_filters[column] = selected_values
        
        # 모든 행에 대해 필터 적용
        for row in range(self.rowCount()):
            show_row = True
            
            # 각 열의 필터 확인
            for col, values in self.column_filters.items():
                item = self.item(row, col)
                if item and item.text() not in values:
                    show_row = False
                    break
            
            self.setRowHidden(row, not show_row)
    
    def save_all_data(self):
        """현재 테이블의 모든 데이터 저장"""
        self.all_rows_data = []
        for row in range(self.rowCount()):
            row_data = []
            for col in range(self.columnCount()):
                item = self.item(row, col)
                row_data.append(item.text() if item else "")
            self.all_rows_data.append(row_data)
    
    def restore_all_data(self):
        """저장된 데이터로 테이블 복원"""
        self.setRowCount(len(self.all_rows_data))
        for row, row_data in enumerate(self.all_rows_data):
            for col, text in enumerate(row_data):
                self.setItem(row, col, QTableWidgetItem(text))
    
    def clear_filters(self):
        """모든 필터 해제"""
        self.column_filters.clear()
        for row in range(self.rowCount()):
            self.setRowHidden(row, False)