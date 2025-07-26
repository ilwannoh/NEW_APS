from PyQt5.QtWidgets import QWidget, QVBoxLayout
from app.views.components.result_components.table_widget.summary_widget import SummaryWidget

class SummaryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_page = parent
        self.summary_widget = None
        self.setup_ui()

    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Summary 위젯 생성
        self.summary_widget = SummaryWidget()
        layout.addWidget(self.summary_widget)

        # 부모의 summary_widget 속성 설정
        if hasattr(self.parent_page, 'summary_widget'):
            self.parent_page.summary_widget = self.summary_widget

    def update_content(self, data):
        """콘텐츠 업데이트"""
        if self.summary_widget and data is not None:
            self.summary_widget.run_analysis(data)

    def get_widget(self):
        """위젯 반환 (호환성 유지)"""
        return self.summary_widget