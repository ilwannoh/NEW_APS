from PyQt5.QtWidgets import QWidget, QVBoxLayout
from app.views.components.result_components.table_widget.split_allocation_widget import SplitAllocationWidget


class SplitViewTab(QWidget):
    """SplitView 탭 컴포넌트"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_page = parent
        self.split_allocation_widget = None
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 분산 배치 분석 위젯 생성
        self.split_allocation_widget = SplitAllocationWidget()
        layout.addWidget(self.split_allocation_widget)
        
        # 부모의 split_allocation_widget 속성 설정 (호환성)
        if hasattr(self.parent_page, 'split_allocation_widget'):
            self.parent_page.split_allocation_widget = self.split_allocation_widget

    def get_widget(self):
        """위젯 반환"""
        return self.split_allocation_widget