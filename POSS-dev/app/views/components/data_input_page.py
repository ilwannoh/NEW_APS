from PyQt5.QtCore import pyqtSignal, QDate, Qt, QTimer
from PyQt5.QtWidgets import (QVBoxLayout, QFrame, QHBoxLayout, QLabel, QPushButton,
                             QSplitter, QStackedWidget, QTabBar,
                             QMessageBox)
from PyQt5.QtGui import QCursor
import pandas as pd
import os
import re

from app.core.input.pre_assign import run_allocation
from app.core.input.maintenance import calc_plan_retention
from app.models.common.file_store import FilePaths, DataStore

from app.views.components.data_upload_components.date_range_selector import DateRangeSelector
from app.views.components.data_upload_components.file_upload_component import FileUploadComponent
from app.views.components.data_upload_components.left_parameter_component import LeftParameterComponent
from app.views.components.data_upload_components.file_explorer_sidebar import FileExplorerSidebar
from app.views.components.data_upload_components.progress_dialog import OptimizationProgressDialog
from app.views.components.data_upload_components.data_input_components import FileTabManager
from app.views.components.data_upload_components.data_input_components import DataModifier
from app.views.components.data_upload_components.data_input_components import SidebarManager
from app.views.components.data_upload_components.right_parameter_component import RightParameterComponent
from app.views.components.data_upload_components.save_confirmation_dialog import SaveConfirmationDialog

from app.analysis.input.capa_analysis import PjtGroupAnalyzer
from app.analysis.input.material_analyzer import MaterialAnalyzer
from app.analysis.input.shipment_analysis import calculate_fulfillment_rate
from app.models.input.capa import process_data
from app.models.input.shipment import preprocess_data_for_fulfillment_rate
from app.resources.fonts.font_manager import font_manager
from app.utils.command.undo_redo_initializer import initialize_undo_redo_in_data_input_page
from app.models.common.screen_manager import *
from app.models.common.settings_store import SettingsStore

