from PyQt5.QtWidgets import QWidget, QVBoxLayout
from app.views.components.result_components.table_widget.shipment_widget import ShipmentWidget

class ShipmentTab(QWidget):
    """Shipment 탭 컴포넌트"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_page = parent
        self.shipment_widget = None
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 당주 출하 위젯 생성
        self.shipment_widget = ShipmentWidget()
        # 출하 상태 업데이트 시그널 연결
        self.shipment_widget.shipment_status_updated.connect(self.on_shipment_status_updated)
        layout.addWidget(self.shipment_widget)
        
        # 부모의 shipment_widget 속성 설정 (호환성)
        if hasattr(self.parent_page, 'shipment_widget'):
            self.parent_page.shipment_widget = self.shipment_widget
    
    def on_shipment_status_updated(self, failure_items):
        """출하 상태 업데이트 시 부모에게 전달"""
        if hasattr(self.parent_page, 'on_shipment_status_updated'):
            self.parent_page.on_shipment_status_updated(failure_items)

    
    def get_widget(self):
        """위젯 반환"""
        return self.shipment_widget