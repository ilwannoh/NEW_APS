import os
import pandas as pd
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                          QTabWidget, QPushButton, QFileDialog)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QCursor, QFontMetrics
from app.views.components.result_components.table_widget.maintenance_rate.maintenance_table_widget import ItemMaintenanceTable, RMCMaintenanceTable
from app.views.components.common.enhanced_message_box import EnhancedMessageBox
from app.analysis.output.plan_maintenance import PlanMaintenanceAnalyzer
from app.models.common.file_store import DataStore, FilePaths

"""
계획 유지율 표시 위젯
"""
class PlanMaintenanceWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # UI 초기화
        self.setup_ui()

        # 상태 변수들
        self.item_maintenance_rate = None
        self.rmc_maintenance_rate = None
        self.adjusted_item_maintenance_rate = None
        self.adjusted_rmc_maintenance_rate = None
        
        # 변경된 아이템 추적 (분석 결과에서 받음)
        self.changed_items = set()
        self.changed_rmcs = set()

        # 이전 계획 정보 (사용자 선택)
        self.user_selected_plan_df = None  # 사용자가 직접 선택한 계획
        self.user_selected_plan_path = None
        
    """
    UI 초기화
    """
    def setup_ui(self):
        # 메인 레이아웃
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(5)
        
        # 데이터 없음 메시지
        self.no_data_message = QLabel("Please Load to Data")
        self.no_data_message.setAlignment(Qt.AlignCenter)
        self.no_data_message.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            background-color: transparent;
            border: none;
        """)
        
        # 데이터 있을 때 표시할 컨테이너
        self.content_container = QWidget()
        self.content_container.setStyleSheet("border: none;")  
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(5)
        
        # 초기 상태 설정
        self.main_layout.addWidget(self.no_data_message)
        self.main_layout.addWidget(self.content_container)
        self.content_container.hide()
        
        # UI 컴포넌트 생성
        self.create_info_section()
        self.create_toolbar()
        self.create_tabs()
        
    """
    툴바 영역 생성
    """
    def create_toolbar(self):
        # 버튼 위젯 생성
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 5)
        
        # 이전 계획 선택 버튼
        self.select_plan_btn = QPushButton("Select Previous Plan")
        self.select_plan_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.select_plan_btn.setStyleSheet("""
            QPushButton {
                background-color: #808080; 
                color: white; 
                border: none;
                border-radius: 5px;
                padding: 10px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0069d9;
            }
            QPushButton:pressed {
                background-color: #0062cc;
            }
        """)
        self.select_plan_btn.clicked.connect(self.select_previous_plan)
        
        # 계획 상태 레이블
        self.plan_status_label = QLabel("No previous plan loaded")
        self.plan_status_label.setStyleSheet("color: #6c757d; font-style: italic;")
        
        # 레이아웃에 추가
        button_layout.addWidget(self.select_plan_btn)
        button_layout.addStretch(1)
        button_layout.addWidget(self.plan_status_label)
        
        # 컨텐츠 레이아웃에 추가
        self.content_layout.addWidget(button_widget)
        
    """
    정보 섹션 생성
    """
    def create_info_section(self):
        # 상단 정보 위젯
        info_widget = QWidget()
        info_widget.setStyleSheet("background-color: white; border-radius: 8px; border: none;")
        info_layout = QHBoxLayout(info_widget)
        info_layout.setContentsMargins(5, 5, 5, 5)
        
        # 유지율 제목과 값
        title_font = QFont()
        title_font.setFamily("Arial")
        title_font.setPointSize(12)
        
        value_font = QFont()
        value_font.setFamily("Arial")
        value_font.setPointSize(12)
        value_font.setBold(True)
        
        self.rate_title_label = QLabel("Item Maintenance Rate :")
        self.rate_title_label.setFont(title_font)
        self.rate_title_label.setStyleSheet("color: #333333;")
        
        self.item_rate_label = QLabel("--")
        self.item_rate_label.setFont(value_font)
        self.item_rate_label.setStyleSheet("color: #1428A0;")
        
        info_layout.addWidget(self.rate_title_label)
        info_layout.addWidget(self.item_rate_label)
        info_layout.addStretch(1)
        
        # 컨텐츠 레이아웃에 추가
        self.content_layout.addWidget(info_widget)
        
    """
    탭 생성
    """
    def create_tabs(self):
        # 컨텐츠 위젯
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent; border: none;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.tab_widget.tabBar().setCursor(QCursor(Qt.PointingHandCursor))
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: white;
                border-radius: 8px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: black;
                font-family: Arial, sans-serif;
                font-weight: bold;
                font-size: 20px; 
            }
            QTabBar::tab:!selected {
                background-color: #E4E3E3;  
                font-family: Arial, sans-serif;
                font-weight: bold;
                font-size: 20px;  
            }
            QTabBar::tab {
                padding: 5px 5px;
                margin-left: 7px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-family: Arial, sans-serif;
                font-weight: bold;
                border: 1px solid #cccccc;
                border-bottom: none;
                font-size: 20px;  
                min-height: 18px;  /* 최소 높이 설정 */
            }
            QTabBar::tab::first { margin-left: 5px; }
        """)


        tab_bar = self.tab_widget.tabBar()
        tab_bar.setElideMode(Qt.ElideNone)  # 텍스트 생략 방지
        tab_bar.setExpanding(True)  # 탭이 전체 너비를 차지하지 않도록

        # Item별 탭
        self.item_tab = QWidget()
        item_layout = QVBoxLayout(self.item_tab)
        item_layout.setContentsMargins(8, 8, 8, 8)
        
        # Item별 테이블 위젯
        self.item_table = ItemMaintenanceTable()
        item_layout.addWidget(self.item_table)
        
        # RMC별 탭
        self.rmc_tab = QWidget()
        rmc_layout = QVBoxLayout(self.rmc_tab)
        rmc_layout.setContentsMargins(8, 8, 8, 8)
        
        # RMC별 테이블 위젯
        self.rmc_table = RMCMaintenanceTable()
        rmc_layout.addWidget(self.rmc_table)
        
        # 탭 추가
        self.tab_widget.addTab(self.item_tab, "Item Maintenance Rate")
        self.tab_widget.addTab(self.rmc_tab, "RMC Maintenance Rate")

        # 탭 바 설정 - 자동 크기 조정을 위한 커스텀 탭바 설정
        tab_bar = self.tab_widget.tabBar()
        tab_bar.setExpanding(False)
        
        # 폰트 설정
        font = tab_bar.font()
        font.setPointSize(14)
        tab_bar.setFont(font)
        
        # 동적으로 탭 크기 조정
        font_metrics = QFontMetrics(font)
        
        # 각 탭의 너비를 텍스트에 맞게 조정
        tab_bar.setTabSizeHint = lambda index: self.get_tab_size_hint(index, font_metrics)
        
        content_layout.addWidget(self.tab_widget)
        
        # 컨텐츠 레이아웃에 추가
        self.content_layout.addWidget(content_widget, 1)
        
        # 탭 변경 시 유지율 레이블 업데이트
        self.tab_widget.currentChanged.connect(self.update_rate_label)
    

    """
    result 페이지에서 이전 계획 업로드
    """
    def select_previous_plan(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Plan File", 
            "", 
            "Excel Files (*.xlsx *.xls);;All Files (*)",
            options=options
        )
        
        if file_path:
            try:
                # 이전 계획 로드
                self.user_selected_plan_df = pd.read_excel(file_path)
                self.user_selected_plan_path = file_path
                
                # 상태 레이블 업데이트
                file_name = os.path.basename(file_path)
                display_name = self.truncate_filename(file_name, max_length=35)
                self.plan_status_label.setText(f"Previous plan: {display_name}")
                self.plan_status_label.setStyleSheet("color: #1428A0; font-weight: bold;")
                self.plan_status_label.setToolTip(f"Full path: {file_path}")
                
                # 재분석 요청 (Controller를 통해)
                self.request_reanalysis()
                
                # 성공 메시지
                EnhancedMessageBox.show_validation_success(
                    self, 
                    "Previous Plan Loaded Successfully", 
                    f"Previous plan has been loaded successfully:\n{file_name}"
                )
                
            except Exception as e:
                self.plan_status_label.setText("Failed to load plan")
                self.plan_status_label.setStyleSheet("color: #6c757d; font-style: italic;")
                
                EnhancedMessageBox.show_validation_error(
                    self, 
                    "Load Failed", 
                    f"Failed to load previous plan: {str(e)}"
                )

    """
    위젯 분석 시행 메소드
    """
    def run_analysis(self, df):
        # UI 먼저 표시 (데이터 있으면 무조건 표시)
        if df is not None and not df.empty:
            self.no_data_message.hide()
            self.content_container.show()
        else:
            self.no_data_message.show()
            self.content_container.hide()
            return
        
        try:
            # 이전 계획 가져오기 
            previous_df = self.get_previous_plan()

            if previous_df is None or previous_df.empty:
                self.plan_status_label.setText("No previous plan available for comparison")
                self.plan_status_label.setStyleSheet("color: #6c757d; font-style: italic;")
            
            # 분석 수행
            result = PlanMaintenanceAnalyzer.analyze_maintenance_rate(df, previous_df)
            
            # UI 업데이트
            self.apply_analysis_results(result)
            
        except Exception as e:
            print(f"PlanMaintenanceWidget: 분석 오류: {e}")
            import traceback
            traceback.print_exc()


    """
    분석 결과만 받아서 UI 업데이트
    """
    def apply_analysis_results(self, plan_results):
        if not plan_results:
            return
        
        # 1. 단일 결과인 경우
        if 'analyzed' in plan_results:
            self._apply_single_result(plan_results)
        
        # 2. 비교 결과인 경우 (original/adjusted)
        elif 'original' in plan_results and 'adjusted' in plan_results:
            self._apply_comparison_results(plan_results)
        
        # 3. UI 업데이트
        self.update_rate_label(self.tab_widget.currentIndex())

                
    """
    단일 분석 결과 적용
    """
    def _apply_single_result(self, result):
        if not result.get('analyzed'):
            self.plan_status_label.setText(result.get('message', 'Analysis failed'))
            return
        
        # 유지율 설정
        item_data = result.get('item_data', {})
        rmc_data = result.get('rmc_data', {})
        
        self.item_maintenance_rate = item_data.get('rate', 0.0)
        self.rmc_maintenance_rate = rmc_data.get('rate', 0.0)
     
        # 변경된 아이템 정보 저장
        self.changed_items = result.get('changed_items', set())
        self.changed_rmcs = result.get('changed_rmcs', set())
        
        # 테이블 업데이트
        if item_data.get('df') is not None:
            self.item_table.populate_data(item_data['df'], self.changed_items)
        
        if rmc_data.get('df') is not None:
            self.rmc_table.populate_data(rmc_data['df'], self.changed_items, self.changed_rmcs)
        
        # 상태 메시지 업데이트
        self.plan_status_label.setText(result.get('message', 'Analysis completed'))

    def _apply_comparison_results(self, results):
        """비교 분석 결과 적용 (original vs adjusted)"""
        original = results.get('original', {})
        adjusted = results.get('adjusted', {})
        
        if not original.get('analyzed') or not adjusted.get('analyzed'):
            self.plan_status_label.setText("Comparison analysis failed")
            return
        
        # 원본 유지율
        orig_item = original.get('item_data', {})
        orig_rmc = original.get('rmc_data', {})
        self.item_maintenance_rate = orig_item.get('rate', 0.0)
        self.rmc_maintenance_rate = orig_rmc.get('rate', 0.0)
        
        # 조정된 유지율
        adj_item = adjusted.get('item_data', {})
        adj_rmc = adjusted.get('rmc_data', {})
        self.adjusted_item_maintenance_rate = adj_item.get('rate', 0.0)
        self.adjusted_rmc_maintenance_rate = adj_rmc.get('rate', 0.0)
        
        # 변경된 아이템 정보 (조정된 결과에서)
        self.changed_items = adjusted.get('changed_items', set())
        self.changed_rmcs = adjusted.get('changed_rmcs', set())
        
        # 테이블 업데이트 (조정된 결과로)
        if adj_item.get('df') is not None:
            self.item_table.populate_data(adj_item['df'], self.changed_items)
        
        if adj_rmc.get('df') is not None:
            self.rmc_table.populate_data(adj_rmc['df'], self.changed_items, self.changed_rmcs)
        
        self.plan_status_label.setText("Comparison analysis completed")

    """
    탭 인덱스에 따라 유지율 레이블 업데이트
    """
    def update_rate_label(self, index):
        if index == 0:  # Item별 탭
            self.rate_title_label.setText("Item Maintenance Rate :")
            original_rate = self.item_maintenance_rate
            adjusted_rate = self.adjusted_item_maintenance_rate
        else:  # RMC별 탭
            self.rate_title_label.setText("RMC Maintenance Rate :")
            original_rate = self.rmc_maintenance_rate
            adjusted_rate = self.adjusted_rmc_maintenance_rate

        # 초기 유지율이 있는 경우
        if original_rate is not None:
            original_rate_int = int(original_rate)

            if adjusted_rate is not None:
                adjusted_rate_int = int(adjusted_rate)
                self.item_rate_label.setText(f"{original_rate_int}% → {adjusted_rate_int}%")
                
                if adjusted_rate_int > original_rate_int:
                    self.item_rate_label.setStyleSheet("color: #1AB394; font-weight: bold;")
                elif adjusted_rate_int < original_rate_int:
                    self.item_rate_label.setStyleSheet("color: #f53b3b; font-weight: bold;")
                else:
                    self.item_rate_label.setStyleSheet("color: #1428A0; font-weight: bold;")
            else:
                self.item_rate_label.setText(f"{original_rate_int}%")
                if original_rate_int >= 90:
                    self.item_rate_label.setStyleSheet("color: #1AB394;")
                elif original_rate_int >= 70:
                    self.item_rate_label.setStyleSheet("color: #1428A0;")
                else:
                    self.item_rate_label.setStyleSheet("color: #f53b3b;")
        else:
            self.item_rate_label.setText("No data")
            

    """
    결과 데이터 설정
    """
    def set_data(self, result_data, start_date=None, end_date=None):
        if result_data is None or result_data.empty:
            # 데이터가 없는 경우
            self.no_data_message.show()
            self.content_container.hide()
            return False
            
        # 데이터가 있는 경우 UI 요소 표시
        self.no_data_message.hide()
        self.content_container.show() 
        return True
    
    def request_reanalysis(self):
        """재분석 요청 - Controller에게 알림"""
        # Controller에게 재분석 요청
        parent_widget = self.parent()
        while parent_widget:
            if hasattr(parent_widget, 'controller') and parent_widget.controller:
                controller = parent_widget.controller
                print("  → Controller 발견! 재분석 실행")
                controller._run_complete_analysis("계획 변경")
                break
            parent_widget = parent_widget.parent()
        else:
            print("PlanMaintenanceWidget: Controller 없음, 직접 분석 불가")
        
        
    """
    현재 선택된 이전 계획 반환
    """
    def get_previous_plan(self):
        # 사용자가 Result 페이지에서 직접 선택한 파일
        if self.user_selected_plan_df is not None:
            return self.user_selected_plan_df
    
        # DataStore에서 이전 계획 데이터 확인
        previous_plan_data = DataStore.get("result_file")
        if previous_plan_data is not None:
            return previous_plan_data
        
        file_path = FilePaths.get("result_file")
        if file_path and os.path.exists(file_path):
            
            # 파일 로드 시도
            previous_df = pd.read_excel(file_path)

            return previous_df
            
    """
    탭 크기 힌트 계산
    """
    def get_tab_size_hint(self, index, font_metrics):
        tab_text = self.tab_widget.tabText(index)
        text_width = font_metrics.width(tab_text)
        return QSize(text_width)  # 여백 추가
    

    """
    긴 파일명을 생략하여 표시
    """
    def truncate_filename(self, filename, max_length=30):
        if len(filename) <= max_length:
            return filename
        
        # 확장자 제거
        name_part, ext = os.path.splitext(filename)
        
        # 생략 후 길이 계산 (... + 확장자를 고려)
        available_length = max_length - 3 - len(ext)
        
        if available_length > 0:
            # 앞부분만 유지하고 ... 추가
            return name_part[:available_length] + "..." + ext
        else:
            # 매우 짧은 max_length인 경우
            return filename[:max_length-3] + "..."
    