class DataInputPage(QWidget) :
    file_selected = pyqtSignal(str)
    date_range_selected = pyqtSignal(QDate, QDate)
    run_button_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.loaded_files = {}
        self.current_file = None
        self.current_sheet = None

        self.init_ui()

        self.sidebar_manager = SidebarManager(self)
        self.tab_manager = FileTabManager(self)
        self.data_modifier = DataModifier(self)

        self._connect_signals()

        initialize_undo_redo_in_data_input_page(self)

    def init_ui(self) :
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        main_container = QFrame()
        main_container.setStyleSheet("border:none; border-radius: 0px;")
        main_container_layout = QVBoxLayout(main_container)
        main_container_layout.setContentsMargins(0, 0, 0, 0)
        main_container_layout.setSpacing(0)

        top_container = QFrame()
        top_container_layout = QVBoxLayout(top_container)
        top_container_layout.setContentsMargins(w(10), h(10), w(10), h(10))
        top_container_layout.setSpacing(h(10))
        top_container.setStyleSheet("background-color: #F5F5F5; border-radius: 0px;")
        top_container.setMinimumHeight(h(100))

        # title_row 레이아웃을 수정하여 타이틀과 버튼이 같은 높이에 있도록 합니다
        title_row = QFrame()
        title_row.setStyleSheet("background-color: transparent;")
        title_row_layout = QHBoxLayout(title_row)
        title_row_layout.setContentsMargins(0, 0, 0, 0)  # 여백 제거
        title_row_layout.setSpacing(w(10))  # 구성 요소 사이 간격 설정
        title_row_layout.setAlignment(Qt.AlignVCenter)  # 수직 중앙 정렬

        # 타이틀 레이블 설정
        title_label = QLabel("Upload Data")
        title_font = font_manager.get_just_font("SamsungSharpSans-Bold").family()
        title_label.setStyleSheet(f"font-family: {title_font}; font-size: {f(21)}px; font-weight: 900;")
        title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)  # 수직 중앙, 수평 왼쪽 정렬

        # 버튼 폰트 설정
        button_font = font_manager.get_just_font("SamsungOne-700").family()

        # 버튼 생성 및 스타일 설정
        save_btn = QPushButton("Save")
        save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        save_btn.setFixedSize(w(100), h(40))  # 버튼 크기 고정
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #1428A0; 
                color: white; 
                border: none;
                border-radius: 5px;
                font-family: {button_font};
                font-size: {f(16)}px;
            }}
            QPushButton:hover {{
                background-color: #0069d9;
            }}
            QPushButton:pressed {{
                background-color: #0062cc;
            }}
        """)

        self.run_btn_enabled_style = f"""
            QPushButton {{
                background-color: #1428A0;
                color: white;
                border: none;
                border-radius: 5px;
                font-family: {button_font};
                font-size: {f(16)}px;
            }}
            QPushButton:hover {{
                background-color: #0069d9;
            }}
            QPushButton:pressed {{
                background-color: #0062cc;
            }}
        """
        self.run_btn_disabled_style = f"""
            QPushButton {{
                background-color: #AAAAAA;
                color: #666666;
                border: none;
                border-radius: 5px;
                font-family: {button_font};
                font-size: {f(16)}px;
            }}
        """

        self.run_btn = QPushButton("Run")
        self.run_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.run_btn.setFixedSize(w(100), h(40))  # 버튼 크기 고정
        self.run_btn.setStyleSheet(self.run_btn_enabled_style)

        # 버튼 클릭 이벤트 연결
        self.run_btn.clicked.connect(self.on_run_clicked)
        save_btn.clicked.connect(self.on_save_clicked)

        # 레이아웃에 위젯 추가 (타이틀, 스트레치, 버튼들)
        title_row_layout.addWidget(title_label)
        title_row_layout.addStretch(1)  # 타이틀과 버튼 사이에 신축성 있는 공간 추가
        title_row_layout.addWidget(save_btn)
        title_row_layout.addWidget(self.run_btn)

        # top_container_layout에 title_row 추가
        top_container_layout.addWidget(title_row)

        input_section = QFrame()
        input_section.setFrameShape(QFrame.StyledPanel)
        input_section.setStyleSheet("background-color: white; border-radius: 0px; border: 3px solid #cccccc;")
        input_section.setFixedHeight(h(50))

        input_layout = QHBoxLayout(input_section)
        input_layout.setContentsMargins(w(10), h(5), w(10), h(5))
        input_layout.setSpacing(30)

        self.date_selector = DateRangeSelector()
        self.file_uploader = FileUploadComponent()

        input_layout.addWidget(self.date_selector, 1)
        input_layout.addWidget(self.file_uploader, 3)

        top_container_layout.addWidget(title_row)
        top_container_layout.addWidget(input_section)

        bottom_container = QFrame()
        bottom_container.setStyleSheet("background-color: #F5F5F5;")
        bottom_container_layout = QVBoxLayout(bottom_container)
        bottom_container_layout.setContentsMargins(w(10), h(10), w(10), h(10))

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setHandleWidth(w(5))
        main_splitter.setStyleSheet("QSplitter::handle { background-color: #F5F5F5; }")
        main_splitter.setContentsMargins(0, 0, 0, 0)

        self.file_explorer = FileExplorerSidebar()

        right_area = QFrame()
        right_area.setFrameShape(QFrame.NoFrame)
        right_area.setStyleSheet("background-color: #F5F5F5; border-radius: 0px; border: none;")
        right_layout = QVBoxLayout(right_area)
        right_layout.setContentsMargins(0, 0, 0, 0)

        vertical_splitter = QSplitter(Qt.Vertical)
        vertical_splitter.setHandleWidth(10)
        vertical_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #F5F5F5;
                height: 10px;
            }
        """)

        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)

        self.tab_bar = QTabBar()
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: white; border: 3px solid #cccccc; border-radius: 0px;")

        tab_layout.addWidget(self.tab_bar)
        tab_layout.addWidget(self.stacked_widget)

        maximize_button = QPushButton()
        maximize_button.setIcon(self.style().standardIcon(self.style().SP_TitleBarShadeButton))
        maximize_button.setStyleSheet("border: none; margin-top: 5px;")
        maximize_button.setCursor(QCursor(Qt.PointingHandCursor))
        maximize_button.clicked.connect(self.open_parameter_component) 
        maximize_button.setVisible(False)
        maximize_button.setObjectName("maximize_button")
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(maximize_button)
        tab_layout.addLayout(button_layout)

        parameter_container = QFrame()
        parameter_container.setStyleSheet("background-color: white; padding: 0px; border:none;")
        parameter_container.setContentsMargins(0,0,0,0)

        parameter_layout = QHBoxLayout(parameter_container)
        parameter_layout.setContentsMargins(0,0,0,0)

        parameter_splitter = QSplitter(Qt.Horizontal)
        parameter_splitter.setHandleWidth(10)
        parameter_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #F5F5F5;
            }
        """)

        left_parameter_area = QFrame()
        left_parameter_area.setStyleSheet("background-color: white; border: 3px solid #cccccc;")
        left_parameter_layout = QVBoxLayout(left_parameter_area)
        left_parameter_layout.setContentsMargins(0, 0, 0, 0)

        self.left_parameter_component = LeftParameterComponent()
        left_parameter_layout.addWidget(self.left_parameter_component)
        self.left_parameter_component.setVisible(True)

        right_parameter_area = QFrame()
        right_parameter_area.setStyleSheet("background-color: white; border: 3px solid #cccccc;")
        right_parameter_layout = QVBoxLayout(right_parameter_area)
        right_parameter_layout.setContentsMargins(0, 0, 0, 0)

        self.parameter_component = RightParameterComponent()
        self.parameter_component.close_button_clicked.connect(self.close_parameter_component)
        right_parameter_layout.addWidget(self.parameter_component)

        parameter_splitter.addWidget(left_parameter_area)
        parameter_splitter.addWidget(right_parameter_area)
        
        parameter_splitter.setSizes([600, 400])

        parameter_layout.addWidget(parameter_splitter)

        vertical_splitter.addWidget(tab_container)
        vertical_splitter.addWidget(parameter_container)
        vertical_splitter.setObjectName("vertical_splitter")
        vertical_splitter.setSizes([700, 300])
        vertical_splitter.splitterMoved.connect(self.check_vertical_splitter)

        right_layout.addWidget(vertical_splitter)

        main_splitter.addWidget(self.file_explorer)
        main_splitter.addWidget(right_area)
        main_splitter.setSizes([140, 860])

        bottom_container_layout.addWidget(main_splitter)

        main_container_layout.addWidget(top_container)
        main_container_layout.addWidget(bottom_container, 1)

        layout.addWidget(main_container)

    """
    시그널 연결
    """
    def _connect_signals(self) :
        self.date_selector.date_range_changed.connect(self.on_date_range_changed)

        self.file_uploader.file_selected.connect(self.on_file_selected)
        self.file_uploader.file_removed.connect(self.on_file_removed)

        self.file_selected.connect(self.parameter_component.on_file_selected)

        self.file_explorer.file_or_sheet_selected.connect(
            self.sidebar_manager.on_file_or_sheet_selected)
        
        self.parameter_component.show_failures.connect(self.on_failures_updated)

    """
    날짜 범위가 변경되면 시그널 발생
    """
    def on_date_range_changed(self, start_date, end_date) :
        self.date_range_selected.emit(start_date, end_date)

    """
    파일이 선택되면 시그널 발생 및 사이드바에 추가
    """
    def on_file_selected(self, file_path) :
        self.file_selected.emit(file_path)

        success, message = self.sidebar_manager.add_file_to_sidebar(file_path)
        self.update_status_message(success, message)

        self.register_file_path(file_path)
        if FilePaths.get("demand_excel_file") and FilePaths.get("dynamic_excel_file") and FilePaths.get("master_excel_file"):
            self.run_combined_analysis()

    """
    파일이 삭제되면 사이드바에서도 제거하고 관련된 모든 탭 닫기
    """
    def on_file_removed(self, file_path):
        result = self.sidebar_manager.remove_file_from_sidebar(file_path)

        self.tab_manager.close_file_tabs(file_path)

        file_name = os.path.basename(file_path)
        self.update_status_message(True, f"파일 '{file_name}'이(가) 제거되었습니다")

        # Parameter 영역 완전 정리
        self._clear_parameter_areas()

        # 필수 파일이 모두 있는지 확인 후 분석 재실행
        demand_file = FilePaths.get("demand_excel_file")
        dynamic_file = FilePaths.get("dynamic_excel_file")
        master_file = FilePaths.get("master_excel_file")

        if all([demand_file, dynamic_file, master_file]):
            try:
                self.run_combined_analysis()
            except Exception as e:
                print(f"[분석 재실행] 오류 발생: {e}")

    """파라미터 영역 데이터 정리"""
    def _clear_parameter_areas(self):
        # 좌측 파라미터 영역 정리
        self.left_parameter_component.all_project_analysis_data.clear()
        self.left_parameter_component._initialize_all_tabs()

        # 우측 파라미터 영역 정리
        empty_failures = {
            'production_capacity': None,
            'materials': None,
            'current_shipment': None,
            'preassign': None,
            'plan_retention': None
        }
        self.parameter_component.show_failures.emit(empty_failures)

    """
    Run 버튼 클릭 시 모든 데이터프레임 DataStore에 저장
    """
    def on_run_clicked(self):
        # 필수 파일 확인
        demand_file = FilePaths.get("demand_excel_file")
        dynamic_file = FilePaths.get("dynamic_excel_file")
        master_file = FilePaths.get("master_excel_file")

        if not all([demand_file, dynamic_file, master_file]):
            missing_files = []
            if not demand_file:
                missing_files.append("Demand")
            if not dynamic_file:
                missing_files.append("Dynamic")
            if not master_file:
                missing_files.append("Master")

            QMessageBox.warning(
                self,
                "필수 파일 누락",
                f"다음 파일이 필요합니다: {', '.join(missing_files)}"
            )
            return

        self.tab_manager.save_current_tab_data()

        modified_data = self.data_modifier.get_all_modified_data()

        if modified_data:
            choice = SaveConfirmationDialog.show_dialog(self)

            if choice == "save_and_run":
                self.on_save_clicked()
                self.show_optimization_progress()
            elif choice == "run_without_save":
                self.show_optimization_progress()
            else:
                return
        else:
            self.show_optimization_progress()

    """
    최적화 프로그래스 다이얼로그 표시
    """

    def show_optimization_progress(self):
        # 프로그래스 다이얼로그 생성 (DataInputPage 객체 전달)
        self.progress_dialog = OptimizationProgressDialog(self, self)

        # 최적화 완료 시그널 연결
        self.progress_dialog.optimization_completed.connect(self.on_optimization_completed)
        self.progress_dialog.optimization_cancelled.connect(self.on_optimization_cancelled)

        # 다이얼로그가 닫힐 때 호출되는 함수
        self.progress_dialog.finished.connect(self.on_dialog_finished)

        # 먼저 다이얼로그 표시
        self.progress_dialog.show()

        # UI가 업데이트될 시간을 주기 위해 약간의 지연 후 최적화 시작
        QTimer.singleShot(300, self.progress_dialog.start_optimization)

    """최적화 완료 처리"""
    def on_optimization_completed(self, result):
        if result:
            # 결과 데이터스토어에 저장
            DataStore.set("optimization_result", result)
            # 이미 구현된 방식 그대로 시그널 발생
            self.run_button_clicked.emit()
        else:
            QMessageBox.warning(
                self,
                "최적화 오류",
                "최적화 과정에서 오류가 발생했습니다."
            )
    """
    최적화 취소 처리
    """

    def on_optimization_cancelled(self):
        # 취소 메시지는 이미 프로그래스 다이얼로그에서 표시됨
        pass

    """
    다이얼로그 종료 처리
    """

    def on_dialog_finished(self):
        # 프로그래스 다이얼로그 정리
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.deleteLater()
            self.progress_dialog = None
    """
    최적화를 위한 데이터프레임 준비 및 저장
    """
    def prepare_dataframes_for_optimization(self) :
        all_dataframes = DataStore.get("dataframes", {})

        organized_dataframes = {
            "demand": {},
            "dynamic": {},
            "master": {},
            "etc": {}
        }

        def get_file_type(file_path) :
            file_name = os.path.basename(file_path).lower()
            if "demand" in file_name:
                return "demand"
            elif "dynamic" in file_name:
                return "dynamic"
            elif "master" in file_name:
                return "master"
            else:
                return "etc"

        for key, df in all_dataframes.items() :
            if ":" in key :
                file_path, sheet_name = key.rsplit(":", 1)
                file_type = get_file_type(file_path)
                organized_dataframes[file_type][sheet_name] = df
            else :
                file_type = get_file_type(key)
                file_name = os.path.basename(key).split('.')[0]
                organized_dataframes[file_type][file_name] = df

        DataStore.set("organized_dataframes", organized_dataframes)

    """
    상태 메시지 업데이트
    """
    def update_status_message(self, success, message):
        if success:
            print(f"성공: {message}")
        else:
            print(f"오류: {message}")

    """
    선택된 파일 경로 리스트 반환
    """
    def get_file_paths(self):
        return self.file_uploader.get_file_paths()

    """
    파일 경로를 FilePaths에 등록
    """
    def register_file_path(self, file_path):
        fn = os.path.basename(file_path).lower()
        if "demand" in fn:
            FilePaths.set("demand_excel_file", file_path)
        elif "dynamic" in fn:
            FilePaths.set("dynamic_excel_file", file_path)
        elif "master" in fn:
            FilePaths.set("master_excel_file", file_path)
        elif "result" in fn:
            FilePaths.set("result_file", file_path)
        elif "pre_assign" in fn:
            FilePaths.set("pre_assign_excel_file", file_path)
        else:
            FilePaths.set("etc_excel_file", file_path)

    """
    파일 분석 실행
    """
    def run_combined_analysis(self) :
        failures = {}  
        pre_failures = run_allocation()
        print(pre_failures)
        if pre_failures:
            failures.update(pre_failures)

        item_plan_retention, rmc_plan_retention,df_result = calc_plan_retention()
        if item_plan_retention is not None:
            sku1 = SettingsStore.get('op_SKU_1',0)
            rmc1 = SettingsStore.get('op_RMC_1',0)
            sku2 = SettingsStore.get('op_SKU_2',0)
            rmc2 = SettingsStore.get('op_RMC_2',0)
            plan_retention_errors = []
            if item_plan_retention < sku1:
                plan_retention_errors.append({'reason':f'The selected sku1 plan retention ratio {sku1}% is greater than the maximum {item_plan_retention:.1f}%.'})
            if item_plan_retention < sku2:
                plan_retention_errors.append({'reason':f'The selected sku2 plan retention ratio {sku2}% is greater than the maximum {item_plan_retention:.1f}%.'})
            if rmc_plan_retention < rmc1:
                plan_retention_errors.append({'reason':f'The selected rmc1 plan retention ratio {rmc1}% is greater than the maximum {rmc_plan_retention:.1f}%.'})
            if rmc_plan_retention < rmc2:
                plan_retention_errors.append({'reason':f'The selected rmc2 plan retention ratio {rmc2}% is greater than the maximum {rmc_plan_retention:.1f}%.'})
            failures['plan_retention'] = plan_retention_errors
            summary = {
                'Maximum SKU Plan Retention Rate':item_plan_retention,
                'Maximum RMC Plan Retention Rate':rmc_plan_retention,
            }
            current_data = self.left_parameter_component.all_project_analysis_data.copy()
            display_df = df_result
            current_data['Plan Retention'] = {
                'display_df' : display_df,
                'summary' : summary
            }
            self.left_parameter_component.set_project_analysis_data(current_data)

        try :
            shipment_data = preprocess_data_for_fulfillment_rate()

            if shipment_data :
                fulfillment_result = calculate_fulfillment_rate(shipment_data)

                if fulfillment_result :
                    summary = {
                        'Total demand(SOP)': fulfillment_result['total_sop'],
                        'Total production': fulfillment_result['total_production'],
                        'Overall fulfillment rate': f"{fulfillment_result['overall_rate']:.2f}%",
                        'Project count': len(fulfillment_result['project_fulfillment']),
                        'Site count': len(fulfillment_result['site_fulfillment']),
                        'Bottleneck items': len([r for _, r in fulfillment_result['detailed_results'].iterrows() 
                                                if not r['Is_Fulfilled'] and r['SOP'] > 0])
                    }

                    display_df = pd.DataFrame()

                    project_rows = []

                    for project, data in fulfillment_result['project_fulfillment'].items() :
                        project_rows.append({
                            'Category': 'Project',
                            'Name': project,
                            'SOP': data['sop'],
                            'Production': data['production'],
                            'Fulfillment Rate': f"{data['rate']:.2f}%",
                            'Status': 'OK' if data['rate'] >= 95 else 'Warning' if data['rate'] >= 80 else 'Error'
                        })
                    project_rows = sorted(project_rows,key=lambda x:x['SOP'],reverse=True)

                    site_rows = []

                    for site, data in fulfillment_result['site_fulfillment'].items() :
                        site_rows.append({
                            'Category': 'Site',
                            'Name': site,
                            'SOP': data['sop'],
                            'Production': data['production'],
                            'Fulfillment Rate': f"{data['rate']:.2f}%",
                            'Status': 'OK' if data['rate'] >= 95 else 'Warning' if data['rate'] >= 80 else 'Error'
                        })
                    site_rows = sorted(site_rows,key=lambda x:x['SOP'], reverse=True)

                    total_row = {
                        'Category': 'Total',
                        'Name': 'Overall',
                        'SOP': fulfillment_result['total_sop'],
                        'Production': fulfillment_result['total_production'],
                        'Fulfillment Rate': f"{fulfillment_result['overall_rate']:.2f}%",
                        'Status': 'OK' if fulfillment_result['overall_rate'] >= 95 else 'Warning' if fulfillment_result['overall_rate'] >= 80 else 'Error'
                    }

                    display_df = pd.DataFrame(project_rows + site_rows + [total_row])

                    current_data = self.left_parameter_component.all_project_analysis_data.copy()
                    current_data['Current Shipment'] = {
                        'display_df' : display_df,
                        'summary' : summary
                    }

                    self.left_parameter_component.set_project_analysis_data(current_data)

                    if fulfillment_result['overall_rate'] < 70 :
                        shipment_failures = []

                        unfulfilled_items = fulfillment_result['detailed_results'][
                            (fulfillment_result['detailed_results']['Is_Fulfilled'] == False) &
                            (fulfillment_result['detailed_results']['SOP'] > 0)
                        ]

                        for _, row in unfulfilled_items.iterrows() :
                            shipment_failures.append({
                                'item': row.get('Item', 'Unknown'),
                                'project': row.get('Project', ''),
                                'tosite': row.get('Tosite_group', ''),
                                'reason': row.get('Constraint_Type', 'Unknown'),
                                'sop': row.get('SOP', 0),
                                'production': row.get('Production_Qty', 0),
                                'shortage': row.get('SOP', 0) - row.get('Production_Qty', 0)
                            })

                        failures['shipment'] = shipment_failures
        except Exception as e :
            print(f'shipment analysis failed : {str(e)}')

        try :
            material_analyzer = MaterialAnalyzer()

            if material_analyzer.analyze() :
                materials_display_data = self.format_material_analysis_results(material_analyzer)

                project_data = self.left_parameter_component.all_project_analysis_data.copy()
                project_data['Materials'] = materials_display_data
                self.left_parameter_component.set_project_analysis_data(project_data)

                if material_analyzer.weekly_shortage_materials is not None and not material_analyzer.weekly_shortage_materials.empty :
                    material_failures = []

                    for _, row in material_analyzer.weekly_shortage_materials.iterrows() :
                        try :
                            material_failures.append({
                                'material_id' : row.get('Material', 'Unknown'),
                                'line' : '',
                                'reason' : 'Material shortage',
                                'available' : row.get('On-Hand', 0),
                                'excess' : row.get('Weekly_Shortage', 0)
                            })
                        except Exception as e :
                            continue

                    # failures['materials'] = material_failures

                if material_analyzer.material_df is not None and not material_analyzer.material_df.empty :
                    negative_stock_materials = {}

                    current_negative = material_analyzer.material_df[material_analyzer.material_df['On-Hand'] < 0].copy()

                    if not current_negative.empty :
                        current_materials = []

                        for _, row in current_negative.iterrows() :
                            material_id = row.get('Material', 'Unknown')
                            stock = row.get('On-Hand', 0)
                            current_materials.append({
                                'material_id': material_id,
                                'stock': stock
                            })
                        negative_stock_materials['Current'] = current_materials
                    # if negative_stock_materials :
                    #     failures['materials_negative_stock'] = negative_stock_materials
            else :
                print('failed material analysis')
        except Exception as e :
            print(f'Error : {str(e)}')

        try :
            processed_data = process_data()

            if processed_data :
                pjt_analyzer = PjtGroupAnalyzer(processed_data)
                project_analysis_results = pjt_analyzer.analyze()

                if project_analysis_results and 'display_df' in project_analysis_results :
                    current_data = self.left_parameter_component.all_project_analysis_data.copy()
                    current_data['Production Capacity'] = project_analysis_results
                    self.left_parameter_component.set_project_analysis_data(current_data)

                    display_df = project_analysis_results['display_df']
                    has_issues = False

                    if display_df is not None :
                        for _, row in display_df.iterrows() :
                            if row.get('PJT') == 'Total' and row.get('status') == 'Error' :
                                has_issues = True
                                break

                        if has_issues :
                            issues = []

                            for _, row in display_df.iterrows() :
                                if row.get('PJT') == 'Total' and row.get('status') == 'Error' :
                                    issues.append({
                                        'line': row.get('PJT Group', ''),
                                        'reason': 'capacity exceeded',
                                        'available': row.get('CAPA', 0),
                                        'excess': self.extract_number(row.get('MFG', 0)) - self.extract_number(row.get('CAPA, 0')) if row.get('MFG') and row.get('CAPA') else 0,
                                        'cap_limit': row.get('CAPA', 0),
                                        'center': row.get('PJT Group', '').split('_')[0] if isinstance(row.get('PJT Group', ''), str) and '_' in row.get('PJT Group', '') else ''
                                    })
                            failures['production_capacity'] = issues if issues else None
                        else :
                            failures['production_capacity'] = None
        except Exception as e :
            print(f'Error : {str(e)}')

            if has_issues :
                issues = []

                for _, row in display_df.iterrows() :
                    if row.get('PJT') == 'Total' and row.get('status') == 'Error' :
                        issues.append({
                            'line': row.get('PJT Group', ''),
                            'reason': 'Capacity exceeded',
                            'available': row.get('CAPA', 0),
                            'excess': self.extract_number(row.get('MFG', 0)) - self.extract_number(row.get('CAPA, 0')) if row.get('MFG') and row.get('CAPA') else 0,
                            'cap_limit': row.get('CAPA', 0),
                            'center': row.get('PJT Group', '').split('_')[0] if isinstance(row.get('PJT Group', ''), str) and '_' in row.get('PJT Group', '') else ''
                        })
                failures['production_capacity'] = issues if issues else None
                self.parameter_component.set_project_analysis_data(project_analysis_results)
            else :
                failures['production_capacity'] = None
        except Exception as e :
            print(f'error : {str(e)}')

        self.parameter_component.show_failures.emit(failures)

    """
    Save 버튼 클릭 시 현재 데이터를 원본 파일에 저장
    """
    def on_save_clicked(self):
        self.tab_manager.save_current_tab_data()

        modified_data = self.data_modifier.get_all_modified_data()

        if not modified_data:
            QMessageBox.information(self, 'Save Notice', 'No changes to save')
            return

        success_count = 0
        error_count = 0

        for file_path, sheets in modified_data.items():
            file_ext = os.path.splitext(file_path)[1].lower()

            try:
                if file_ext == '.csv':
                    if 'data' in sheets:
                        df = sheets['data']
                        df.to_csv(file_path, index=False, encoding='utf-8')
                        success_count += 1
                elif file_ext in ['.xls', '.xlsx']:
                    with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                        for sheet_name, df in sheets.items():
                            if sheet_name != 'data':
                                df.to_excel(writer, sheet_name=sheet_name, index=False)
                    success_count += 1
            except Exception as e:
                print(f"Error saving file '{file_path}' : {str(e)}")
                error_count += 1

        if success_count > 0:
            self.data_modifier.modified_data_dict.clear()

            for (file_path, sheet_name), idx in self.tab_manager.open_tabs.items():
                self.data_modifier.remove_modified_status_in_sidebar(file_path, sheet_name)
                self.tab_manager.update_tab_title(file_path, sheet_name, False)
            
            self.run_combined_analysis()

        if error_count == 0:
            message = f"Successfully saved {success_count} file(s)"
            QMessageBox.information(self, 'Save Success', message)
            self.update_status_message(True, message)
        else:
            message = f"Saved {success_count} file(s), Failed to save {error_count} file(s)"
            QMessageBox.warning(self, 'Save Notice', message)
            self.update_status_message(False, message)

    """
    문자열에서 숫자 추출 후 정수 변환
    """
    def extract_number(self, value) :
        if isinstance(value, (int, float)) :
            return int(value)
        elif isinstance(value, str) :
            num_str = re.sub(r'[^\d]', '', value.split()[0])
            
            return int(num_str) if num_str else 0
        return 0
    
    """
    자재 분석 결과 형식 변환
    """
    def format_material_analysis_results(self, material_analyzer) :
        try :
            if material_analyzer.weekly_shortage_materials is None :
                return None
            
            df = material_analyzer.weekly_shortage_materials.copy()

            if df.empty :
                return None
            
            display_columns = ['Material', 'Active_OX', 'On-Hand', 'Weekly_Shortage', 'Shortage_Rate']
            available_columns = [col for col in display_columns if col in df.columns]

            shortage_df = df[df['Weekly_Shortage'] > 0][available_columns].copy() if 'Weekly_Shortage' in df.columns else df

            if shortage_df.empty :
                return None
            
            column_mapping = {
                'Material': 'Material ID',
                'Active_OX': 'Active',
                'On-Hand': 'Current Stock',
                'Weekly_Shortage': 'Shortage Amount',
                'Shortage_Rate': 'Shortage Rate (%)'
            }

            change_columns = {}

            for col in available_columns :
                if col in column_mapping :
                    change_columns[col] = column_mapping[col]

            display_df = shortage_df.rename(columns = change_columns)

            weekly_count = len(shortage_df)
            full_period_count = len(material_analyzer.full_period_shortage_materials) if material_analyzer.full_period_shortage_materials is not None else 0
            total_materials = len(material_analyzer.material_df) if material_analyzer.material_df is not None else 0
            shortage_rate = (weekly_count / total_materials * 100) if total_materials > 0 else 0

            top_materials = []

            if not shortage_df.empty and 'Weekly_Shortage' in shortage_df.columns :
                try :
                    top_df = shortage_df.sort_values(by='Weekly_Shortage', ascending=False).head(5)

                    for _, row in top_df.iterrows() :
                        material_id = row.get('Material', 'Unknown')
                        shortage = row.get('Weekly_Shortage', 0)
                        top_materials.append(f'{material_id} : {int(shortage)}')
                except Exception as e :
                    print(f'Error getting top materials : {str(e)}')

            summary = {
                'Total materials': total_materials,
                'Weekly shortage materials': weekly_count,
                'Full period shortage materials': full_period_count,
                'Shortage rate (%)': round(shortage_rate, 2),
                'Period': '4/7-4/13 (weekly), 4/7-4/20 (full)',
                'Top shortage materials': ", ".join(top_materials[:3]) if top_materials else "None"
            }

            return {
                'display_df': display_df,
                'summary': summary
            }
        except Exception as e :
            return None
    
    def check_vertical_splitter(self):
        vertical_splitter = self.findChild(QSplitter,"vertical_splitter")
        sizes = vertical_splitter.sizes()
        maximize_button = self.findChild(QPushButton,"maximize_button")
        if sizes[1] == 0:
            maximize_button.setVisible(True)
        else:
            maximize_button.setVisible(False)
    
    def open_parameter_component(self):
        vertical_splitter = self.findChild(QSplitter,"vertical_splitter")
        if vertical_splitter:
            vertical_splitter.setSizes([700,300])
        self.check_vertical_splitter()

    def close_parameter_component(self):
        vertical_splitter = self.findChild(QSplitter,"vertical_splitter")
        if vertical_splitter:
            vertical_splitter.setSizes([1,0])
        self.check_vertical_splitter()
    
    """failures에 데이터가 있으면 버튼 비활성화"""
    def on_failures_updated(self, failures: dict):
        has_any = any(
            v not in (None, [], {}, '')
            for v in failures.values()
        )
        self.run_btn.setEnabled(not has_any)
        if has_any:
            self.run_btn.setStyleSheet(self.run_btn_disabled_style)
        else:
            self.run_btn.setStyleSheet(self.run_btn_enabled_style)