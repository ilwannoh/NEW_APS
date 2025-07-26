from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from PyQt5.QtCore import Qt
from app.views.components.visualization.mpl_canvas import MplCanvas
from app.views.components.visualization.visualization_updater import VisualizationUpdater


class CapaTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_page = parent
        self.capa_canvas = None
        self.util_canvas = None
        self.init_ui()

    def init_ui(self):
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 스크롤 영역 생성 및 스타일링
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
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

        # 스크롤 콘텐츠 위젯
        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(20)

        # *** 핵심 변경: 고정 크기 설정으로 스크롤바 강제 표시 ***
        # Capa 차트 캔버스 - 더 큰 고정 크기로 설정
        self.capa_canvas = MplCanvas(width=10, height=6, dpi=100)
        content_layout.addWidget(self.capa_canvas)

        # Utilization 차트 캔버스 - 더 큰 고정 크기로 설정
        self.util_canvas = MplCanvas(width=10, height=6, dpi=100)
        content_layout.addWidget(self.util_canvas)

        # 하단에 여백 추가
        content_layout.addStretch()

        # *** 중요: 스크롤 콘텐츠의 최소 크기 설정 ***
        # scroll_content.setMinimumSize(800,800)  # 차트보다 약간 큰 크기로 설정

        # 스크롤 영역 설정
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    """
    콘텐츠 업데이트
    """
    def update_content(self, capa_data, utilization_data):
        if self.capa_canvas and capa_data is not None:
            VisualizationUpdater.update_capa_chart(self.capa_canvas, capa_data)

        if self.util_canvas and utilization_data is not None:
            VisualizationUpdater.update_utilization_chart(self.util_canvas, utilization_data)

    """
    캔버스들 반환
    """
    def get_canvases(self):
        return [self.capa_canvas, self.util_canvas]

    """
    초기 시각화 생성
    """
    def create_initial_visualizations(self, capa_data, utilization_data):
        if self.capa_canvas:
            VisualizationUpdater.update_capa_chart(self.capa_canvas, capa_data)

        if self.util_canvas:
            VisualizationUpdater.update_utilization_chart(self.util_canvas, utilization_data)