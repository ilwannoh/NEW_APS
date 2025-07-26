import pandas as pd
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QSplitter,
    QMessageBox, QScrollArea, QStackedWidget
)
from PyQt5.QtCore import Qt, pyqtSignal

from ...resources.styles.pre_assigned_style import PRIMARY_BUTTON_STYLE, SECONDARY_BUTTON_STYLE, ACTIVE_BUTTON_STYLE, INACTIVE_BUTTON_STYLE
from .pre_assigned_components.summary import SummaryWidget
from .pre_assigned_components.calendar_header import CalendarHeader
from .pre_assigned_components.weekly_calendar import WeeklyCalendar
from .pre_assigned_components.project_group_dialog import ProjectGroupDialog
from .result_components.filter_widget import FilterWidget
from app.utils.fileHandler import create_from_master
from app.utils.export_manager import ExportManager
from app.models.common.screen_manager import *
from app.resources.fonts.font_manager import font_manager

bold_font = font_manager.get_just_font("SamsungSharSans-Bold").family()
normal_font = font_manager.get_just_font("SamsungOne-700").family()

"""
공통으로 사용하는 버튼 생성 함수
"""
def create_button(text, style="primary", parent=None):
    btn = QPushButton(text, parent)
    btn.setCursor(QCursor(Qt.PointingHandCursor))
    btn.setFixedSize(w(100), h(40))
    btn.setStyleSheet(
        (PRIMARY_BUTTON_STYLE if style == "primary" else SECONDARY_BUTTON_STYLE)
        + f" font-family:{normal_font}; font-size:{f(14)}px;"
    )
    return btn


