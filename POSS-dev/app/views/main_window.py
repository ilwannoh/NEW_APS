from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCursor
import os
from app.core.optimization import Optimization
from app.views.components import Navbar, DataInputPage, PlanningPage, ResultPage
from app.views.models.data_model import DataModel
from app.models.common.file_store import FilePaths
from app.models.common.file_store import DataStore
from app.views.components.help_dialogs.help_dialog import HelpDialog
from app.views.components.settings_dialogs.settings_dialog import SettingsDialog
from app.utils.error_handler import (
    error_handler, safe_operation,
    DataError, FileError, ValidationError, CalculationError
)
from app.resources.fonts.font_manager import font_manager
from app.models.common.screen_manager import *

class MainWindow(QMainWindow):

    @error_handler(
        show_dialog=True,
        default_return=None
    )
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Samsung Production Planning Optimization System")
        # self.setFixedSize(1920, 1080)

        # Create a smaller icon
        # app_icon = QIcon('../resources/icon/samsung_icon1.png')
        # # Create a scaled version of the icon (adjust size as needed)
        # scaled_pixmap = app_icon.pixmap(16, 16)  # Small 16x16 icon
        # scaled_icon = QIcon(scaled_pixmap)
        # self.setWindowIcon(scaled_icon)

        self.data_model = DataModel()

        self.init_ui()
        QTimer.singleShot(100, self.showMaximized)

    @error_handler(
        show_dialog=True,
        default_return=None
    )
    def init_ui(self):
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #F5F5F5; border:none;")
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.navbar = Navbar()
        self.navbar.help_clicked.connect(self.show_help)
        self.navbar.settings_clicked.connect(self.show_settings)
        main_layout.addWidget(self.navbar)

        self.tab_widget = QTabWidget()
        self.tab_widget.tabBar().setCursor(QCursor(Qt.PointingHandCursor))
        self.tab_widget.setStyleSheet(f"""      
                    QTabWidget::pane {{
                        background-color: #ffffff;
                        border: none;
                        border-top: 1px solid #e9ecef;
                        border-radius: 0px;
                    }}

                    QTabBar {{
                        background-color: #f8f9fa;
                        border: none;
                        border-radius: 0px;
                    }}

                    QTabBar::tab {{
                        background: transparent;
                        color: #666;
                        padding: {w(8)}px {w(12)}px;
                        font-family: {font_manager.get_just_font("SamsungOne-700").family()};
                        font-size: {f(13)}px;
                        font-weight: 600;
                        border-bottom: 3px solid transparent;
                        margin-right: 0px;
                        min-width: 10px;
                    }}

                    QTabBar::tab:hover {{
                        color: #1428A0;
                        background: rgba(20, 40, 160, 0.05);
                    }}

                    QTabBar::tab:selected {{
                        color: #1428A0;
                        font-weight: 700;
                        border-bottom: 3px solid #1428A0;
                        background: rgba(20, 40, 160, 0.05);
                    }}
                """)

        self.data_input_page = DataInputPage()
        self.data_input_page.file_selected.connect(self.on_file_selected)
        self.data_input_page.date_range_selected.connect(self.on_date_range_selected)
        self.data_input_page.run_button_clicked.connect(self.on_run_button_clicked)

        self.planning_page = PlanningPage(self)
        # 시그널이 정의되지 않았으므로 연결 제거 또는 시그널 추가 필요

        self.result_page = ResultPage(self)
        # 시그널이 정의되지 않았으므로 연결 제거 또는 시그널 추가 필요

        self.tab_widget.addTab(self.data_input_page, "Data Input")
        self.tab_widget.addTab(self.planning_page, "Pre-Assigned Result")
        self.tab_widget.addTab(self.result_page, "Results")

        main_layout.addWidget(self.tab_widget)
        self.setCentralWidget(central_widget)

    """
    특정 인덱스의 탭으로 이동
    """
    @error_handler(
        show_dialog=False,
        default_return=None
    )
    def navigate_to_page(self, index):
        if 0 <= index < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(index)
        else :
            raise ValidationError(f'Invalid tab index : {index}')

    """ 
    도움말 표시 실행 함수
    """
    @error_handler(
        show_dialog=True,
        default_return=None
    )
    def show_help(self):
        hel_dialog = HelpDialog(self)
        hel_dialog.exec_()

    """
    설정 창 표시
    """
    @error_handler(
        show_dialog=True,
        default_return=None
    )
    def show_settings(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.settings_changed.connect(self.on_settings_changed)

        result = settings_dialog.exec_()

        if result == settings_dialog.Accepted:
            print("설정이 저장되었습니다.")
        else:
            print("설정이 취소되었습니다.")

    """
    설정 변경 시 호출되는 콜백
    """
    @error_handler(
        show_dialog=False,
        default_return=None
    )
    def on_settings_changed(self, settings):
        # try:
            # DataModel에 update_settings 메서드가 없으므로 주석 처리하거나 제거
            # self.data_model.update_settings(settings)

            # 대신 필요한 처리를 여기에 구현
            # 예: 설정 변경 사항을 로그로 남김
        #     print("Settings have been changed:", settings)
        #
        #     # 사용자에게 알림
        #     QMessageBox.information(self, "Change Settings", "Settings have been saved.")
        # except Exception as e:
        #     print(f"Error applying settings: {e}")
        pass
    
    """
    파일 경로 중앙 관리를 위한 함수
    """
    @error_handler(
        show_dialog=True,
        default_return=None
    )
    def on_file_selected(self, file_path):
        if not file_path or not os.path.exists(file_path) :
            raise FileError(f'Invalid file path : {file_path}')

        file_name = os.path.basename(file_path)
        self.data_model.set_file_path(file_path)

        if "demand" in file_name:
            FilePaths.set("demand_excel_file", file_path)
        elif "dynamic" in file_name:
            FilePaths.set("dynamic_excel_file", file_path)
        elif "master" in file_name:
            FilePaths.set("master_excel_file", file_path)
        else:
            FilePaths.set("etc_excel_file", file_path)

    """
    날짜 범위가 선택되면 처리
    """
    @error_handler(
        show_dialog=False,
        default_return=None
    )
    def on_date_range_selected(self, start_date, end_date):
        if start_date > end_date :
            raise ValidationError('Start date cannot be later than end date')

        self.data_model.set_date_range(start_date, end_date)

        # FilePaths에 날짜 정보 저장 (필요한 경우)
        # start_date_str = start_date.toString('yyyy-MM-dd')
        # end_date_str = end_date.toString('yyyy-MM-dd')
        # FilePaths.set("start_date", start_date_str)
        # FilePaths.set("end_date", end_date_str)

    """
    Run 버튼이 클릭되면 DataStore에서 데이터프레임 가져와 사용
    """
    @error_handler(
        show_dialog=True,
        default_return=None
    )
    @error_handler(
        show_dialog=True,
        default_return=None
    )
    def on_run_button_clicked(self):
        """Run 버튼이 클릭되면 DataStore에서 데이터프레임 가져와 사용"""
        # 먼저 DataStore에서 이미 최적화된 결과가 있는지 확인
        optimization_result = DataStore.get("optimization_result")

        if optimization_result and 'result' in optimization_result:
            # 이미 계산된 결과가 있으면 그것을 사용
            df = optimization_result['result']
            self.planning_page.display_preassign_result(df)
            self.navigate_to_page(1)
            # 사용 후 결과 삭제 (중복 처리 방지)
            DataStore.set("optimization_result", None)
            return

        # 아래는 기존 코드: 저장된 최적화 결과가 없을 경우에만 실행
        demand_file = FilePaths.get("demand_excel_file")
        dynamic_file = FilePaths.get("dynamic_excel_file")
        master_file = FilePaths.get("master_excel_file")

        if not all([demand_file, dynamic_file, master_file]):
            raise FileError('Required files are missing', {
                "demand_file": bool(demand_file),
                "dynamic_file": bool(dynamic_file),
                "master_file": bool(master_file)
            })

        all_dataframes = DataStore.get("organized_dataframes", {})

        if not all_dataframes:
            raise DataError('No dataframes available for optimization')

        try:
            optimization = Optimization(all_dataframes)

            if hasattr(optimization, 'set_data') and callable(getattr(optimization, 'set_data')):
                optimization.set_data(all_dataframes)
            else:
                print("최적화 엔진에 set_data 메소드가 없습니다. 기존 방식으로 진행합니다.")
        except Exception as e:
            raise CalculationError(f'Error initializing optimization engine : {str(e)}')

        result_dict = safe_operation(
            optimization.pre_assign,
            'Error during pre-assignment optimization'
        )

        if not result_dict or 'result' not in result_dict:
            raise CalculationError('Pre-assignment optimization failed or returned invalid results')

        df = result_dict['result']

        self.planning_page.display_preassign_result(df)
        self.navigate_to_page(1)

    """
    결과 내보내기 로직
    """
    @error_handler(
        show_dialog=True,
        default_return=None
    )
    def export_results(self, file_path=None):
        if not file_path :
            raise FileError('No file path provided for export')

        print(f"결과를 다음 경로에 저장: {file_path}")
        # self.data_model.export_results(file_path)

    """
    최적화 결과 처리
    """
    @error_handler(
        show_dialog=True,
        default_return=None
    )
    def handle_optimization_result(self, results):
        print("main_window : handle_optimization_result 호출")
        # Args:
        #     results (dict): 최적화 결과를 포함하는 딕셔너리

        if not results or not isinstance(results, dict) :
            print("main_window : raise ValidationError('Invalid optimization results')")
            raise ValidationError('Invalid optimization results')

        if not hasattr(self, 'result_page'):
            print("main_window : self.central_widget.addWidget(self.result_page)")
            self.result_page = ResultPage(self)
            self.central_widget.addWidget(self.result_page)

        if 'assignment_result' in results and results['assignment_result'] is not None:
            print("main_window : self.central_widget.addWidget(self.result_page)")
            self.result_page.set_optimization_result(results)
        else :
            print('No assignment results available')

        self.central_widget.setCurrentWidget(self.result_page)