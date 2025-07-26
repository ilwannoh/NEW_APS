# app/views/components/result_components/split_allocation_widget.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                            QLabel, QHeaderView, QTabWidget, QHBoxLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QBrush, QFont
import pandas as pd
from app.analysis.output.separate_region_and_group import analyze_line_allocation

class SplitAllocationWidget(QWidget):
    """여러 라인에 분산된 프로젝트 및 모델을 표시하는 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.result_df = None
        self.project_df = None
        self.model_df = None
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        # 전체 위젯 스타일
        self.setStyleSheet("""
            SplitAllocationWidget, 
            QLabel, 
            QTabWidget, 
            QTabBar, 
            QTableWidget,
            QHeaderView,
            QScrollBar {
                background-color: white;
                border: none;
            }
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
                margin: 0px;
                padding: 0px;
            }
            QTabWidget::tab-bar {
                left: 0px;
                border: none; 
            }
            QTabBar::tab {
                background: #e0e0e0;
                color: #333333;
                padding: 8px 16px;
                border: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #1428A0;
                color: white;
            }
        """)
        
        # 공통 테이블 스타일 - 테이블 주변 테두리만 제거, 내부 셀 구분선은 유지
        table_style = """
            QTableWidget {
                border: none !important;
                gridline-color: #E0E0E0;
                background-color: white;
                outline: none;
                selection-background-color: #0078D7;
                selection-color: white;
            }
            QHeaderView {
                border: none !important;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #1428A0;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: 1px solid #0c1a6b;
            }
            QTableView {
                border: none !important;
                outline: none;
            }
            QTableWidget::item {
                padding: 8px;
                border-right: 1px solid #d0d0d0; /* 열 구분선 */
                border-bottom: 1px solid #d0d0d0; /* 행 구분선 */
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
        """
        
        # 탭 컨테이너 생성
        project_tab = QWidget()
        model_tab = QWidget()
        
        # 탭 레이아웃 설정 (테두리 제거를 위해 별도 컨테이너 사용)
        project_layout = QVBoxLayout(project_tab)
        project_layout.setContentsMargins(0, 0, 0, 0)
        project_layout.setSpacing(0)
        
        model_layout = QVBoxLayout(model_tab)
        model_layout.setContentsMargins(0, 0, 0, 0)
        model_layout.setSpacing(0)
        
        # 프로젝트 테이블 (탭 1)
        self.project_table = QTableWidget()
        self.project_table.setStyleSheet(table_style)
        self.project_table.setFrameStyle(QTableWidget.NoFrame)  # 명시적으로 프레임 제거
        project_layout.addWidget(self.project_table)
        
        # 모델 테이블 (탭 2)
        self.model_table = QTableWidget()
        self.model_table.setStyleSheet(table_style)
        self.model_table.setFrameStyle(QTableWidget.NoFrame)  # 명시적으로 프레임 제거
        model_layout.addWidget(self.model_table)
        
        # 테이블 설정
        for table in [self.project_table, self.model_table]:
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.setAlternatingRowColors(True)
            table.horizontalHeader().setHighlightSections(False)
            table.verticalHeader().setVisible(False)
            table.setFrameShape(QTableWidget.NoFrame)  # 프레임 경계 제거
            table.setShowGrid(True)  # 그리드 라인 표시
            table.setStyleSheet(table_style)  # 각 테이블에 개별적으로 스타일 적용
        
        # 탭에 위젯 추가
        self.tab_widget.addTab(project_tab, "Project Split View")
        self.tab_widget.addTab(model_tab, "Model Split View")
        
        # 레이아웃에 위젯 추가
        self.main_layout.addWidget(self.tab_widget, 1)  # 스트레치 팩터 1 설정
        
        # 초기 메시지 설정
        self.set_initial_message()
        
    def set_initial_message(self):
        """초기 메시지 설정 - 데이터가 없을 때 표시"""
        for table in [self.project_table, self.model_table]:
            table.setRowCount(1)
            table.setColumnCount(1)
            table.setHorizontalHeaderLabels(["Message"])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            
            message_item = QTableWidgetItem("Please load result data first")
            message_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(0, 0, message_item)
    
    def run_analysis(self, result_data=None):
        """프로젝트 및 모델의 라인 할당 분석 실행"""
        if result_data is None or result_data.empty:
            self.set_initial_message()
            return
        
        # 분석 실행
        self.result_df, self.project_df, self.model_df = analyze_line_allocation(result_data, only_split=True)
        
        # 결과가 없으면 메시지 표시
        if self.project_df is None or self.project_df.empty:
            self.project_table.setRowCount(1)
            self.project_table.setColumnCount(1)
            self.project_table.setHorizontalHeaderLabels(["Message"])
            message_item = QTableWidgetItem("No split projects found")
            message_item.setTextAlignment(Qt.AlignCenter)
            self.project_table.setItem(0, 0, message_item)
        else:
            self.update_project_table()
        
        if self.model_df is None or self.model_df.empty:
            self.model_table.setRowCount(1)
            self.model_table.setColumnCount(1)
            self.model_table.setHorizontalHeaderLabels(["Message"])
            message_item = QTableWidgetItem("No split models found")
            message_item.setTextAlignment(Qt.AlignCenter)
            self.model_table.setItem(0, 0, message_item)
        else:
            self.update_model_table()
    
    def update_project_table(self):
        """프로젝트 테이블 업데이트 - 지역 열 제거"""
        if self.project_df is None or self.project_df.empty:
            return
        
        # 테이블 초기화
        self.project_table.setRowCount(0)
        self.project_table.setColumnCount(5)
        self.project_table.setHorizontalHeaderLabels([
            "Project", "Line Count", "Lines", "Model Count", "Total Qty"
        ])
        
        # 데이터 추가
        self.project_table.setRowCount(len(self.project_df))
        for row_idx, (_, row) in enumerate(self.project_df.iterrows()):
            project_item = QTableWidgetItem(str(row['Project']))
            project_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.project_table.setItem(row_idx, 0, project_item)
            
            # 라인 수 (색상으로 강조)
            line_count_item = QTableWidgetItem(str(row['LineCount']))
            line_count_item.setTextAlignment(Qt.AlignCenter)
            self.project_table.setItem(row_idx, 1, line_count_item)

            lines_item = QTableWidgetItem(str(row['Lines']))
            lines_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.project_table.setItem(row_idx, 2, lines_item)
            
            model_count_item = QTableWidgetItem(str(row['ModelCount']))
            model_count_item.setTextAlignment(Qt.AlignCenter)
            self.project_table.setItem(row_idx, 3, model_count_item)
            
            qty_item = QTableWidgetItem(f"{row['TotalQty']:,.0f}")
            qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.project_table.setItem(row_idx, 4, qty_item)
        
        # 열 너비 설정
        self.project_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)  # Project
        self.project_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)  # Line Count
        self.project_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)     # Lines
        self.project_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive) # Model Count
        self.project_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Interactive) # Total Qty
        
        # 최소 너비 설정 (더 넓게 조정)
        self.project_table.setColumnWidth(0, 150)  # Project
        self.project_table.setColumnWidth(1, 140)  # Line Count
        self.project_table.setColumnWidth(3, 170)  # Model Count
        self.project_table.setColumnWidth(4, 140)  # Total Qty
    
    def update_model_table(self):
        """모델 테이블 업데이트"""
        if self.model_df is None or self.model_df.empty:
            return
        
        # 테이블 초기화
        self.model_table.setRowCount(0)
        self.model_table.setColumnCount(6)
        self.model_table.setHorizontalHeaderLabels([
            "Model", "Region", "Line Count", "Lines", "Project Count", "Total Qty"
        ])
        
        # 데이터 추가
        self.model_table.setRowCount(len(self.model_df))
        for row_idx, (_, row) in enumerate(self.model_df.iterrows()):
            model_item = QTableWidgetItem(str(row['Item']))
            model_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.model_table.setItem(row_idx, 0, model_item)
            
            region_item = QTableWidgetItem(str(row['Region']))
            region_item.setTextAlignment(Qt.AlignCenter)
            self.model_table.setItem(row_idx, 1, region_item)
            
            # 라인 수
            line_count_item = QTableWidgetItem(str(row['LineCount']))
            line_count_item.setTextAlignment(Qt.AlignCenter)
            self.model_table.setItem(row_idx, 2, line_count_item)
            
            lines_item = QTableWidgetItem(str(row['Lines']))
            lines_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.model_table.setItem(row_idx, 3, lines_item)
            
            project_count_item = QTableWidgetItem(str(row['ProjectCount']))
            project_count_item.setTextAlignment(Qt.AlignCenter)
            self.model_table.setItem(row_idx, 4, project_count_item)
            
            qty_item = QTableWidgetItem(f"{row['TotalQty']:,.0f}")
            qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.model_table.setItem(row_idx, 5, qty_item)
        
        # 열 너비 설정
        self.model_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)  # Model
        self.model_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)  # Region
        self.model_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)  # Line Count
        self.model_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)      # Lines
        self.model_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Interactive)  # Project Count
        self.model_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Interactive)  # Total Qty
        
        # 최소 너비 설정 (더 넓게 조정)
        self.model_table.setColumnWidth(0, 240)  # Model (더 넓게)
        self.model_table.setColumnWidth(1, 100)  # Region
        self.model_table.setColumnWidth(2, 140)  # Line Count
        self.model_table.setColumnWidth(4, 170)  # Project Count
        self.model_table.setColumnWidth(5, 130)  # Total Qty