class PlanningPage(QWidget):
    # 최적화 요청 시그널
    optimization_requested = pyqtSignal(dict)
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._df = pd.DataFrame()
        self._splitter_ratio = 3/4
        self._setup_ui()

    def _setup_ui(self):
        # 메인 레이아웃 (타이틀 + 버튼)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignTop)

        title_hbox = QHBoxLayout()
        title_hbox.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel("Pre-Assignment")
        lbl.setStyleSheet(f"font-family:{bold_font}; font-size:{f(21)}px; font-weight: 900;")
        title_hbox.addWidget(lbl)

        # Export 버튼
        btn_export = create_button("Export", "primary", self)
        btn_export.clicked.connect(self.on_export_click)
        title_hbox.addWidget(btn_export)

        # Run 버튼
        self.btn_run = create_button("Run", "primary", self)
        self.btn_run.clicked.connect(self.on_run_click)
        title_hbox.addWidget(self.btn_run)

        # Reset 버튼
        btn_reset = create_button("Reset", "secondary", self)
        btn_reset.clicked.connect(self.on_reset_click)
        title_hbox.addWidget(btn_reset)

        self.main_layout.addLayout(title_hbox)

        # LEFT: 캘린더 영역 (데이터 없을 때 placeholder 표시)
        self.leftContainer = QWidget(self)
        self.leftContainer.setObjectName("leftContainer")
        self.leftContainer.setStyleSheet("""
            QWidget#leftContainer {
                border: 3px solid #cccccc;
            }
            QWidget#leftContainer, 
            QWidget#leftContainer * {
                background-color: white;
            }
        """)
        left_l = QVBoxLayout(self.leftContainer)
        left_l.setContentsMargins(20, 20, 20, 20)
        left_l.setSpacing(6)

        # placeholder: 데이터 없을 때 문구
        self.placeholder_label = QLabel("Please Load to Data", self.leftContainer)
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet(f"font-family:{normal_font}; font-size:{f(16)}px;")
        left_l.addWidget(self.placeholder_label, stretch=1)

        # RIGHT: 요약 테이블 영역
        self.rightContainer = QWidget(self)
        self.rightContainer.setObjectName("rightContainer")
        self.rightContainer.setStyleSheet("""
            QWidget#rightContainer {
                border: 3px solid #cccccc;
            }
            QWidget#rightContainer, 
            QWidget#rightContainer * {
                background-color: white;
            }
        """)
        right_l = QVBoxLayout(self.rightContainer)
        right_l.setContentsMargins(20, 20, 20, 20)
        right_l.setSpacing(6)
        
        # Summary 버튼 영역
        btn_bar = QHBoxLayout()
        self.btn_summary = QPushButton("Summary")
        self.btn_summary.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_summary.setStyleSheet(INACTIVE_BUTTON_STYLE)
        self.btn_summary.setFixedHeight(36)
        self.btn_summary.setEnabled(False)
        btn_bar.addWidget(self.btn_summary)
        right_l.addLayout(btn_bar)
        
        # SummaryWidget 영역
        self.stack = QStackedWidget(self.rightContainer)
        right_l.addWidget(self.stack, stretch=1)
        right_l.addStretch()

        # QSplitter
        self.splitter = QSplitter(Qt.Horizontal, self)
        self.splitter.setContentsMargins(0, 0, 0, 0)
        self.splitter.setHandleWidth(10)
        self.splitter.setChildrenCollapsible(False)

        self.splitter.addWidget(self.leftContainer)
        self.splitter.addWidget(self.rightContainer)
        self.main_layout.addWidget(self.splitter, 1)

        self.splitter.splitterMoved.connect(self._on_splitter_moved)

        self.setLayout(self.main_layout)

        # 시그널 중복 연결 방지용 플래그
        self._range_connected = False

    """
    스크롤바에 따른 margin 설정 
    """
    def _sync_header_margin(self):
        if not hasattr(self, 'header'):
            return
        sb = self.scroll_area.verticalScrollBar()
        right_margin = sb.sizeHint().width() if sb.maximum() > 0 else 0
        # 캘린더 헤더 레이아웃에 오른쪽 마진 설정
        self.header.layout().setContentsMargins(0, 0, right_margin, 0)

    def on_export_click(self):
        if self._df.empty:
            QMessageBox.warning(self, "Export Error", "No data to export.")
            return
        try:
            start, end = self.main_window.data_input_page.date_selector.get_date_range()
        except:
            start, end = None, None
        ExportManager.export_data(
            self,
            data_df=self._df,
            start_date=start,
            end_date=end,
            is_planning=True
        )

    """
    reset 버튼 클릭시 호출
    """
    def on_reset_click(self):
        self._df = pd.DataFrame(columns=["Line", "Time", "Qty", "Item", "Project"])

        # LEFT 영역: 이전 체크박스 제거
        if hasattr(self, 'filter_widget'):
            self.leftContainer.layout().removeWidget(self.filter_widget)
            self.filter_widget.deleteLater()
            del self.filter_widget

        # LEFT 영역: 이전 header 제거
        if hasattr(self, 'header'):
            self.leftContainer.layout().removeWidget(self.header)
            self.header.deleteLater()
            del self.header

        # LEFT 영역: 이전 캘린더 제거
        if hasattr(self, 'scroll_area'):
            self.leftContainer.layout().removeWidget(self.scroll_area)
            self.scroll_area.deleteLater()
            del self.scroll_area

        # RIGHT 영역: SummaryWidget 제거
        while self.stack.count():
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            w.deleteLater()
        # Summary 버튼 스타일 비활성화
        self.btn_summary.setStyleSheet(INACTIVE_BUTTON_STYLE)

        # LEFT 영역: placeholder 재생성
        if hasattr(self, 'placeholder_label'):
            self.leftContainer.layout().removeWidget(self.placeholder_label)
            self.placeholder_label.deleteLater()
            del self.placeholder_label

        self.placeholder_label = QLabel("Please Load to Data", self.leftContainer)
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet(
            f"font-family:{normal_font}; font-size:{f(16)}px;"
        )
        self.leftContainer.layout().addWidget(self.placeholder_label, stretch=1)

        self._range_connected = False

    """
    run 버튼 클릭시 호출
    """
    def on_run_click(self):
        if self._df.empty:
            QMessageBox.warning(self, "Error", "You need to load the results by running it first.")
            return
        all_groups = create_from_master()
        current = set(self._df['Project'])
        filtered = {
            gid: projs
            for gid, projs in all_groups.items()
            if current & set(projs)
        }

        dlg = ProjectGroupDialog(
            filtered,
            self._df,
            on_done_callback=self._on_optimization_prepare,
            parent=self
        )
        dlg.exec_()

    """
    projectGroupDialog에서 작업 완료 후 호출
    """
    def _on_optimization_prepare(self, result_df, filtered_df):
        # self.filtered_df = filtered_df
        pre_items = filtered_df['Item'].unique().tolist()
        self.main_window.result_page.set_optimization_result({
                'assignment_result': result_df,
                'pre_assigned_items': pre_items
            })
        self.main_window.navigate_to_page(2)

    """
    사전 할당 결과 표시 함수
    """
    def display_preassign_result(self, df: pd.DataFrame):
        self.on_reset_click()

        if hasattr(self, 'placeholder_label'):
            self.leftContainer.layout().removeWidget(self.placeholder_label)
            self.placeholder_label.deleteLater()
            del self.placeholder_label

        # 데이터 준비
        self._df = df.copy()
        # print(self._df)
        tmp = df.sort_values(by=['Line', 'Time', 'Qty'], ascending=[True,True,False]).reset_index(drop=True)
        agg = tmp.groupby(['Line', 'Time', 'Project'], as_index=False)['Qty'].sum()
        details = (
            tmp.groupby(['Line', 'Time', 'Project'])
              .apply(lambda g: g[[
                  'Demand', 'Item', 'To_site', 'SOP', 'MFG', 'RMC', 'Due_LT', 'Qty'
              ]].to_dict('records'))
              .to_frame('Details')
              .reset_index()
        )
        df_agg = agg.merge(details, on=['Line', 'Time', 'Project'])
        df_agg = df_agg.assign(Building = df_agg['Line'].str.split('_').str[0])
        df_agg['BuildingTotal'] = df_agg.groupby('Building')['Qty'].transform('sum')
        df_agg = df_agg.sort_values(
            by=['BuildingTotal', 'Building', 'Time', 'Qty'],
            ascending=[False, True, True, False]
        ).reset_index(drop=True)
        df_agg = df_agg.drop(columns=['Building', 'BuildingTotal'])
        # print(df_agg)
        
        # 각 Line별 총 Qty 계산
        line_qty = df.groupby('Line')['Qty'].sum().to_dict()
        
        # line, project, Building별로 묶기
        lines = tmp['Line'].unique().tolist()
        projects = tmp['Project'].unique().tolist()
        groups = {}
        for line, qty in line_qty.items():
            bld = line.split('_')[0]
            groups.setdefault(bld, []).append((line, qty))

        # Building별 총합 계산
        building_totals = {
            bld: sum(q for _, q in line)
            for bld, line in groups.items()
        }

        # Building 총합 내림차순 정렬
        sorted_buildings = sorted(
            building_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # 각 Building 안의 Line들도 Qty 내림차순 정렬
        self.line_order = []
        for bld, _ in sorted_buildings:
            for line, _ in sorted(groups[bld], key=lambda x: x[1], reverse=True):
                self.line_order.append(line)

        # 필터 생성
        self.filter_widget = FilterWidget(self.leftContainer)
        self.filter_widget.set_filter_data(lines=lines, projects=projects)
        self.filter_widget.filter_changed.connect(self._on_filter_changed)
        self.leftContainer.layout().addWidget(self.filter_widget, 0, Qt.AlignRight)

        # 캘린더 헤더 생성
        self.header = CalendarHeader(set(df['Time']), parent=self)

        # 캘린더 생성
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignTop)

        self.scroll_area.setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #CCCCCC;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                border: none;
                height: 10px;
                margin: 0px;
            }                  
            QScrollBar::handle:horizontal {
                background: #CCCCCC;
                min-width: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)

        self.body_container = QWidget()
        self.body_layout = QVBoxLayout(self.body_container)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(0)
        self.body_layout.setAlignment(Qt.AlignTop)

        calendar = WeeklyCalendar(df_agg, line_order=self.line_order)
        self.body_layout.addWidget(calendar, 0, Qt.AlignTop)

        self.scroll_area.setWidget(self.body_container)

        # 스크롤 시그널
        if not self._range_connected:
            self.scroll_area.verticalScrollBar().rangeChanged.connect(self._sync_header_margin)
            self._range_connected = True

        # 캘린더 헤더, 캘린더 배치
        left_l = self.leftContainer.layout()
        left_l.addWidget(self.header, stretch=0)
        left_l.addWidget(self.scroll_area, stretch=1)

        # 요약 테이블 생성, 버튼 연결
        summary = SummaryWidget(df, line_order=self.line_order, parent=self)
        self.stack.addWidget(summary)

        # try:
        #     self.btn_summary.clicked.disconnect()
        # except TypeError:
        #     pass

        # def _on_summary_clicked():
        #     self.stack.setCurrentWidget(summary)
        #     self.btn_summary.setStyleSheet(ACTIVE_BUTTON_STYLE)

        # self.btn_summary.clicked.connect(_on_summary_clicked)

        # self.stack.setCurrentWidget(summary)
        self.btn_summary.setStyleSheet(ACTIVE_BUTTON_STYLE)

        sizes = self.splitter.sizes()
        total = sum(sizes)
        if total:
            self._splitter_ratio = sizes[0] / total

    """
    필터 기능
    """
    def _on_filter_changed(self, states: dict):
        # 선택된 필터 리스트
        sel_lines    = [l for l, ok in states['line'].items() if ok]
        sel_projects = [p for p, ok in states['project'].items() if ok]

        df_filtered = self._df
        if sel_lines:
            df_filtered = df_filtered[df_filtered['Line'].isin(sel_lines)]
        if sel_projects:
            df_filtered = df_filtered[df_filtered['Project'].isin(sel_projects)]

        # 빈 결과 
        if df_filtered.empty:
            df_agg = pd.DataFrame(columns=['Line','Time','Project','Qty','Details'])
        else:
            # Qty 집계
            agg = df_filtered.groupby(
                ['Line','Time','Project'], as_index=False
            )['Qty'].sum()

            # Details 생성
            details_series = df_filtered.groupby(
                ['Line','Time','Project']
            ).apply(
                lambda g: g[[
                    'Demand','Item','To_site','SOP','MFG','RMC','Due_LT','Qty'
                ]].to_dict('records')
            )
            details = details_series.to_frame('Details').reset_index()

            df_agg = agg.merge(details, on=['Line','Time','Project'])

        # 정렬·삭제
        df_agg = df_agg.sort_values(
            by=['Line','Time','Qty'], ascending=[True, True, False]
        ).reset_index(drop=True)

        old = self.body_layout.takeAt(0).widget()
        if old:
            old.deleteLater()

        self.body_layout.addWidget(
            WeeklyCalendar(df_agg, line_order=self.line_order),
            0, Qt.AlignTop
        )
        self._sync_header_margin()

    """
    사용자 스플리터 변경
    """
    def _on_splitter_moved(self, pos, index):
        sizes = self.splitter.sizes()
        total = sum(sizes)
        if total:
            self._splitter_ratio = sizes[0] / total

    """
    스플리터 오버라이드
    """
    def resizeEvent(self, event):
        super().resizeEvent(event)
        total_w = self.width()
        left_w = int(total_w * self._splitter_ratio)
        self.splitter.setSizes([left_w, total_w - left_w])