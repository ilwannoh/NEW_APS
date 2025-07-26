from PyQt5.QtWidgets import QWidget, QVBoxLayout
from app.views.components.result_components.table_widget.portcapa_widget import PortCapaWidget


class PortCapaTab(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_page = parent
        self.portcapa_widget = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # PortCapa 위젯 생성
        self.portcapa_widget = PortCapaWidget()
        self.portcapa_widget.setStyleSheet("""
            QWidget { 
                border: none;
                outline: none;
                background-color: white;
            }
        """)
        layout.addWidget(self.portcapa_widget)
        
        # 부모의 portcapa_widget 속성 설정 (호환성)
        if hasattr(self.parent_page, 'portcapa_widget'):
            self.parent_page.portcapa_widget = self.portcapa_widget
    
    """
    위젯 반환
    """
    def get_widget(self):
        return self.portcapa_widget