"""
업데이트된 메인 윈도우
모든 기능이 작동하는 통합 UI
"""
from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                           QHBoxLayout, QAction, QMenuBar, QMessageBox,
                           QFileDialog, QPushButton, QLabel, QProgressDialog,
                           QSplitter, QTextEdit, QGroupBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap

from app.resources.styles.app_style import AppStyle
from app.resources.styles.screen_manager import w, h, f
from app.controllers.main_controller import MainController
from app.views.master_data_view import MasterDataView
from app.views.schedule_grid_view import ScheduleGridView
from app.utils.file_handler import FileHandler
from app.models.production_plan import ProductionPlan


class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""
    
    def __init__(self):
        super().__init__()
        self.controller = MainController()
        self.init_ui()
        self.connect_signals()
        
        # 샘플 작업자 데이터 추가
        self.controller.add_sample_operator_data()
        
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
        
        # 1. 마스터 데이터 탭
        self.master_data_view = MasterDataView(self.controller.master_data)
        self.tab_widget.addTab(self.master_data_view, "① 마스터 설정")
        
        # 2. 스케줄 생성 탭
        self.schedule_create_tab = self.create_schedule_tab()
        self.tab_widget.addTab(self.schedule_create_tab, "② 스케줄 생성")
        
        # 3. 스케줄 편집 탭
        self.schedule_edit_tab = self.create_edit_tab()
        self.tab_widget.addTab(self.schedule_edit_tab, "③ 스케줄 편집")
        
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
        
        # 내보내기 서브메뉴
        export_menu = file_menu.addMenu("내보내기")
        
        export_csv_action = QAction("CSV로 내보내기...", self)
        export_csv_action.triggered.connect(lambda: self.export_results('csv'))
        export_menu.addAction(export_csv_action)
        
        export_excel_action = QAction("Excel로 내보내기...", self)
        export_excel_action.triggered.connect(lambda: self.export_results('xlsx'))
        export_menu.addAction(export_excel_action)
        
        export_grid_action = QAction("그리드뷰로 내보내기...", self)
        export_grid_action.triggered.connect(lambda: self.export_results('grid'))
        export_menu.addAction(export_grid_action)
        
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
        
        # 현재 파일 표시
        self.current_file_label = QLabel("판매계획: 없음")
        self.current_file_label.setStyleSheet(f"color: #666; font-size: {f(12)}px;")
        layout.addWidget(self.current_file_label)
        
        layout.addWidget(QLabel(" | "))
        
        # 스케줄 상태 표시
        self.schedule_status_label = QLabel("스케줄: 미생성")
        self.schedule_status_label.setStyleSheet(f"color: #666; font-size: {f(12)}px;")
        layout.addWidget(self.schedule_status_label)
        
        return toolbar_widget
    
    def create_schedule_tab(self):
        """스케줄 생성 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(w(20), h(20), w(20), h(20))
        
        # 헤더
        header = QLabel("생산 스케줄 생성")
        header.setProperty("class", "heading")
        layout.addWidget(header)
        
        # 설명
        info_label = QLabel(
            "판매계획을 기반으로 자동으로 최적화된 생산 스케줄을 생성합니다.\n"
            "마스터 데이터의 제약조건을 고려하여 스케줄링이 수행됩니다."
        )
        layout.addWidget(info_label)
        
        # 버튼 영역
        btn_layout = QHBoxLayout()
        
        load_btn = QPushButton("📁 판매계획 로드")
        load_btn.clicked.connect(self.open_sales_plan)
        btn_layout.addWidget(load_btn)
        
        generate_btn = QPushButton("⚙️ 스케줄 생성")
        generate_btn.clicked.connect(self.generate_schedule)
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #1428A0;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #0F1F7E;
            }
        """)
        btn_layout.addWidget(generate_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 로그 영역
        log_group = QGroupBox("처리 로그")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(h(200))
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        layout.addStretch()
        
        return widget
    
    def create_edit_tab(self):
        """스케줄 편집 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(w(10), h(10), w(10), h(10))
        
        # 스플리터
        splitter = QSplitter(Qt.Horizontal)
        
        # 좌측: 그리드 뷰
        grid_container = QWidget()
        grid_layout = QVBoxLayout(grid_container)
        
        header = QLabel("생산 스케줄 그리드")
        header.setProperty("class", "subheading")
        grid_layout.addWidget(header)
        
        self.schedule_grid = ScheduleGridView(master_data=self.controller.master_data)
        grid_layout.addWidget(self.schedule_grid)
        
        # 컨트롤러에 grid_view 참조 설정
        self.controller.grid_view = self.schedule_grid
        
        splitter.addWidget(grid_container)
        
        # 우측: 정보 패널
        info_panel = self.create_info_panel()
        splitter.addWidget(info_panel)
        
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        return widget
    
    def create_info_panel(self):
        """정보 패널 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 선택된 배치 정보
        batch_group = QGroupBox("선택된 배치")
        batch_layout = QVBoxLayout()
        
        self.batch_info_label = QLabel("배치를 선택하세요")
        batch_layout.addWidget(self.batch_info_label)
        
        batch_group.setLayout(batch_layout)
        layout.addWidget(batch_group)
        
        # 요약 정보
        summary_group = QGroupBox("스케줄 요약")
        summary_layout = QVBoxLayout()
        
        self.summary_label = QLabel("스케줄이 생성되지 않았습니다")
        summary_layout.addWidget(self.summary_label)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # 액션 버튼
        action_group = QGroupBox("작업")
        action_layout = QVBoxLayout()
        
        # 스케줄 초기화 버튼 추가
        clear_btn = QPushButton("🗑️ 스케줄 초기화")
        clear_btn.clicked.connect(self.clear_schedule)
        action_layout.addWidget(clear_btn)
        
        export_btn = QPushButton("💾 결과 내보내기")
        export_btn.clicked.connect(lambda: self.export_results('xlsx'))
        action_layout.addWidget(export_btn)
        
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.clicked.connect(self.refresh_schedule_view)
        action_layout.addWidget(refresh_btn)
        
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)
        
        layout.addStretch()
        
        return widget
    
    def connect_signals(self):
        """시그널 연결"""
        # 컨트롤러 시그널
        self.controller.schedule_generated.connect(self.on_schedule_generated)
        self.controller.schedule_updated.connect(self.refresh_schedule_view)
        self.controller.error_occurred.connect(self.show_error)
        
        # 그리드 뷰 시그널
        self.schedule_grid.batch_moved.connect(self.on_batch_moved)
        self.schedule_grid.batch_selected.connect(self.on_batch_selected)
        
        # 마스터 데이터 변경
        self.master_data_view.data_changed.connect(self.on_master_data_changed)
    
    def open_sales_plan(self):
        """판매계획 파일 열기"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "판매계획 파일 선택",
            "data",
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if file_path:
            if self.controller.load_sales_plan(file_path):
                self.current_file_label.setText(f"판매계획: {file_path.split('/')[-1]}")
                self.log_message(f"판매계획 로드 완료: {file_path}")
                self.statusBar().showMessage("판매계획이 로드되었습니다")
    
    def generate_schedule(self):
        """스케줄 생성"""
        if self.controller.current_sales_df is None:
            QMessageBox.warning(self, "경고", "먼저 판매계획을 로드해주세요.")
            return
        
        # 진행률 다이얼로그
        progress = QProgressDialog("스케줄 생성 중...", "취소", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        def update_progress(value, message):
            progress.setValue(value)
            progress.setLabelText(message)
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
        
        # 스케줄 생성
        self.log_message("스케줄 생성 시작...")
        
        plan = self.controller.generate_schedule(update_progress)
        
        progress.close()
        
        if plan:
            self.log_message("스케줄 생성 완료!")
            QMessageBox.information(self, "완료", "스케줄이 성공적으로 생성되었습니다.")
    
    def on_schedule_generated(self, plan):
        """스케줄 생성 완료"""
        self.schedule_status_label.setText(f"스케줄: 생성됨 ({len(plan.batches)}개 배치)")
        
        # 그리드에 로드
        self.schedule_grid.load_schedule(plan)
        
        # 요약 정보 업데이트
        self.update_summary()
        
        # 편집 탭으로 이동
        self.tab_widget.setCurrentIndex(2)
    
    def on_batch_moved(self, batch_id, new_equipment_id, new_date):
        """배치 이동 처리"""
        # 유효성 검사
        valid, message = self.controller.validate_batch_move(
            batch_id, new_equipment_id, new_date
        )
        
        if not valid:
            QMessageBox.warning(self, "이동 불가", message)
            self.refresh_schedule_view()
            return
        
        # 이동 수행
        if self.controller.move_batch(batch_id, new_equipment_id, new_date):
            self.log_message(f"배치 {batch_id} 이동 완료")
        else:
            self.refresh_schedule_view()
    
    def on_batch_selected(self, batch):
        """배치 선택"""
        if batch:
            info = f"""
            배치 ID: {batch.id}
            제품: {batch.product_name}
            장비: {batch.equipment_id}
            시작: {batch.start_time.strftime('%Y-%m-%d %H:%M')}
            소요시간: {batch.duration_hours}시간
            공정: {batch.process_id or 'N/A'}
            """
            self.batch_info_label.setText(info.strip())
    
    def on_master_data_changed(self):
        """마스터 데이터 변경"""
        self.log_message("마스터 데이터가 변경되었습니다.")
        self.statusBar().showMessage("마스터 데이터가 변경되었습니다", 3000)
    
    def refresh_schedule_view(self):
        """스케줄 뷰 새로고침"""
        self.schedule_grid.refresh_view()
        self.update_summary()
    
    def update_summary(self):
        """요약 정보 업데이트"""
        summary = self.controller.get_schedule_summary()
        if summary:
            text = f"""
            총 배치수: {summary['total_batches']}
            제품별 배치수:
            """
            for prod_id, prod_info in summary['products'].items():
                text += f"\n  - {prod_info['name']}: {prod_info['count']}개"
            
            self.summary_label.setText(text.strip())
    
    def export_results(self, format='xlsx'):
        """결과 내보내기"""
        if not self.controller.current_plan:
            QMessageBox.warning(self, "경고", "내보낼 스케줄이 없습니다.")
            return
        
        # 파일 형식별 필터
        filters = {
            'csv': "CSV Files (*.csv)",
            'xlsx': "Excel Files (*.xlsx)",
            'xml': "XML Files (*.xml)",
            'grid': "Excel Grid View (*.xlsx)"
        }
        
        default_name = {
            'csv': "production_schedule.csv",
            'xlsx': "production_schedule.xlsx",
            'xml': "production_schedule.xml",
            'grid': "production_schedule_grid.xlsx"
        }
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "결과 저장",
            default_name[format],
            filters[format]
        )
        
        if file_path:
            if self.controller.export_schedule(file_path, format):
                QMessageBox.information(
                    self,
                    "저장 완료",
                    f"파일이 저장되었습니다:\n{file_path}"
                )
                self.log_message(f"결과 내보내기 완료: {file_path}")
    
    def create_sample_files(self):
        """샘플 파일 생성"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "샘플 파일 저장 위치 선택",
            "data"
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
                self.show_error(str(e))
    
    def show_about(self):
        """프로그램 정보"""
        QMessageBox.about(
            self,
            "APS 생산계획 시스템",
            "APS Production Planning System v1.0.0\n\n"
            "판매계획을 기반으로 최적화된 생산계획을 생성하고\n"
            "시각적으로 편집할 수 있는 시스템입니다.\n\n"
            "주요 기능:\n"
            "- 마스터 데이터 관리 (제품, 공정, 장비, 작업자)\n"
            "- 자동 스케줄 생성 및 최적화\n"
            "- 드래그&드롭 기반 스케줄 편집\n"
            "- 다양한 형식으로 결과 내보내기\n\n"
            "© 2025 APS Development Team"
        )
    
    def log_message(self, message):
        """로그 메시지 추가"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def show_error(self, message):
        """에러 메시지 표시"""
        QMessageBox.critical(self, "오류", message)
        self.log_message(f"오류: {message}")
    
    def clear_schedule(self):
        """스케줄 초기화"""
        reply = QMessageBox.question(
            self, '확인', 
            '현재 스케줄을 모두 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 생산계획 초기화
            self.production_plan = ProductionPlan()
            
            # 스케줄 뷰 초기화
            if hasattr(self, 'schedule_view'):
                self.schedule_view.production_plan = self.production_plan
                self.schedule_view.refresh_view()
            
            # 요약 정보 업데이트
            self.update_summary()
            
            QMessageBox.information(self, "완료", "스케줄이 초기화되었습니다.")
            self.log_message("스케줄이 초기화되었습니다")