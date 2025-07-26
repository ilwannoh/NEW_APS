from PyQt5.QtWidgets import (QTableWidget, QHeaderView, QTableWidgetItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush, QFont
import pandas as pd
from app.models.common.screen_manager import *
from app.resources.fonts.font_manager import font_manager

class CustomTable(QTableWidget):
    def __init__(self, headers=[], parent=None):
        super().__init__(parent)
        self.setup_default_settings()
        self.setup_appearance()
        if headers:
            self.setup_header(headers)
    
    """기본 테이블 설정"""
    def setup_default_settings(self):
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setAlternatingRowColors(False)
        self.verticalHeader().setVisible(False)
        self.setFrameShape(QTableWidget.NoFrame)
        self.setFocusPolicy(Qt.StrongFocus)
        
    """테이블 위젯의 기본 스타일 설정"""
    def setup_appearance(self):
        self.setStyleSheet("""
            QTableWidget {
                border: none;
                gridline-color: #E0E0E0;
                background-color: white;
                selection-background-color: #0078D7;
                selection-color: white;
                outline: none;
            }
            QHeaderView::section {
                background-color: #1428A0;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: 1px solid #0c1a6b;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #d0d0d0;
                border-right: 1px solid #d0d0d0;
            }
            QTableWidget::item:selected {
                background-color: #0078D7;
                color: white;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                border: none;
                background: #f5f5f5;
                width: 10px;
                height: 10px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #c0c0c0;
                border-radius: 5px;
                min-height: 20px;
                min-width: 20px;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                border: none;
                background: none;
                height: 0px;
                width: 0px;
            }
            QScrollBar::add-page, QScrollBar::sub-page {
                background: none;
            }
        """)


    """테이블을 읽기 전용으로 설정"""
    def make_read_only(self):
        # 테이블 전체를 읽기 전용으로 설정
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 선택 모드 설정 (행 단위 선택)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        
        # 포커스 정책 설정
        self.setFocusPolicy(Qt.StrongFocus)
        

    """
    헤더 설정
    header_labels: 헤더 라벨 리스트
    fixed_columns: {index: width} 형태의 dict. 고정하고 싶은 열의 인덱스와 너비
    resizable: 열 크기 조정 가능 여부
    """
    def setup_header(self, header_labels, fixed_columns=None, resizable=True):
        self.setColumnCount(len(header_labels))
        self.setHorizontalHeaderLabels(header_labels)
        
        header = self.horizontalHeader()
        
        # 헤더 설정
        header.setSectionsClickable(False)  # 클릭 불가
        header.setHighlightSections(False)  # 선택 시 강조 표시 비활성화
        
        # 정렬 기능은 필요에 따라 활성화
        header.setSortIndicatorShown(False)
        self.setSortingEnabled(False)
        
        # 열 크기 설정
        fixed_columns = fixed_columns or {}
        
        if resizable:
            # 크기 조정 가능한 모드
            for i in range(len(header_labels)):
                if i in fixed_columns:
                    header.setSectionResizeMode(i, QHeaderView.Fixed)
                    header.resizeSection(i, fixed_columns[i])
                else:
                    header.setSectionResizeMode(i, QHeaderView.Interactive)
                    
            # 마지막 열은 늘어나도록 설정 
            if len(header_labels) > 0 and len(header_labels) - 1 not in fixed_columns:
                header.setSectionResizeMode(len(header_labels) - 1, QHeaderView.Stretch)
        else:
            # 모든 열을 균등하게 늘림
            for i in range(len(header_labels)):
                if i in fixed_columns:
                    header.setSectionResizeMode(i, QHeaderView.Fixed)
                    header.resizeSection(i, fixed_columns[i])
                else:
                    header.setSectionResizeMode(i, QHeaderView.Stretch)

        # 헤더 텍스트 중앙 정렬
        for i in range(len(header_labels)):
            item = self.horizontalHeaderItem(i)
            if item:
                item.setTextAlignment(Qt.AlignCenter)


    """메시지 표시"""
    def set_message(self, message: str, span_all_columns=True):
        self.clear()
        self.setRowCount(1)
        
        if span_all_columns and self.columnCount() > 1:
            # 모든 열에 걸쳐 메시지 표시
            item = QTableWidgetItem(message)
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(0, 0, item)
            self.setSpan(0, 0, 1, self.columnCount())
        else:
            # 단일 열에 메시지 표시
            self.setColumnCount(1)
            self.setHorizontalHeaderLabels(["Message"])
            self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            
            item = QTableWidgetItem(message)
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(0, 0, item)

    """
    DataFrame 데이터를 테이블에 설정
    df: 표시할 DataFrame
    formatters: {column_name: function} 형태의 포맷터 딕셔너리
    alignments: {column_name: alignment} 형태의 정렬 딕셔너리
    """
    def set_data(self, df: pd.DataFrame, formatters=None, alignments=None):
        if df is None or df.empty:
            self.set_message("No data to display.")
            return

        self.clear()
        self.setRowCount(len(df))
        self.setColumnCount(len(df.columns))
        self.setHorizontalHeaderLabels(df.columns.tolist())

        # 기본 포맷터 및 정렬 설정
        formatters = formatters or {}
        alignments = alignments or {}
        
        # 데이터 입력
        for row_idx, (_, row) in enumerate(df.iterrows()):
            for col_idx, (col_name, value) in enumerate(row.items()):
                # 포맷터 적용
                if col_name in formatters:
                    display_value = formatters[col_name](value)
                else:
                    # 숫자인 경우 기본 포맷 적용
                    if pd.isna(value):
                        display_value = ""
                    elif isinstance(value, (int, float)):
                        if isinstance(value, float) and value.is_integer():
                            display_value = f"{int(value):,}"
                        else:
                            display_value = f"{value:,.1f}"
                    else:
                        display_value = str(value)
                
                item = QTableWidgetItem(display_value)
                
                # 정렬 설정
                if col_name in alignments:
                    item.setTextAlignment(alignments[col_name])
                else:
                    # 숫자 컬럼은 우측 정렬, 나머지는 중앙 정렬
                    if isinstance(value, (int, float)) and not pd.isna(value):
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    else:
                        item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
                
                self.setItem(row_idx, col_idx, item)

        # 기본 행 높이 설정
        for row in range(len(df)):
            self.setRowHeight(row, 25)

    def add_custom_row(self, row_data, styles=None, is_total=False, is_header=False):
        """
        커스텀 스타일의 행 추가
        row_data: 행 데이터 리스트
        styles: {column_index: {'background': color, 'font': font, 'alignment': alignment}} 형태
        is_total: 총계 행 여부
        is_header: 헤더 스타일 행 여부
        """
        row_idx = self.rowCount()
        self.insertRow(row_idx)
        
        styles = styles or {}
        
        for col_idx, value in enumerate(row_data):
            item = QTableWidgetItem(str(value))
            
            # 기본 정렬
            if isinstance(value, (int, float)) and col_idx >= 2:  # 숫자 컬럼 (보통 3번째부터)
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            else:
                item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)

            # 커스텀 스타일 적용
            if col_idx in styles:
                style = styles[col_idx]
                if 'background' in style:
                    item.setBackground(QBrush(style['background']))
                if 'foreground' in style:
                    item.setForeground(QBrush(style['foreground']))
                if 'font' in style:
                    item.setFont(style['font'])
                if 'alignment' in style:
                    item.setTextAlignment(style['alignment'])

            else:
                # 총계 행 스타일
                if is_total:
                    item.setBackground(QBrush(QColor('#E8E8E8')))
                    item.setForeground(QBrush(QColor('#333333')))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                
                # 헤더 스타일 행
                elif is_header:
                    item.setBackground(QBrush(QColor('#f5f5f5')))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
            
            self.setItem(row_idx, col_idx, item)
        
        # 행 높이 설정
        if is_total or is_header:
            self.setRowHeight(row_idx, 35)
        else:
            self.setRowHeight(row_idx, 25)
    
    def highlight_row(self, row_idx, color):
        """특정 행 강조"""
        for col in range(self.columnCount()):
            item = self.item(row_idx, col)
            if item:
                item.setBackground(QBrush(color))
    
    def set_cell_style(self, row, col, background=None, foreground=None, font=None, alignment=None):
        """특정 셀 스타일 설정"""
        item = self.item(row, col)
        if item:
            if background:
                item.setBackground(QBrush(background))
            if foreground:
                item.setForeground(QBrush(foreground))
            if font:
                item.setFont(font)
            if alignment:
                item.setTextAlignment(alignment)
    
    def merge_cells(self, row, col, row_span, col_span):
        """셀 병합"""
        self.setSpan(row, col, row_span, col_span)
    
    def resize_columns_to_content(self):
        """컬럼을 내용에 맞게 크기 조정"""
        self.resizeColumnsToContents()
    
    def on_cell_clicked(self, row, column):
        """셀 클릭 이벤트 (필요시 오버라이드)"""
        value = self.item(row, column).text() if self.item(row, column) else ""
        print(f"Clicked on cell ({row}, {column}): {value}")