from PyQt5.QtWidgets import (QMessageBox, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
                             QFrame, QSplitter, QStackedWidget, QTableWidget, QHeaderView,
                            QScrollArea, QGridLayout, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QCursor
import pandas as pd
import os

from app.models.common.file_store import DataStore, FilePaths
from ..components.visualization.visualization_updater import VisualizationUpdater
from app.analysis.output.daily_capa_utilization import CapaUtilization
from app.analysis.output.capa_ratio import CapaRatioAnalyzer
from app.utils.export_manager import ExportManager
from app.core.output.adjustment_validator import PlanAdjustmentValidator
from app.resources.styles.result_style import ResultStyles 
from app.views.components.result_components.modified_left_section import ModifiedLeftSection
from app.views.components.result_components.table_widget.split_allocation_widget import SplitAllocationWidget
from app.views.components.result_components.items_container import ItemsContainer
from app.views.components.result_components.right_section.adj_error_manager import AdjErrorManager
from app.views.components.result_components.right_section.tabs.tab_manager import TabManager
from app.views.components.result_components.table_widget.split_allocation_widget import SplitAllocationWidget
from app.views.components.result_components.right_section.kpi_widget import KpiWidget
from app.models.output.assignment_model import AssignmentModel
from app.controllers.adjustment_controller import AdjustmentController
from app.models.common.screen_manager import *
from app.resources.fonts.font_manager import font_manager
from app.analysis.output.kpi_score import KpiScore
from app.views.components.common.enhanced_message_box import EnhancedMessageBox
from app.models.common.settings_store import SettingsStore
from app.models.common.file_store import FilePaths


class ResultPage(QWidget):
    export_requested = pyqtSignal(str)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.result_data = None # 결과 데이터 저장 변수
        self.capa_ratio_data = None
        self.data_changed_count = 0
        self.utilization_data = None # 가동률 데이터 저장 변수
        self.material_analyzer = None  # 자재 부족량 분석기 추가
        self.pre_assigned_items = set()  # 사전할당된 아이템 저장

        # MVC 모드 구분
        self.controller = None
        self._mvc_mode = False  # MVC 패턴 사용 여부

        # KPI Calculator 
        self.kpi_score = KpiScore(self.main_window)
        self.kpi_calculator = None
        self.demand_df = None  

        # 위젯 참조 (호환성 유지)
        self.summary_widget = None
        self.plan_maintenance_widget = None
        self.portcapa_widget = None
        self.shipment_widget = None
        self.split_allocation_widget = None
        self.material_widget = None  # MaterialWidget 참조 추가
        self.shortage_items_table = None
        self.viz_canvases = []

        self.init_ui()
        self.connect_signals()
        print("==== ResultPage: connect_signals 호출 완료 ====\n")
        

    def init_ui(self):
        bold_font = font_manager.get_just_font("SamsungSharpSans-Bold").family()
        normal_font = font_manager.get_just_font("SamsungOne-700").family()

        # 레이아웃 설정
        result_layout = QVBoxLayout(self)
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.setSpacing(0)

        # 타이틀 프레임
        title_frame = QFrame()
        title_frame.setStyleSheet("background-color: transparent;")
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(10, 10, 10, 0)
        title_layout.setSpacing(w(10))
        title_layout.setAlignment(Qt.AlignVCenter)

        # 타이틀 레이블
        title_label = QLabel("Result")
        title_label.setStyleSheet(f"font-family: {bold_font}; font-size: {f(21)}px; font-weight: 900;")
        title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        # Export 버튼
        export_btn = QPushButton("Export")
        export_btn.setCursor(QCursor(Qt.PointingHandCursor))
        export_btn.setFixedSize(w(100), h(40))
        export_btn.clicked.connect(self.export_results)
        export_btn.setStyleSheet(ResultStyles.EXPORT_BUTTON_STYLE)

        # Report 버튼
        report_btn = QPushButton("Report")
        report_btn.setCursor(QCursor(Qt.PointingHandCursor))
        report_btn.setFixedSize(w(100), h(40))
        report_btn.setStyleSheet(ResultStyles.EXPORT_BUTTON_STYLE)

        title_layout.addWidget(title_label)
        title_layout.addStretch(1)
        title_layout.addWidget(export_btn)
        # title_layout.addWidget(report_btn)

        # 타이틀 프레임을 메인 레이아웃에 추가
        result_layout.addWidget(title_frame)

        # 수평 스플리터 생성 (왼쪽 | 오른쪽)
        main_horizontal_splitter = QSplitter(Qt.Horizontal)
        main_horizontal_splitter.setHandleWidth(10)
        main_horizontal_splitter.setStyleSheet("QSplitter::handle { background-color: #F5F5F5; }")
        main_horizontal_splitter.setContentsMargins(10, 10, 10, 10)

        # =============== 왼쪽 컨테이너 ===============
        left_frame = QFrame()
        left_frame.setFrameShape(QFrame.StyledPanel)
        left_frame.setStyleSheet("background-color: white; border: 2px solid #cccccc;")

        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(10, 10, 10, 10)

        # 드래그 가능한 테이블 위젯 추가
        self.left_section = ModifiedLeftSection()
        self.left_section.parent_page = self  # 명시적 참조 설정

        # # 시그널 연결
        # self.left_section.viewDataChanged.connect(self.on_data_changed)  # 데이터 변경 시그널 연결

        left_layout.addWidget(self.left_section)
        
        # =============== 오른쪽 컨테이너 (3개 섹션 분할) ===============
        # 1) 수직 스플리터로 위/아래 분할
        right_vertical_splitter = QSplitter(Qt.Vertical)
        right_vertical_splitter.setHandleWidth(10)
        right_vertical_splitter.setStyleSheet("QSplitter::handle { background-color: #F5F5F5; }")

        # 2) 위쪽 영역을 수평 스플리터로 좌/우 분할
        right_top_horizontal_splitter = QSplitter(Qt.Horizontal)
        right_top_horizontal_splitter.setHandleWidth(5)
        right_top_horizontal_splitter.setStyleSheet("QSplitter::handle { background-color: #F5F5F5; }")

        # =============== 1. KPI Score 섹션 ===============
        kpi_frame = QFrame()
        kpi_frame.setFrameShape(QFrame.StyledPanel)
        kpi_frame.setStyleSheet(f"background-color: white; border:2px solid #cccccc;")

        kpi_layout = QGridLayout(kpi_frame)
        kpi_layout.setContentsMargins(0, 10, 0, 0)
        kpi_layout.setSpacing(0)

        # KPI 제목
        kpi_title = QLabel("KPI Score")
        kpi_title.setStyleSheet(f"color: #333; border: none; font-family: {bold_font}; font-size: {f(14)}px; font-weight: bold; margin-left: {w(10)}px")
        kpi_layout.addWidget(kpi_title)

        # KPI 위젯 영역 (계산된 점수들이 들어갈 공간)
        self.kpi_widget = KpiWidget()
        
        # KPI 라벨들을 생성하고 저장 (나중에 업데이트용)
        self.kpi_labels = {}
        kpi_layout.addWidget(self.kpi_widget)

        # 1) demand_df 로드
        self.demand_df = DataStore.get("organized_dataframes", {}).get("demand", pd.DataFrame())

        # 2) KPI 위젯과 데이터 연결
        self.kpi_score.set_kpi_widget(self.kpi_widget)
        self.kpi_score.set_data(
            result_data=self.result_data or pd.DataFrame(),
            material_anaylsis=self.material_analyzer,
            demand_df=self.demand_df
        )

        # 3) Base KPI 갱신
        self._refresh_base_kpi()

        # =============== 2. 조정 에러 메세지 섹션 ===============
        error_frame = QFrame()
        error_frame.setFrameShape(QFrame.StyledPanel)
        error_frame.setStyleSheet("background-color: white; border: 2px solid #cccccc;")
        
        error_layout = QVBoxLayout(error_frame)
        error_layout.setContentsMargins(0, 0, 0, 0)
        error_layout.setSpacing(10)

        # 에러 위젯
        self.error_display_widget = QWidget()
        self.error_display_layout = QVBoxLayout(self.error_display_widget)
        self.error_display_layout.setContentsMargins(5, 5, 5, 5)
        self.error_display_layout.setSpacing(5)
        self.error_display_layout.setAlignment(Qt.AlignTop)

        # 스크롤 가능한 에러 영역
        self.error_scroll_area = QScrollArea()
        self.error_scroll_area.setWidgetResizable(True)
        self.error_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.error_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.error_scroll_area.setWidget(self.error_display_widget)
        self.error_scroll_area.setStyleSheet("border: none;")

        # 에러 매니저 초기화
        self.error_manager = AdjErrorManager(
            parent_widget=self,
            error_scroll_area=self.error_scroll_area,
            navigate_callback=self.navigate_to_error_item,
            left_section=self.left_section
        )

        error_layout.addWidget(self.error_scroll_area)

        # 스플리터에 위젯 추가
        right_top_horizontal_splitter.addWidget(kpi_frame)
        right_top_horizontal_splitter.addWidget(error_frame)

        # 직접 픽셀 크기 지정 (1:1 비율)
        right_top_horizontal_splitter.setSizes([500, 500])  # 적절한 값으로 조정
   
        # =============== 3. 오른쪽 하단 섹션 : 지표 탭 ===============
        right_bottom_frame = QFrame()
        right_bottom_frame.setFrameShape(QFrame.StyledPanel)
        right_bottom_frame.setStyleSheet("background-color: white; border: 2px solid #cccccc;")

        right_bottom_layout = QVBoxLayout(right_bottom_frame)

        # 1) TabManager 인스턴스화
        self.tab_manager = TabManager(self)

        # 2) 스택 위젯 생성
        self.viz_stack = QStackedWidget()
        self.viz_stack.setStyleSheet("border: none;")

        # 3) stack_widget 연결 - *반드시* create_tab_buttons 전에
        self.tab_manager.set_stack_widget(self.viz_stack)

        # 4) 버튼 레이아웃 준비
        button_group_layout = QHBoxLayout()
        button_group_layout.setSpacing(5)
        button_group_layout.setContentsMargins(10, 10, 10, 5)
        button_group_layout.setAlignment(Qt.AlignCenter)  # 중앙 정렬

        # 5) 탭 버튼/페이지 생성
        self.tab_manager.create_tab_buttons(button_group_layout)
        self.viz_buttons = self.tab_manager.buttons    # 호환성을 위해 기존 참조 유지

        # 위젯 참조 설정 (호환성 유지)
        self._setup_widget_references()

        # 6) 레이아웃에 버튼과 스택 추가
        right_bottom_layout.addLayout(button_group_layout)
        right_bottom_layout.addWidget(self.viz_stack)

        # 오른쪽 수직 스플리터에 상단과 하단 프레임 추가
        right_vertical_splitter.addWidget(right_top_horizontal_splitter)
        right_vertical_splitter.addWidget(right_bottom_frame)
        
        # 상단과 하단의 비율 설정 
        # right_vertical_splitter.setSizes([250, 750])
        right_vertical_splitter.setStretchFactor(0, 3)  # 상단 
        right_vertical_splitter.setStretchFactor(1, 7)  # 하단 

        # 메인 수평 스플리터에 왼쪽과 오른쪽 프레임 추가
        main_horizontal_splitter.addWidget(left_frame)
        main_horizontal_splitter.addWidget(right_vertical_splitter)

        # 왼쪽과 오른쪽의 비율 설정 
        main_horizontal_splitter.setStretchFactor(0, 8)  # 왼쪽 80%
        main_horizontal_splitter.setStretchFactor(1, 2)  # 오른쪽 20%

        # 스플리터를 메인 레이아웃에 추가
        result_layout.addWidget(main_horizontal_splitter, 1)  # stretch factor 1로 설정하여 남은 공간 모두 차지


    """
    컨트롤러 설정 - MVC 모드 활성화
    """
    def set_controller(self, controller, defer_signal=False):
        self.controller = controller
        self._mvc_mode = True  # MVC 모드 활성화
        print("ResultPage: MVC 모드 활성화됨")

        # defer_signal=True일 경우, 연결을 나중에 호출자가 수동으로 하도록 함
        if not defer_signal and hasattr(controller.model, 'modelDataChanged'):
                # MVC 모드에서는 Controller를 통해서만 업데이트 받음
                controller.model.modelDataChanged.connect(self.update_ui_from_model)
                print("ResultPage: MVC 시그널 연결 완료")

    """
    시그널 연결 - MVC/Legacy 모드 구분
    """
    def connect_signals(self):
        if self._mvc_mode:
            print("ResultPage: MVC 모드 - Controller를 통한 연결만 사용")
            return

        # MVC 컨트롤러가 없는 경우: 레거시 직접 처리 방식 사용
        print("ResultPage: Legacy 모드 - 직접 연결 사용")
        if hasattr(self, 'left_section'):
            if hasattr(self.left_section, 'viewDataChanged'):
                self.left_section.viewDataChanged.connect(self.on_data_changed)
                print("ResultPage: Legacy viewDataChanged 연결")
        
            # 컨트롤러가 없을 때만 레거시 이벤트 핸들러 연결
            if hasattr(self.left_section, 'itemModified'):
                self.left_section.itemModified.connect(self.on_item_data_changed_legacy)
                print("ResultPage: Legacy itemModified 연결")

    """
    초기화 - 분석 결과와 함께 (MVC 전용)
    """
    def initialize_with_data(self, df, analysis_results):
        print("ResultPage: 분석 결과와 함께 초기화")
        
        self.result_data = df
        
        # 위젯 참조 설정
        if self.plan_maintenance_widget is None:
            self._setup_widget_references()

        # 사전할당 정보를 LeftSection에 먼저 전달
        if hasattr(self, 'pre_assigned_items') and hasattr(self, 'left_section'):
            print(f"ResultPage: 사전할당 정보를 LeftSection에 전달 - {len(self.pre_assigned_items)}개")
            self.left_section.set_pre_assigned_items(self.pre_assigned_items)
        else:
            print("ResultPage: 사전할당 정보 없음 또는 LeftSection 없음")
        
        # 분석 결과로 위젯 업데이트 (재분석 없음)
        self._update_widgets_with_analysis_results(analysis_results)

    """
    UI만 업데이트 - 분석 없음 (MVC 전용)
    """
    def update_ui_only(self, df, analysis_results):
        self.result_data = df
        
        # 각 위젯에 결과만 적용
        self._apply_material_results(analysis_results.get('material', {}))
        self._apply_shipment_results(analysis_results.get('shipment', {}))

    """
    자재 결과 적용 - 분석 없음
    """
    def _apply_material_results(self, material_results):
        if 'analyzer' in material_results:
            self.material_analyzer = material_results['analyzer']
            
            # Left Section에 결과만 전달
            if hasattr(self, 'left_section'):
                shortage_results = material_results.get('shortage_results', {})
                self.left_section.set_current_shortage_items(shortage_results)
    
    """
    출하 결과 적용 - 분석 없음
    """
    def _apply_shipment_results(self, shipment_results):
        if not shipment_results.get('analyzed'):
            return
            
        failure_items = shipment_results.get('failure_items', {})
            
        # 상태 변화 확인
        current_failures = getattr(self, '_last_shipment_failures', {})
        if current_failures != failure_items:
            print(f"출하 상태 업데이트: {len(failure_items)}개 실패 아이템")
            
            # Left Section에 전달
            if hasattr(self, 'left_section'):
                self.left_section.set_shipment_failure_items(failure_items)
            
            # 상태 저장
            self._last_shipment_failures = failure_items

    """
    분석 결과로 위젯 업데이트 - 재분석 없음
    """
    def _update_widgets_with_analysis_results(self, analysis_results):
        print("ResultPage: 분석 결과로 위젯 업데이트")
        
        if not analysis_results:
            return
        
        try:
            # 1. KPI 위젯 업데이트
            if 'kpi' in analysis_results:
                kpi_data = analysis_results['kpi']
                if 'base_scores' in kpi_data:
                    self.kpi_widget.update_scores(
                        base_scores=kpi_data['base_scores'],
                        adjust_scores=kpi_data.get('adjust_scores', {})
                    )
            
            # 2. 자재 위젯 업데이트
            if 'material' in analysis_results:
                material_data = analysis_results['material']
                if 'analyzer' in material_data and material_data['analyzer']:
                    self.material_analyzer = material_data['analyzer']

                    # 자재 부족 상태를 Left Section에 전달
                    if hasattr(self, 'left_section'):
                        self.left_section.set_current_shortage_items(
                            material_data.get('shortage_results', {})
                        )

            # 3.  출하 결과 업데이트
            if 'shipment' in analysis_results:
                self._apply_shipment_results(analysis_results['shipment'])
            
           # 4. 계획 유지율 위젯 업데이트
            if 'plan_maintenance' in analysis_results:
                print("계획 유지율 위젯 초기화는 위젯에서")
            
            # 5. 시각화 데이터 설정
            if 'capa_ratio' in analysis_results:
                self.capa_ratio_data = analysis_results['capa_ratio']
            
            if 'utilization' in analysis_results:
                self.utilization_data = analysis_results['utilization']
            
            # 5. 시각화 업데이트
            self.update_all_visualizations()
            
        except Exception as e:
            print(f"ResultPage: 위젯 업데이트 중 오류: {e}")
            import traceback
            traceback.print_exc()
    
    """
    출하 분석 호출 부분만 제거
    """
    def preload_tab_analyses(self, data):
        if data is None or data.empty:
            return
            
        try:
            # 현재 데이터 저장
            self.result_data = data
                
            # 자재 부족 분석은 유지
            if hasattr(self, 'material_widget') and self.material_widget:
                self.material_widget.run_analysis(data)
                self.material_analyzer = self.material_widget.get_material_analyzer()
                
        except Exception as e:
            print(f"사전 분석 실행 중 오류: {e}")

    """
    MVC 모드 전용 - 모델로부터 UI 업데이트
    """
    def update_ui_from_model(self, model_df=None):
        if not self._mvc_mode:
            print("ResultPage: Legacy 모드 - update_ui_from_model 실행")
            # Legacy 처리...
            if model_df is None and self.controller:
                model_df = self.controller.model.get_dataframe()
            
            if model_df is not None and not model_df.empty:
                self._update_all_components(model_df)
        else:
            print("ResultPage: MVC 모드 - update_ui_from_model 스킵 (Controller가 처리)")

    """
    Legacy 모드 또는 초기화용 - 데이터 변경 처리
    """
    def on_data_changed(self, data):
        if self._mvc_mode:
            print("ResultPage: MVC 모드에서 on_data_changed 직접 호출 차단")
            return
        
        print("ResultPage: Legacy 모드 - on_data_changed 실행")
        self._update_all_components(data)

    """
    계획 유지율 업데이트
    """
    def _update_plan_maintenance(self, data):
        if self.plan_maintenance_widget:
            start_date, end_date = self.main_window.data_input_page.date_selector.get_date_range()
            self.plan_maintenance_widget.set_data(data, start_date, end_date)

    """
    할당 분석 업데이트
    """
    def _update_split_allocation(self, data):
        if self.split_allocation_widget:
            self.split_allocation_widget.run_analysis(data)

    """
    요약 정보 업데이트
    """
    def _update_summary(self, data):
        if self.summary_widget:
            self.summary_widget.run_analysis(data)

    """
    시각화 데이터 준비
    """
    def _prepare_visualization_data(self, data):
        has_user_adjustments = False

        # MVC 모드에서 조정 여부 확인
        if self._mvc_mode and self.controller and hasattr(self.controller, 'model'):
            original_df = self.controller.model._original_df  # 원본 데이터
            current_df = self.controller.model._df  # 현재(조정된) 데이터
            
            if original_df is not None and current_df is not None:
                # 주요 컬럼 비교로 조정 여부 확인
                key_columns = ['Line', 'Time', 'Item', 'Qty']
                for col in key_columns:
                    if col in original_df.columns and col in current_df.columns:
                        if not original_df[col].equals(current_df[col]):
                            has_user_adjustments = True
                            print(f"시각화 업데이트: 조정 감지 - '{col}' 컬럼 변경됨")
                            break
        
        # 조정 여부에 따라 시각화 데이터 설정
        if has_user_adjustments and self._mvc_mode:
            if self.controller and self.controller.model:
                comparison_df = self.controller.model.get_comparison_dataframe()
                
                if comparison_df and 'original' in comparison_df and 'adjusted' in comparison_df:
                    self.capa_ratio_data = {
                        'original': CapaRatioAnalyzer.analyze_capa_ratio(comparison_df['original']),
                        'adjusted': CapaRatioAnalyzer.analyze_capa_ratio(comparison_df['adjusted'])
                    }
                    self.utilization_data = {
                        'original': CapaUtilization.analyze_utilization(comparison_df['original']),
                        'adjusted': CapaUtilization.analyze_utilization(comparison_df['adjusted'])
                    }
        else:
            self.capa_ratio_data = CapaRatioAnalyzer.analyze_capa_ratio(data_df=data, is_initial=True)
            self.utilization_data = CapaUtilization.analyze_utilization(data)

        # 시각화 갱신
        # self.update_all_visualizations()

    """
    Legacy 모드 전용 - 아이템 변경 처리
    """
    def on_item_data_changed_legacy(self, item, new_data):
        if self._mvc_mode:
            print("ResultPage: MVC 모드에서 Legacy 처리 차단")
            return
        
        print("ResultPage: Legacy 모드 - 아이템 변경 처리")
        # 위치 변경에 의한 호출인지 확인
        if hasattr(item, '_is_position_change'):
            return

        print("ResultPage: Legacy 모드 아이템 변경 처리 완료 (계획 유지율은 전체 분석에서 처리)")
        
    """
    최적화 결과 설정 - MVC 구조 초기화
    """
    def set_optimization_result(self, results):
        # 변수 초기화 - 중복 호출 방지 위한 추적
        self.data_changed_count = 0
        print("1. data_changed_count 초기화 완료")
        
        # 결과 데이터 추출
        assignment_result = results.get('assignment_result')
        pre_assigned_items = results.get('pre_assigned_items', [])
        optimization_metadata = results.get('optimization_metadata', {})
        
        # 사전할당 아이템을 초기화 단계에서 먼저 저장
        self.pre_assigned_items = set(pre_assigned_items)
        print(f"[DEBUG] 최적화 결과에서 사전할당 아이템 {len(self.pre_assigned_items)}개 설정")

        print("2. set_optimization_result : 컨트롤러 초기화 시작")
        # ─── MVC 구조 초기화 ───
        # 1) 기존 PlanAdjustmentValidator를 재사용해 validator 생성
        validator = PlanAdjustmentValidator(assignment_result,self)
        
        # 2) AssignmentModel 생성
        model = AssignmentModel(pd.DataFrame(assignment_result), list(self.pre_assigned_items), validator)
        
        # 3) AdjustmentController 생성 (error_manager 주입)
        controller = AdjustmentController(model, self.left_section, self.error_manager)
        
        print("3. 컨트롤러 생성 완료")
        
        # 4) ResultPage 참조 설정
        controller.set_result_page(self)
        print("4. 컨트롤러에 ResultPage 참조 전달")
        
        # 5) MVC 모드 설정
        self.set_controller(controller)
        
        # 6) Left Section에 validator와 controller 저장 (fallback용)
        self.left_section.set_validator(validator)
        self.left_section.set_controller(controller)
        
        print("5. 컨트롤러 세팅 완료")
        
        # 7) 초기 데이터 로드 (시그널 연결 전에)
        controller.initialize_views()
        print("6. 초기 데이터 설정 완료")

        
        # 8) 시그널 연결 (초기화 후 마지막에 수행)
        print("7. 시그널 연결 시작")
        controller.connect_signals()
        print("8. 시그널 연결 완료")
        
        # 메타데이터 필요시 - 추후 삭제
        self.optimization_metadata = optimization_metadata
        
        print(f"MVC 초기화 완료: Controller={controller}")
        return True
    
    """
    결과 파일 로드 및 MVC 구조 초기화
    
    Args:
        file_path: 선택적으로 파일 경로를 직접 전달 가능
    Returns:
        bool: 로드 성공 여부
    """
    def load_result_file(self, file_path=None):
        # 파일 선택 (경로가 전달되지 않은 경우)
        if file_path is None:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "결과 파일 선택", "", "Excel Files (*.xlsx *.xls *.csv)"
            )
        
        if not file_path or not os.path.exists(file_path):
            print(f"유효한 파일 경로가 아닙니다: {file_path}")
            return False
        
        try:
            print(f"[INFO] 결과 파일 로드 시작: {file_path}")
            
            # 기존 데이터 정리
            if hasattr(self, 'left_section'):
                self.left_section.clear_all_items()
            
            # 파일 로드
            from app.utils.fileHandler import load_file
            result_data = load_file(file_path)
            
            # 여러 시트가 반환되면 첫 번째 시트 사용
            if isinstance(result_data, dict):
                if 'result' in result_data:
                    result_data = result_data['result']
                else:
                    # 첫 번째 시트 사용
                    first_sheet_name = list(result_data.keys())[0]
                    result_data = result_data[first_sheet_name]
                    print(f"[INFO] '{first_sheet_name}' 시트 데이터 사용")
            
            # DataFrame이 아니면 변환
            if not isinstance(result_data, pd.DataFrame):
                print("[ERROR] 데이터를 DataFrame으로 변환할 수 없습니다.")
                EnhancedMessageBox.show_validation_error(
                    self, 
                    "파일 형식 오류", 
                    "파일에서 유효한 데이터를 찾을 수 없습니다."
                )
                return False
            
            # 데이터 검증 - 필수 컬럼 확인
            required_columns = ['Line', 'Time', 'Item']
            missing_columns = [col for col in required_columns if col not in result_data.columns]
            
            if missing_columns:
                EnhancedMessageBox.show_validation_error(
                    self,
                    "파일 형식 오류",
                    f"필수 열이 없습니다: {', '.join(missing_columns)}\n올바른 형식의 파일을 선택해주세요."
                )
                return False
            
            # 데이터 타입 정규화
            try:
                if 'Line' in result_data.columns:
                    result_data['Line'] = result_data['Line'].astype(str)
                
                if 'Time' in result_data.columns:
                    result_data['Time'] = pd.to_numeric(result_data['Time'], errors='coerce').fillna(0).astype(int)
                
                if 'Item' in result_data.columns:
                    result_data['Item'] = result_data['Item'].astype(str)
                
                if 'Qty' in result_data.columns:
                    result_data['Qty'] = pd.to_numeric(result_data['Qty'], errors='coerce').fillna(0).astype(int)
            except Exception as e:
                print(f"[WARNING] 데이터 타입 변환 중 오류: {e}")

            FilePaths.set("optimizer_file", file_path)
            
            # MVC 구조 초기화
            print("[INFO] MVC 구조 초기화 시작")
            
            # 1. 검증기(Validator) 생성
            validator = PlanAdjustmentValidator(result_data,self)
            print("[INFO] 검증기 생성 완료")
            
            # 2. 사전할당 아이템 식별
            pre_assigned_items = set()
            if 'Type' in result_data.columns:
                pre_assigned_mask = result_data['Type'] == 'Pre-assigned'
                if pre_assigned_mask.any():
                    pre_assigned_items = set(result_data.loc[pre_assigned_mask, 'Item'].unique())
            
            # 3. 모델(Model) 생성
            model = AssignmentModel(result_data, list(pre_assigned_items), validator)
            print("[INFO] 모델 생성 완료")
            
            # 4. 컨트롤러(Controller) 생성
            controller = AdjustmentController(model, self.left_section, self.error_manager)
            print("[INFO] 컨트롤러 생성 완료")
            
            # 5. 컨트롤러에 ResultPage 참조 설정
            controller.set_result_page(self)
            
            # 6. MVC 모드 설정
            self.set_controller(controller)
            
            # 7. Left Section에 validator와 controller 설정
            self.left_section.set_validator(validator)
            self.left_section.set_controller(controller)
            print("[INFO] 검증기 및 컨트롤러 설정 완료")
            
            # 8. 초기 데이터 설정
            controller.initialize_views()
            print("[INFO] 초기 데이터 설정 완료")
            
            # 9. 시그널 연결
            controller.connect_signals()
            print("[INFO] 시그널 연결 완료")
            
            # 10. 사전할당 상태 설정
            self.pre_assigned_items = pre_assigned_items
            if pre_assigned_items:
                self.update_left_widget_pre_assigned_status(pre_assigned_items)
                print(f"[INFO] {len(pre_assigned_items)}개 사전할당 아이템 상태 설정")
            
            # 11. 자재 부족 분석 실행
            try:
                if hasattr(self, 'material_widget') and self.material_widget:
                    self.material_widget.run_analysis(result_data)
                    self.material_analyzer = self.material_widget.get_material_analyzer()
                    print("[INFO] 자재 부족 분석 완료")
            except Exception as e:
                print(f"[WARNING] 자재 부족 분석 중 오류: {e}")
            
            # 성공 메시지 표시
            EnhancedMessageBox.show_validation_success(
                self,
                "File Loaded Successfully",
                 f"File has been successfully loaded.\nRows: {result_data.shape[0]}, Columns: {result_data.shape[1]}"
            )
            
            # 데이터 변경 이벤트 발생
            if hasattr(self, 'on_data_changed'):
                self.on_data_changed(result_data)
            
            print("[INFO] 파일 로드 및 MVC 초기화 완료")

            return True
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            EnhancedMessageBox.show_validation_error(
                self,
                "File Loding Error", 
                f"An error occurred while loading the file.\n{str(e)}"
            )
            return False
        

    """
    Material 탭 콘텐츠 생성
    """
    def _create_material_tab_content(self, layout):
        material_page = QWidget()
        material_layout = QVBoxLayout(material_page)
        material_layout.setContentsMargins(0, 0, 0, 0)
        
        # 자재 부족 테이블
        self.shortage_items_table = QTableWidget()
        self.shortage_items_table.setColumnCount(4)
        self.shortage_items_table.setHorizontalHeaderLabels(["Material", "Model", "Shortage", "Shift"])
        self.shortage_items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # 테이블 스타일 적용
        self._apply_material_table_style()
        
        # 테이블 이벤트 연결
        self.shortage_items_table.setMouseTracking(True)
        self.shortage_items_table.cellEntered.connect(self.show_shortage_tooltip)
        
        material_layout.addWidget(self.shortage_items_table)
        layout.addWidget(material_page)
    
    """
    위젯 참조 설정
    """
    def _setup_widget_references(self):
        # Summary 위젯
        summary_tab = self.tab_manager.get_tab_instance('Summary')
        if summary_tab:
            self.summary_widget = summary_tab.summary_widget

        # Plan 위젯
        plan_tab = self.tab_manager.get_tab_instance('Plan')
        if plan_tab:
            self.plan_maintenance_widget = plan_tab.plan_maintenance_widget

        # PortCapa 위젯
        portcapa_tab = self.tab_manager.get_tab_instance('PortCapa')
        if portcapa_tab:
            self.portcapa_widget = portcapa_tab.portcapa_widget

        # Shipment 위젯
        shipment_tab = self.tab_manager.get_tab_instance('Shipment')
        if shipment_tab:
            self.shipment_widget = shipment_tab.shipment_widget

        # SplitView 위젯 
        splitview_tab = self.tab_manager.get_tab_instance('SplitView')
        if splitview_tab:
            self.split_allocation_widget = splitview_tab.split_allocation_widget
        # 없으면 직접 생성
        elif self.split_allocation_widget is None:
            self.split_allocation_widget = SplitAllocationWidget()

        # Material 위젯 및 테이블
        material_tab = self.tab_manager.get_tab_instance('Material')
        if material_tab:
            # MaterialTab에서 material_widget 가져오기 
            self.material_widget = material_tab.get_widget() if hasattr(material_tab, 'get_widget') else None
            self.shortage_items_table = material_tab.get_table()

            # 자재 부족 정보 업데이트 시그널 연결
            if hasattr(self.material_widget, 'material_shortage_updated'):
                self.material_widget.material_shortage_updated.connect(self.on_material_shortage_updated)

        # 캔버스 리스트 설정
        capa_tab = self.tab_manager.get_tab_instance('Capa')
        if capa_tab:
            self.viz_canvases = capa_tab.get_canvases()
    
                        
    """
    시각화 페이지 전환 및 버튼 스타일 업데이트
    """
    def switch_viz_page(self, index):
        # TabManager를 통한 탭 전환 (호환성 유지)
        self.tab_manager.switch_tab(index)

    """
    자재 부족 정보가 업데이트되었을 때 호출되는 함수
    """
    def on_material_shortage_updated(self, shortage_dict):
        # 왼쪽 섹션에 자재 부족 정보 전달
        if hasattr(self, 'left_section'):
            self.left_section.set_current_shortage_items(shortage_dict)
            
        # 기존에 사용하던 material_analyzer 업데이트
        if hasattr(self, 'material_widget') and self.material_widget:
            self.material_analyzer = self.material_widget.get_material_analyzer()
        
    """
    각 지표별 초기 시각화 생성
    """
    def create_initial_visualization(self, canvas, viz_type):
        # 각 지표 예시
        if viz_type == "Capa":
            VisualizationUpdater.update_capa_chart(canvas, self.capa_ratio_data)
        
        elif viz_type == "Utilization":
            if self.utilization_data is None:
                try:
                    self.utilization_data = CapaUtilization.analyze_utilization(self.result_data)
                    print("Finished Utilization Rate :", self.utilization_data)
                except Exception as e:
                    print(f"Utilization Rate Error : {str(e)}")
                    self.utilization_data = {}
            
            VisualizationUpdater.update_utilization_chart(canvas, self.utilization_data)


    """
    모든 시각화 차트 업데이트
    """
    def update_all_visualizations(self):
        # Capa 탭 업데이트 
        capa_tab = self.tab_manager.get_tab_instance('Capa')
        if capa_tab:
            capa_tab.update_content(self.capa_ratio_data, self.utilization_data)
        else:
            print("[디버그] Capa 탭을 찾을 수 없음")


    """
    개별 시각화 차트 업데이트
    """
    def update_visualization(self, canvas, viz_type):
        if viz_type == "Capa":
            VisualizationUpdater.update_capa_chart(canvas, self.capa_ratio_data)
        elif viz_type == "Utilization":
            VisualizationUpdater.update_utilization_chart(canvas, self.utilization_data)
        elif viz_type == "Material":
            # Material 위젯이 있는 경우
            if hasattr(self, 'material_widget') and self.material_widget:
                self.material_widget.run_analysis(self.result_data)
        elif viz_type == "PortCapa":
            pass
    

    """
    최종 최적화 결과를 파일로 내보내는 메서드
    """
    def export_results(self):
        try:
            # 저장 경로 설정
            save_dir = SettingsStore.get("op_SavingRoute", "")
            print(f"설정에서 불러온 저장 경로: {save_dir}")

            # 데이터가 있는지 확인
            if hasattr(self, 'controller') and self.controller and hasattr(self.controller, 'model'):
                export_data = self.controller.model.get_dataframe_for_display()
                print("모델에서 get_dataframe_for_display 가져오기")
                print(f"필터링된 데이터 컬럼: {export_data.columns.tolist()}")

                if export_data is not None and not export_data.empty:
                    print("데이터 존재")
                    internal_fields = [col for col in export_data.columns if
                                       col.startswith('_') or col in ['_id', '_is_copy']]
                    if internal_fields:
                        print(f"경고: 여전히 내부 필드가 존재합니다: {internal_fields}")

                    start_date, end_date = self.main_window.data_input_page.date_selector.get_date_range()

                    # 저장 로직에 저장 경로 전달
                    saved_path = ExportManager.export_data(
                        parent=self,
                        data_df=export_data,
                        start_date=start_date,
                        end_date=end_date,
                        is_planning=False,
                    )

                    if saved_path:
                        self.export_requested.emit(saved_path)

                else:
                    print("No data to export.")
                    QMessageBox.warning(self, "Export Error", "No data to export.")

            else:
                print("내보내기 컨트롤러 없음.")
                if hasattr(self, 'left_section') and hasattr(self.left_section,
                                                             'data') and self.left_section.data is not None:
                    start_date, end_date = self.main_window.data_input_page.date_selector.get_date_range()

                    saved_path = ExportManager.export_data(
                        parent=self,
                        data_df=self.left_section.data,
                        start_date=start_date,
                        end_date=end_date,
                        is_planning=False,
                    )
                    if saved_path:
                        self.export_requested.emit(saved_path)
                else:
                    print("No data to export.")
                    QMessageBox.warning(self, "Export Error", "No data to export.")
        except Exception as e:
            print(f"Export 과정에서 오류 발생: {str(e)}")
            QMessageBox.critical(self, "Export Error", f"An error occurred during export:\n{str(e)}")

    """
    아이템 상태 업데이트 - 사전할당, 자재부족, 출하실패
    """
    def _update_item_status(self):
        print("ResultPage: 아이템 상태 업데이트")
        
        try:
            # 사전할당 상태 적용
            if self.pre_assigned_items and hasattr(self, 'left_section'):
                self.update_left_widget_pre_assigned_status(self.pre_assigned_items)
            
            # 자재 부족 상태 적용
            if (hasattr(self, 'material_analyzer') and 
                self.material_analyzer and 
                hasattr(self.material_analyzer, 'shortage_results') and
                hasattr(self, 'left_section')):
                self.update_left_widget_shortage_status(self.material_analyzer.shortage_results)
            
            # 출하 실패 상태 적용
            if (hasattr(self, 'left_section') and 
                hasattr(self.left_section, 'shipment_failure_items') and 
                self.left_section.shipment_failure_items):
                self.left_section.apply_shipment_failure_status()
                
        except Exception as e:
            print(f"아이템 상태 업데이트 중 오류: {e}")
    
    """
    왼쪽 위젯의 아이템들에 자재 부족 상태 적용
    
    Args:
        shortage_dict: {item_code: [{shift: shift_num, material: material_code, shortage: shortage_amt}]}
    """
    def update_left_widget_shortage_status(self, shortage_dict):
        if not hasattr(self, 'left_section') or not hasattr(self.left_section, 'grid_widget'):
            return
        
        # 그리드의 모든 컨테이너 순회
        for row_containers in self.left_section.grid_widget.containers:
            for container in row_containers:
                # 각 컨테이너의 아이템들 순회
                for item in container.items:
                    if hasattr(item, 'item_data') and item.item_data and 'Item' in item.item_data:
                        item_code = item.item_data['Item']
                        item_time = item.item_data.get('Time')  # 시프트(Time) 정보 가져오기
                        
                        # 해당 아이템이 자재 부족 목록에 있는지 확인
                        if item_code in shortage_dict:
                            # 시프트별 부족 정보 검사
                            shortages_for_item = shortage_dict[item_code]
                            matching_shortages = []
                            
                            for shortage in shortages_for_item:
                                shortage_shift = shortage.get('shift')
                                
                                # 시프트가 일치하면 부족 정보 저장
                                if shortage_shift and item_time and int(shortage_shift) == int(item_time):
                                    matching_shortages.append(shortage)
                            
                            # 일치하는 시프트의 부족 정보가 있으면 부족 상태로 설정
                            if matching_shortages:
                                item.set_shortage_status(True, matching_shortages)
                            else:
                                item.set_shortage_status(False)
                        else:
                            # 부족 목록에 없는 경우 부족 상태 해제
                            item.set_shortage_status(False)
 
    """
    왼쪽 위젯에 사전할당 상태 적용
    """
    def update_left_widget_pre_assigned_status(self, pre_assigned_items):
        if not hasattr(self, 'left_section') or not hasattr(self.left_section, 'grid_widget'):
            return
        
        # 그리드의 모든 컨테이너 순환
        for row_containers in self.left_section.grid_widget.containers:
            for container in row_containers:
                # 각 컨테이너의 아이템들 순환
                for item in container.items:
                    if hasattr(item, 'item_data') and item.item_data and 'Item' in item.item_data:
                        item_code = item.item_data['Item']

                        # 해당 아이템이 사전할당 목록에 있는지 확인
                        if item_code in pre_assigned_items:
                            item.set_pre_assigned_status(True)
                        else:
                            item.set_pre_assigned_status(False)

    """
    에러 관리 메서드
    """
    def add_validation_error(self, item_info, error_message):
        self.error_manager.add_validation_error(item_info, error_message)

    """
    에러 아이템 navigation 및 highlight
    """
    def navigate_to_error_item(self, error_info):
        # print(f"navigate_to_error_item 호출: {error_info}")
        item_info = error_info['item_info']

        if not hasattr(self, 'left_section') or not hasattr(self.left_section, 'grid_widget'):
            return
        
        # 먼저 모든 아이템 선택 해제
        self.left_section.grid_widget.clear_all_selections()
        
        # 그리드에서 해당 아이템 찾기
        found_item = None
        
        if '_id' in item_info and item_info['_id']:
            # ID로 아이템 찾기
            target_id = item_info['_id']
            
            for row_idx, row_containers in enumerate(self.left_section.grid_widget.containers):
                for col_idx, container in enumerate(row_containers):
                    for item in container.items:
                        if (hasattr(item, 'item_data') and item.item_data and 
                            item.item_data.get('_id') == target_id):
                            found_item = item
                            break
                    if found_item:
                        break
                if found_item:
                    break

        # ID로 찾지 못한 경우 기존 방식으로 찾기
        if not found_item:
            target_line = str(item_info.get('Line', ''))
            target_time = str(item_info.get('Time', ''))
            target_item = str(item_info.get('Item', ''))
            
            for row_idx, row_containers in enumerate(self.left_section.grid_widget.containers):
                for col_idx, container in enumerate(row_containers):
                    for item in container.items:
                        if hasattr(item, 'item_data') and item.item_data:
                            current_line = str(item.item_data.get('Line', ''))
                            current_time = str(item.item_data.get('Time', ''))
                            current_item = str(item.item_data.get('Item', ''))
                            
                            if (current_line == target_line and 
                                current_time == target_time and 
                                current_item == target_item):
                                found_item = item
                                break
                        if found_item:
                            break
                    if found_item:
                        break
                if found_item:
                    break

        if found_item:
            # 아이템 선택 및 강조
            found_item.set_selected(True)
            
            # 컨테이너에도 선택 이벤트 전달
            container = found_item.parent()
            if hasattr(container, 'on_item_selected'):
                container.on_item_selected(found_item)
            
            # 그리드 위젯에도 선택 이벤트 전달
            self.left_section.grid_widget.on_item_selected(found_item, container)
            
            # 스크롤 이동 
            QTimer.singleShot(50, lambda: self.scroll_to_item(found_item))
            
            print("아이템으로 이동 완료")
        else:
            print("해당 아이템을 찾을 수 없습니다")

        
    """
    해당 아이템으로 스크롤 이동
    """
    def scroll_to_item(self, item):
        # print(f"scroll_to_item 호출 : {item}")
        
        # QScrollArea 찾기
        scroll_area = None
        parent = item.parent()
        while parent:
            if isinstance(parent, QScrollArea):
                scroll_area = parent
                break
            parent = parent.parent()
        
        if not scroll_area:
            print("QScrollArea를 찾지 못했습니다.")
            return
        
        # 아이템이 속한 컨테이너 찾기
        container = item.parent()
        if not isinstance(container, ItemsContainer):
            print("ItemsContainer를 찾지 못했습니다.")
            return
        
        # 스크롤 영역의 viewport 가져오기
        viewport = scroll_area.viewport()
        scroll_widget = scroll_area.widget()
        
        # 아이템의 전역 좌표를 스크롤 위젯 기준으로 변환
        item_global_pos = item.mapToGlobal(item.rect().center())
        item_pos_in_scroll = scroll_widget.mapFromGlobal(item_global_pos)
        
        # 현재 스크롤 위치 가져오기
        h_scrollbar = scroll_area.horizontalScrollBar()
        v_scrollbar = scroll_area.verticalScrollBar()
        
        # 아이템 위치 계산
        item_y = item_pos_in_scroll.y()
        viewport_height = viewport.height()
        
        # 아이템이 화면 중앙에 오도록 스크롤 위치 계산
        target_y = item_y - viewport_height // 2
        
        # 스크롤 위치 조정
        v_scrollbar.setValue(target_y)
    

    """
    결과 데이터 설정 및 KPI 초기화
    """
    def set_result_data(self, result_data, material_analyzer=None, demand_df=None):
        self.result_data = result_data
        self.material_analyzer = material_analyzer
        self.demand_df = demand_df
        
        # KPI Calculator 초기화
        if result_data is not None:
            self.kpi_calculator = KpiScore(self.main_window)
            self.kpi_calculator.set_data(result_data, material_analyzer, demand_df)
            
            # 초기 KPI 계산 및 표시
            self.update_kpi_scores()
        
        # 왼쪽 섹션에 데이터 설정
        if hasattr(self.left_section, 'data_manager'):
            self.left_section.data_manager.set_data_from_external(result_data)
        
        # Material 위젯에 분석기 설정 및 분석 실행
        if hasattr(self, 'material_widget') and self.material_widget:
            if material_analyzer:
                self.material_widget.set_material_analyzer(material_analyzer)
            self.material_widget.run_analysis(result_data)
    
    """
    KPI 점수 계산 및 라벨 업데이트
    """
    def update_kpi_scores(self):
        if not self.kpi_calculator:
            return
        
        try:
            # Base 점수 계산 (초기 최적화 결과)
            base_scores = self.kpi_calculator.calculate_all_scores()
            
            # Adjust 점수 계산 (사용자 조정 후 - 현재는 Base와 동일)
            adjust_scores = base_scores.copy()
            
            # 라벨 업데이트
            self.update_kpi_labels("Base", base_scores)
            self.update_kpi_labels("Adjust", adjust_scores)
            
            print(f"KPI Scores - Base: {base_scores}, Adjust: {adjust_scores}")
            
        except Exception as e:
            print(f"KPI 계산 오류: {e}")
            # 오류 발생 시 기본값 표시
            default_scores = {'Total': 0, 'Mat': 0, 'SOP': 0, 'Util': 0}
            self.update_kpi_labels("Base", default_scores)
            self.update_kpi_labels("Adjust", default_scores)
    
    """
    KPI 라벨 업데이트
    """
    def update_kpi_labels(self, row_type, scores):
        # 점수에 따른 색상 결정
        def get_color(score):
            if score >= 90:
                return "#28a745"  # 초록색
            elif score >= 70:
                return "#ffc107"  # 노란색  
            else:
                return "#dc3545"  # 빨간색
        
        # 각 점수 라벨 업데이트
        for col_name in ["Total", "Mat", "SOP", "Util"]:
            label_key = f"{row_type}_{col_name}"
            
            if label_key in self.kpi_labels:
                score = scores.get(col_name, 0)
                color = get_color(score)
                
                # 라벨 텍스트와 스타일 업데이트
                self.kpi_labels[label_key].setText(f"{score:.1f}")
                self.kpi_labels[label_key].setStyleSheet(f"""
                    QLabel {{
                        color: {color};
                        font-weight: bold;
                        border: none;
                        padding: 5px;
                    }}
                """)

    """
    KPI 점수 초기화
    """
    def clear_kpi_scores(self):
        for label_key, label in self.kpi_labels.items():
            label.setText("--")
            label.setStyleSheet("""
                QLabel {
                    color: #555;
                    border: none;
                    padding: 5px;
                }
            """)


    """
    Base KPI 점수를 계산하고 위젯에 표시
    """
    def _refresh_base_kpi(self):
        demand_df = None

        # 원본 결과(조정 전) 점수 계산
        demand_path = FilePaths.get("demand_excel_file")
        if demand_path and os.path.exists(demand_path):
            # 모든 시트를 dict 형태로 읽어오기
            demand_df = pd.read_excel(demand_path, sheet_name='demand')
            
        data = self.result_data if (self.result_data is not None and not self.result_data.empty) else pd.DataFrame()
        self.kpi_score.set_data(
            result_data=data,
            material_anaylsis=self.material_analyzer,
            demand_df=demand_df
        )

        # Base 점수 계산 (소수점 값 그대로 전달)
        base_scores = self.kpi_score.calculate_all_scores()
        print(f"base_scores : {base_scores}")
        

        # 조정이 있다면 adjust 점수 표시
        has_user_adjustments = False

        if self.controller and hasattr(self.controller, 'model'):
            try:
                # 원본과 현재 데이터 비교 (가장 직접적인 방법)
                original_df = self.controller.model._original_df  # 원본 데이터
                current_df = self.controller.model._df  # 현재(조정된) 데이터

                if original_df is not None and current_df is not None:
                    # 1) 행 수가 다른지 확인 (추가/삭제 있음)
                    if len(original_df) != len(current_df):
                        has_user_adjustments = True
                        print("조정 감지: 행 수가 변경됨")
                    else:
                        # 2) 주요 컬럼 값이 다른지 확인
                        key_columns = ['Line', 'Time', 'Item', 'Qty']
                        for col in key_columns:
                            if col in original_df.columns and col in current_df.columns:
                                # 컬럼 값이 하나라도 다르면 조정이 있는 것
                                if not original_df[col].equals(current_df[col]):
                                    has_user_adjustments = True
                                    print(f"조정 감지: '{col}' 컬럼 값이 변경됨")
                                    break

                    # 조정이 있는 경우에만 Adjust 점수 계산
                    if has_user_adjustments:
                        # 조정 데이터로 KPI 점수 계산
                        self.kpi_score.set_data(
                            result_data=current_df,  # 현재 조정된 데이터 사용
                            material_anaylsis=self.material_analyzer,
                            demand_df=demand_df
                        )
                        
                        # Adjust 점수 계산
                        adjust_scores = self.kpi_score.calculate_all_scores()
                        
                        # KpiScoreWidget에 Adjust 점수 설정
                        self.kpi_widget.update_scores(adjust_scores=adjust_scores)
                        
                        print(f"KPI 점수 업데이트 (조정 있음): Base={base_scores}, Adjust={adjust_scores}")
                    else:
                        # 새로운 KpiScoreWidget에 Base 점수 설정
                        self.kpi_widget.update_scores(base_scores=base_scores)
                        print("조정 없음: KPI Adjust 점수 표시하지 않음")
            except Exception as e:
                print(f"조정 여부 확인 중 오류: {str(e)}")
                import traceback
                traceback.print_exc()
            
        # 조정이 없으면 Adjust 점수 초기화
        if not has_user_adjustments:
            self.kpi_widget.update_scores(adjust_scores={})

        
    """
    현재 데이터로 분산 배치 분석 업데이트
    """
    def update_split_view_analysis(self, data):
        # SplitView 탭 인스턴스 가져오기
        split_tab = self.tab_manager.get_tab_instance('SplitView')
        
        if split_tab and hasattr(split_tab, 'get_widget'):
            # SplitAllocationWidget 가져오기
            split_widget = split_tab.get_widget()
            
            if split_widget and hasattr(split_widget, 'run_analysis'):
                # 분석 실행
                split_widget.run_analysis(data)
