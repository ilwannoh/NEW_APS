"""
메인 윈도우
APS 생산계획 시스템의 메인 화면
"""
from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                           QHBoxLayout, QAction, QMenuBar, QMessageBox,
                           QFileDialog, QPushButton, QLabel)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap

from app.resources.styles.app_style import AppStyle
from app.resources.styles.screen_manager import w, h, f
from app.models.master_data import MasterDataManager
from app.models.production_plan import ProductionPlan
from app.core.scheduler import APSScheduler
from app.utils.file_handler import FileHandler

# 뷰 임포트 (추후 구현)
# from app.views.master_data_view import MasterDataView
# from app.views.schedule_view import ScheduleView 
# from app.views.result_view import ResultView


class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""
    
    # 시그널
    file_loaded = pyqtSignal(str)  # 파일 로드 완료
    schedule_generated = pyqtSignal()  # 스케줄 생성 완료
    
    def __init__(self):
        super().__init__()
        self.master_data = MasterDataManager()
        self.scheduler = APSScheduler(self.master_data)
        self.current_plan = None
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("APS 생산계획 시스템")
        self.setStyleSheet(AppStyle.get_stylesheet())
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 메뉴바 설정
        self.create_menu_bar()
        
        # 툴바 영역
        toolbar_widget = self.create_toolbar()
        main_layout.addWidget(toolbar_widget)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                background-color: #ffffff;
                border: none;
                border-top: 1px solid #e9ecef;
            }}
            
            QTabBar::tab {{
                min-width: {w(120)}px;
                padding: {h(8)}px {w(16)}px;
                font-size: {f(13)}px;
            }}
        """)
        
        # 탭 추가 (임시 위젯)
        self.master_data_tab = QWidget()
        self.setup_master_data_tab()
        self.tab_widget.addTab(self.master_data_tab, "마스터 설정")
        
        self.schedule_tab = QWidget()
        self.setup_schedule_tab()
        self.tab_widget.addTab(self.schedule_tab, "스케줄 생성")
        
        self.result_tab = QWidget()
        self.setup_result_tab()
        self.tab_widget.addTab(self.result_tab, "스케줄 편집")
        
        main_layout.addWidget(self.tab_widget)
        
        # 상태바
        self.statusBar().showMessage("준비")
        
        # 윈도우 크기 설정
        self.resize(w(1920), h(1080))
        QTimer.singleShot(100, self.showMaximized)
    
    def create_menu_bar(self):
        """메뉴바 생성"""
        menubar = self.menuBar()
        
        # 파일 메뉴
        file_menu = menubar.addMenu("파일")
        
        open_action = QAction("판매계획 열기...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_sales_plan)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("결과 내보내기...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_results)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("종료", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 도구 메뉴
        tools_menu = menubar.addMenu("도구")
        
        sample_action = QAction("샘플 파일 생성", self)
        sample_action.triggered.connect(self.create_sample_files)
        tools_menu.addAction(sample_action)
        
        # 도움말 메뉴
        help_menu = menubar.addMenu("도움말")
        
        about_action = QAction("정보", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """툴바 생성"""
        toolbar_widget = QWidget()
        toolbar_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-bottom: 1px solid #e9ecef;
            }
        """)
        
        layout = QHBoxLayout(toolbar_widget)
        layout.setContentsMargins(w(16), h(8), w(16), h(8))
        
        # 로고/타이틀
        title_label = QLabel("APS 생산계획 시스템")
        title_label.setStyleSheet(f"""
            font-size: {f(18)}px;
            font-weight: bold;
            color: #1428A0;
        """)
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # 주요 액션 버튼들
        load_btn = QPushButton("📁 판매계획 로드")
        load_btn.clicked.connect(self.open_sales_plan)
        layout.addWidget(load_btn)
        
        generate_btn = QPushButton("⚙️ 스케줄 생성")
        generate_btn.clicked.connect(self.generate_schedule)
        layout.addWidget(generate_btn)
        
        export_btn = QPushButton("💾 결과 내보내기")
        export_btn.clicked.connect(self.export_results)
        layout.addWidget(export_btn)
        
        return toolbar_widget
    
    def setup_master_data_tab(self):
        """마스터 데이터 탭 설정 (임시)"""
        layout = QVBoxLayout(self.master_data_tab)
        
        # 헤더
        header = QLabel("마스터 데이터 관리")
        header.setProperty("class", "heading")
        layout.addWidget(header)
        
        info_label = QLabel(
            "제품, 공정, 장비, 작업자 정보를 설정합니다.\n"
            "각 항목을 추가, 수정, 삭제할 수 있습니다."
        )
        layout.addWidget(info_label)
        
        layout.addStretch()
    
    def setup_schedule_tab(self):
        """스케줄 생성 탭 설정 (임시)"""
        layout = QVBoxLayout(self.schedule_tab)
        
        # 헤더
        header = QLabel("생산 스케줄 생성")
        header.setProperty("class", "heading")
        layout.addWidget(header)
        
        info_label = QLabel(
            "판매계획을 업로드하고 '스케줄 생성' 버튼을 클릭하면\n"
            "자동으로 최적화된 생산계획이 생성됩니다."
        )
        layout.addWidget(info_label)
        
        layout.addStretch()
    
    def setup_result_tab(self):
        """결과 탭 설정 (임시)"""
        layout = QVBoxLayout(self.result_tab)
        
        # 헤더
        header = QLabel("생산 스케줄 편집")
        header.setProperty("class", "heading")
        layout.addWidget(header)
        
        info_label = QLabel(
            "생성된 스케줄을 그리드 뷰에서 확인하고\n"
            "드래그&드롭으로 수정할 수 있습니다."
        )
        layout.addWidget(info_label)
        
        layout.addStretch()
    
    def open_sales_plan(self):
        """판매계획 파일 열기"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "판매계획 파일 선택",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if file_path:
            try:
                # 파일 유효성 검사
                if FileHandler.validate_sales_plan(file_path):
                    self.current_sales_plan_path = file_path
                    self.statusBar().showMessage(f"판매계획 로드됨: {file_path}")
                    self.file_loaded.emit(file_path)
                else:
                    QMessageBox.warning(
                        self,
                        "잘못된 파일 형식",
                        "판매계획 파일 형식이 올바르지 않습니다.\n"
                        "필수 컬럼: 제품명, 1월~12월"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "파일 로드 오류",
                    f"파일을 읽을 수 없습니다:\n{str(e)}"
                )
    
    def generate_schedule(self):
        """스케줄 생성"""
        if not hasattr(self, 'current_sales_plan_path'):
            QMessageBox.warning(
                self,
                "파일 없음",
                "먼저 판매계획 파일을 로드해주세요."
            )
            return
        
        try:
            # 판매계획 읽기
            sales_df = FileHandler.read_excel(self.current_sales_plan_path)
            
            # 스케줄 생성
            from datetime import datetime
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            self.current_plan = self.scheduler.schedule_from_sales_plan(sales_df, start_date)
            
            # 세척 블록 추가
            self.scheduler.add_cleaning_blocks()
            
            self.statusBar().showMessage("스케줄 생성 완료")
            self.schedule_generated.emit()
            
            # 결과 탭으로 이동
            self.tab_widget.setCurrentIndex(2)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "스케줄 생성 오류",
                f"스케줄 생성 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    def export_results(self):
        """결과 내보내기"""
        if not self.current_plan:
            QMessageBox.warning(
                self,
                "결과 없음",
                "내보낼 스케줄이 없습니다.\n먼저 스케줄을 생성해주세요."
            )
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "결과 저장",
            "production_schedule.csv",
            "CSV Files (*.csv);;Excel Files (*.xlsx);;XML Files (*.xml)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.current_plan.export_to_csv(file_path)
                elif file_path.endswith('.xlsx'):
                    df = self.current_plan.to_dataframe()
                    FileHandler.write_excel(df, file_path, "생산계획")
                elif file_path.endswith('.xml'):
                    self.current_plan.export_to_xml(file_path)
                
                QMessageBox.information(
                    self,
                    "저장 완료",
                    f"결과가 저장되었습니다:\n{file_path}"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "저장 오류",
                    f"파일 저장 중 오류가 발생했습니다:\n{str(e)}"
                )
    
    def create_sample_files(self):
        """샘플 파일 생성"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "샘플 파일 저장 위치 선택"
        )
        
        if dir_path:
            try:
                FileHandler.create_sample_files(dir_path)
                QMessageBox.information(
                    self,
                    "샘플 생성 완료",
                    f"샘플 파일이 생성되었습니다:\n{dir_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "샘플 생성 오류",
                    f"샘플 파일 생성 중 오류가 발생했습니다:\n{str(e)}"
                )
    
    def show_about(self):
        """프로그램 정보 표시"""
        QMessageBox.about(
            self,
            "APS 생산계획 시스템",
            "APS Production Planning System v1.0.0\n\n"
            "판매계획을 기반으로 최적화된 생산계획을 생성하고\n"
            "시각적으로 편집할 수 있는 시스템입니다.\n\n"
            "© 2025 APS Development Team"
        )