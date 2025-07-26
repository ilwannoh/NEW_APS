from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QBrush, QCursor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QTabWidget, QPushButton, QSizePolicy, QHBoxLayout,
    QFrame, QHeaderView, QSplitter
)
from app.resources.fonts.font_manager import font_manager
from app.resources.styles.result_style import ResultStyles
from app.utils.error_handler import (
    error_handler, safe_operation,
    DataError, ValidationError
)
from app.models.common.screen_manager import *
from app.models.common.settings_store import SettingsStore
"""
좌측 파라미터 영역에 프로젝트 분석 결과 표시
"""


class LeftParameterComponent(QWidget):
    def __init__(self):
        super().__init__()

        self.all_project_analysis_data = {}
        self.pages = {}

        self._init_ui()
        self._initialize_all_tabs()

    """
    모든 탭의 컨텐츠 초기화
    """

    @error_handler(
        show_dialog=False,
        default_return=None
    )
    def _initialize_all_tabs(self):
        for metric in self.metrics:
            if metric in self.pages:
                page = self.pages[metric]
                table = page['table']
                table.clear()
                table.setColumnCount(0)
                page['summary_table'].clear()

    """
    UI 요소 초기화 및 배치
    """

    @error_handler(
        show_dialog=False,
        default_return=None
    )
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 전체 컨테이너에 스타일 적용
        self.setStyleSheet("background-color: white; border: none;")

        self.tab_buttons = []
        self.metrics = [
            "Production Capacity",
            "Materials",
            "Current Shipment",
            "Plan Retention",
        ]

        # 버튼 영역을 위한 프레임
        button_frame = QFrame()
        button_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #F5F5F5;
                border: none;
                border-bottom: {f(1)}px solid #E0E0E0;
                border-radius: 0px;
            }}
        """)

        button_group_layout = QHBoxLayout(button_frame)
        button_group_layout.setSpacing(f(2))
        button_group_layout.setContentsMargins(w(10), h(8), w(10), h(8))

        for i, btn_text in enumerate(self.metrics):
            btn = QPushButton(btn_text)
            btn_font = font_manager.get_just_font("SamsungOne-700").family()
            btn.setCursor(QCursor(Qt.PointingHandCursor))

            btn.setMinimumWidth(w(80))

            # 버튼 스타일 업데이트
            if i == 0:
                btn.setStyleSheet(f"""
                            QPushButton {{
                                background-color: #1428A0;
                                color: white;
                                border: none;
                                border-radius: 5px;
                                padding: 4px 8px;
                                min-height: 26px;
                                font-weight: bold;
                                font-family: {btn_font};
                                font-size: {f(16)}px;
                            }}
                            QPushButton:hover {{
                                background-color: #0F1F8A;
                            }}
                        """)
            else:
                btn.setStyleSheet(f"""
                            QPushButton {{
                                background-color: white;
                                color: #666666;
                                border: 1px solid #E0E0E0;
                                border-radius: 5px;
                                padding: 4px 8px;
                                min-height: 26px;
                                font-weight: bold;
                                font-family: {btn_font};
                                font-size: {f(16)}px;
                            }}
                            QPushButton:hover {{
                                background-color: #F5F5F5;
                                color: #1428A0;
                                border-color: #1428A0;
                            }}
                        """)

            btn.clicked.connect(lambda checked, idx=i: self.switch_tab(idx))
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button_group_layout.addWidget(btn)
            self.tab_buttons.append(btn)

        layout.addWidget(button_frame)

        # 컨텐츠 영역
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: none;
            }
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.tabBar().hide()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: white;
            }
        """)

        for metric in self.metrics:
            try:
                page = QWidget()
                page_layout = QVBoxLayout(page)
                page_layout.setContentsMargins(0, 0, 0, 0)
                page_layout.setSpacing(0)

                # 가로 분할기 생성
                horizontal_splitter = QSplitter(Qt.Horizontal)
                horizontal_splitter.setHandleWidth(5)
                horizontal_splitter.setStyleSheet("""
                    QSplitter::handle {
                        background-color: white;
                        border-radius: 2px;
                    }
                    QSplitter::handle:hover {
                        background-color: #1428A0;
                    }
                """)

                # 왼쪽: 테이블 컨테이너
                table_container = QFrame()
                table_container.setStyleSheet("""
                    QFrame {
                        background-color: white;
                        border: 1px solid #E0E0E0;
                        border-radius: 0px;
                    }
                """)
                table_layout = QVBoxLayout(table_container)
                table_layout.setContentsMargins(0, 0, 0, 0)

                table = QTreeWidget()
                table.setRootIsDecorated(False)
                table.setSortingEnabled(True)
                table.setHeaderHidden(True)
                table.setStyleSheet(f"""
                    QTreeWidget {{ 
                        border: none; 
                        outline: none;
                        background-color: white;
                        border-radius: 0px;
                        font-family: {font_manager.get_just_font("SamsungOne-700").family()};
                        font-size: {f(13)}px;
                    }}
                    QTreeWidget::item {{
                        padding: 6px; 
                        border-bottom: 1px solid #F5F5F5;
                    }}
                    QTreeWidget::item:selected {{
                        background-color: #E8ECFF;
                        color: black;
                        font-size: {f(13)}px;
                    }}
                    QTreeWidget::item:hover {{
                        background-color: #F5F7FF;
                    }}
                    QHeaderView::section {{ 
                        background-color: #F5F5F5;
                        color: #333333;
                        border: none;
                        padding: {h(3)}px;
                        font-weight: bold;
                        border-bottom: 2px solid #E0E0E0;
                        font-size: {f(13)}px;
                    }}
                    QScrollBar:vertical {{
                        border: none;
                        width: 10px;
                        margin: 0px;
                    }}
                    QScrollBar::handle:vertical {{
                        background: #CCCCCC;
                        min-height: 20px;
                        border-radius: 5px;
                    }}
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                        border: none;
                        background: none;
                        height: 0px;
                    }}
                    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                        background: none;
                    }}
                    QScrollBar:horizontal {{
                        border: none;
                        height: 10px;
                        margin: 0px;
                    }}
                    QScrollBar::handle:horizontal {{
                        background: #CCCCCC;
                        min-width: 20px;
                        border-radius: 5px;
                    }}
                    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                        border: none;
                        background: none;
                        width: 0px;
                    }}
                    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                        background: none;
                    }}
                """)

                table_layout.addWidget(table)

                # 오른쪽: Summary 테이블 컨테이너
                summary_container = QFrame()
                summary_container.setStyleSheet("""
                    QFrame {
                        background-color: #F8F9FA;
                        border: 1px solid #E0E0E0;
                        border-radius: 0px;
                    }
                """)
                summary_layout = QVBoxLayout(summary_container)
                summary_layout.setContentsMargins(0, 0, 0, 0)
                summary_layout.setSpacing(5)

                # Summary 테이블 생성
                summary_table = QTreeWidget()
                summary_table.setRootIsDecorated(False)
                summary_table.setHeaderHidden(True)
                summary_table.setAlternatingRowColors(True)
                summary_table.setStyleSheet(f"""
                    QTreeWidget {{ 
                        border: none; 
                        outline: none;
                        background-color: white;
                        border-radius: 6px;
                    }}
                    QTreeWidget::item {{
                        padding: 6px 10px;
                        border-bottom: 1px solid #F0F0F0;
                    }}
                    QTreeWidget::item:alternate {{
                        background-color: #FAFAFA;
                    }}
                    QTreeWidget::item:hover {{
                        background-color: #F5F7FF;
                    }}
                    QScrollBar:vertical {{
                        border: none;
                        width: 10px;
                        margin: 0px;
                    }}
                    QScrollBar::handle:vertical {{
                        background: #CCCCCC;
                        min-height: 20px;
                        border-radius: 5px;
                    }}
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                        border: none;
                        background: none;
                        height: 0px;
                    }}
                    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                        background: none;
                    }}
                    QScrollBar:horizontal {{
                        border: none;
                        height: 10px;
                        margin: 0px;
                    }}
                    QScrollBar::handle:horizontal {{
                        background: #CCCCCC;
                        min-width: 20px;
                        border-radius: 5px;
                    }}
                    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                        border: none;
                        background: none;
                        width: 0px;
                    }}
                    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                        background: none;
                    }}
                """)
                summary_table.setColumnCount(2)

                summary_layout.addWidget(summary_table)

                # 스플리터에 위젯 추가
                horizontal_splitter.addWidget(table_container)
                horizontal_splitter.addWidget(summary_container)

                # 초기 비율 설정 (7:3)
                horizontal_splitter.setSizes([700, 300])

                # 페이지 레이아웃에 스플리터 추가
                page_layout.addWidget(horizontal_splitter)

                self.tab_widget.addTab(page, metric)

                self.pages[metric] = {
                    "table": table,
                    "summary_table": summary_table,  # 변경된 부분
                    "splitter": horizontal_splitter
                }

            except Exception as e:
                raise ValidationError(f'Failed to set up UI for metric \'{metric}\' : {str(e)}')

        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        content_layout.addWidget(self.tab_widget)
        layout.addWidget(content_frame)

    """
    프로젝트 분석 데이터 설정
    """

    @error_handler(
        default_return=None
    )
    def set_project_analysis_data(self, data_dict):
        if not isinstance(data_dict, dict):
            raise DataError('Analysis data must be a dictionary', {'type': type(data_dict)})

        self.all_project_analysis_data = data_dict

        if not self.metrics or len(self.metrics) == 0:
            raise ValidationError('No metrics defined')

        safe_operation(
            self._update_tab_content,
            'Error updating first tab content',
            self.metrics[0]
        )

    """
    탭을 변경할 때 호출
    """

    @error_handler(
        default_return=None
    )
    def _on_tab_changed(self, index):
        if index < 0 or index >= len(self.metrics):
            raise IndexError(f'Invalid tab index : {index}')

        metric = self.metrics[index]

        safe_operation(
            self._update_tab_content,
            f'Error updating {metric} tab content',
            metric
        )

    """
    탭 내용 업데이트
    """

    @error_handler(
        default_return=None
    )
    def _update_tab_content(self, metric):
        data = self.all_project_analysis_data.get(metric)
        page_widgets = self.pages.get(metric)

        if data is None or page_widgets is None:
            if page_widgets:
                table = page_widgets['table']
                safe_operation(table.clear, 'Error clearing table')
                safe_operation(table.setColumnCount, 'Error setting column count', 0)
                safe_operation(table.setHeaderHidden, 'Error hiding header', True)

                summary_table = page_widgets["summary_table"]
                safe_operation(summary_table.clear, 'Error clearing summary table')
            return

        display_df = data.get('display_df')
        summary = data.get('summary')

        table = page_widgets["table"]
        safe_operation(table.clear, 'Error clearing table')

        if display_df is None or (hasattr(display_df, 'empty') and display_df.empty):
            safe_operation(table.setColumnCount, 'Error setting column count', 0)
            safe_operation(table.setHeaderHidden, 'Error hiding header', True)
            summary_table = page_widgets["summary_table"]
            safe_operation(summary_table.clear, 'Error clearing summary table')
            return

        safe_operation(table.setHeaderHidden, 'Error setting header visibility', False)

        # 표 헤더 설정
        try:
            if display_df is None or display_df.empty:
                table.setColumnCount(0)
            else:
                if metric == 'Production Capacity':
                    headers = ["PJT Group", "PJT", "MFG", "SOP", "CAPA", "MFG/CAPA", "SOP/CAPA"]
                elif metric == 'Materials':
                    headers = list(display_df.columns)
                elif metric == 'Current Shipment':
                    headers = ["Category", "Name", "SOP", "Production", "Fulfillment Rate", "Status"]
                elif metric == 'Plan Retention':
                    headers = ['Line','Time','RMC','Item','Previous Qty','Max Item Qty','Max RMC Qty']
                else:
                    headers = list(display_df.columns) if hasattr(display_df, 'columns') else []

                table.setColumnCount(len(headers))
                table.setHeaderLabels(headers)

                # 헤더의 열 너비를 균등하게 분배
                header = table.header()
                header.setSectionResizeMode(QHeaderView.Stretch)

                red_brush = QBrush(QColor('#e74c3c'))
                yellow_brush = QBrush(QColor('#f39c12'))
                green_brush = QBrush(QColor('#2ecc71'))
                bold_font = QFont()
                bold_font.setBold(True)

                for _, row in display_df.iterrows():
                    row_data = []

                    for col in headers:
                        val = row.get(col, '')

                        if isinstance(val, (int, float)):
                            row_data.append(f'{val :,.0f}')
                        else:
                            row_data.append(str(val))

                    item = QTreeWidgetItem(row_data)

                    # 탭에 따른 표시 그래프(표) 내용 설정
                    try:
                        if metric == "Production Capacity":
                            if str(row.get('PJT', '')) == 'Total':
                                for col in range(len(headers)):
                                    item.setFont(col, bold_font)
                                if row.get('status', '') == 'Error':
                                    for col in range(len(headers)):
                                        item.setForeground(col, red_brush)
                        elif metric == 'Materials':
                            if 'Shortage Amount' in headers:
                                shortage_col = headers.index('Shortage Amount')

                                try:
                                    shortage_amount = float(row.get('Shortage Amount', 0))

                                    if shortage_amount > 0:
                                        for col in range(len(headers)):
                                            item.setForeground(col, red_brush)
                                except (ValueError, TypeError):
                                    pass
                        elif metric == 'Current Shipment':
                            status = row.get('Status', '')
                            category = row.get('Category', '')

                            if category == 'Total':
                                for col in range(len(headers)):
                                    item.setFont(col, bold_font)

                            if status == 'Error':
                                for col in range(len(headers)):
                                    item.setForeground(col, red_brush)
                            elif status == 'Warning':
                                for col in range(len(headers)):
                                    item.setForeground(col, yellow_brush)
                            elif status == 'OK':
                                for col in range(len(headers)):
                                    item.setForeground(col, green_brush)
                        elif metric == 'Plan Retention':
                            if round(row['Max Item Qty']) < round(row['Previous Qty']) or round(row['Max RMC Qty']) < round(row['Previous Qty']):
                                for col in range(len(header)):
                                    item.setForeground(col,red_brush)

                    except Exception as style_error:
                        pass

                    table.addTopLevelItem(item)
        except Exception as e:
            raise DataError(f'Error displaying data : {str(e)}', {'metric': metric})

        # Summary 테이블 업데이트
        summary_table = page_widgets["summary_table"]
        safe_operation(summary_table.clear, 'Error clearing summary table')

        if summary is not None:
            # 메트릭별 summary 데이터 구조화
            summary_data = []

            if metric == 'Production Capacity':
                summary_data = [
                    ("Total Groups", f"{summary.get('Total number of groups', 0)}"),
                    ("Error Groups", f"{summary.get('Number of error groups', 0)}"),
                    ("Total MFG", f"{summary.get('Total MFG', 0):,}"),
                    ("Total SOP", f"{summary.get('Total SOP', 0):,}"),
                    ("Total CAPA", f"{summary.get('Total CAPA', 0):,}"),
                    ("MFG/CAPA Ratio", f"{summary.get('Total MFG/CAPA ratio', '0%')}"),
                    ("SOP/CAPA Ratio", f"{summary.get('Total SOP/CAPA ratio', '0%')}")
                ]

            elif metric == 'Materials':
                summary_data = [
                    ("Total Materials", f"{summary.get('Total materials', 0):,}"),
                    ("Weekly Shortage", f"{summary.get('Weekly shortage materials', 0):,}"),
                    ("Full Period Shortage", f"{summary.get('Full period shortage materials', 0):,}"),
                    ("Shortage Rate", f"{summary.get('Shortage rate (%)', 0)}%"),
                    ("Analysis Period", f"{summary.get('Period', 'N/A')}")
                ]

                # Top shortage materials가 있다면 추가
                top_materials = summary.get('Top shortage materials', 'None')
                if top_materials and top_materials != 'None':
                    summary_data.append(("Top Shortages", top_materials))

            elif metric == 'Current Shipment':
                summary_data = [
                    ("Fulfillment Rate", f"{summary.get('Overall fulfillment rate', '0%')}"),
                    ("Total Demand (SOP)", f"{summary.get('Total demand(SOP)', 0):,}"),
                    ("Total Production", f"{summary.get('Total production', 0):,}"),
                    ("Project Count", f"{summary.get('Project count', 0)}"),
                    ("Site Count", f"{summary.get('Site count', 0)}"),
                    ("Bottleneck Items", f"{summary.get('Bottleneck items', 0)}")
                ]
            elif metric == 'Plan Retention':
                summary_data = [
                    ("Maximum SKU Plan Retention Rate",f"{summary.get('Maximum SKU Plan Retention Rate',0):.1f} %"),
                    ("Maximum RMC Plan Retention Rate",f"{summary.get('Maximum RMC Plan Retention Rate',0):.1f} %"),
                    ("Required SKU Plan Retention Rate1",f"{SettingsStore.get('op_SKU_1',0)} %"),
                    ("Required RMC Plan Retention Rate1",f"{SettingsStore.get('op_RMC_1',0)} %"),
                    ("Required SKU Plan Retention Rate2",f"{SettingsStore.get('op_SKU_2',0)} %"),
                    ("Required RMC Plan Retention Rate2",f"{SettingsStore.get('op_RMC_2',0)} %"),
                ]
            # Summary 테이블에 데이터 추가
            for label, value in summary_data:
                item = QTreeWidgetItem([label, str(value)])

                # 라벨 스타일링
                label_font = font_manager.get_just_font("SamsungOne-700")
                label_font.setBold(True)
                label_font.setPixelSize(f(13))
                item.setFont(0, label_font)
                item.setForeground(0, QColor("#666666"))

                # 값 스타일링
                value_font = font_manager.get_just_font("SamsungOne-700")
                value_font.setPixelSize(f(13))
                item.setFont(1, value_font)

                # 특정 값에 대한 색상 설정
                if metric == 'Production Capacity' and label == "Error Groups":
                    if int(str(value).replace(',', '')) > 0:
                        item.setForeground(1, QColor("#E74C3C"))
                elif metric == 'Materials' and label == "Shortage Rate":
                    rate_value = float(str(value).replace('%', ''))
                    if rate_value > 10:
                        item.setForeground(1, QColor("#E74C3C"))
                    elif rate_value > 5:
                        item.setForeground(1, QColor("#F39C12"))
                    else:
                        item.setForeground(1, QColor("#2ECC71"))
                elif metric == 'Current Shipment' and label == "Fulfillment Rate":
                    rate_value = float(str(value).replace('%', ''))
                    if rate_value < 90:
                        item.setForeground(1, QColor("#E74C3C"))
                    elif rate_value < 95:
                        item.setForeground(1, QColor("#F39C12"))
                    else:
                        item.setForeground(1, QColor("#2ECC71"))

                summary_table.addTopLevelItem(item)

            # 열 너비 자동 조정
            summary_table.resizeColumnToContents(0)
            summary_table.resizeColumnToContents(1)
        else:
            # 데이터가 없을 때 기본 메시지
            empty_item = QTreeWidgetItem(["No data", ""])
            empty_item.setForeground(0, QColor("#999999"))
            summary_table.addTopLevelItem(empty_item)

    """
    선택된 탭 새로고침
    """

    def refresh_current_tab(self):
        current_index = self.tab_widget.currentIndex()

        if 0 <= current_index < len(self.metrics):
            metric = self.metrics[current_index]
            self._update_tab_content(metric)

    def switch_tab(self, index):
        """
        index 번째 탭으로 전환
        """
        for i, btn in enumerate(self.tab_buttons):
            if i == index:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1428A0;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: 4px 8px;
                        min-height: 26px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #0F1F8A;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: white;
                        color: #666666;
                        border: 1px solid #E0E0E0;
                        border-radius: 5px;
                        padding: 4px 8px;
                        min-height: 26px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #F5F5F5;
                        color: #1428A0;
                        border-color: #1428A0;
                    }
                """)
        self.tab_widget.setCurrentIndex(index)
        self._on_tab_changed(index)