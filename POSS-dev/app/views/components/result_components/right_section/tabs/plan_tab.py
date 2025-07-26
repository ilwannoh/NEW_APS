from PyQt5.QtWidgets import QWidget, QVBoxLayout
from app.views.components.result_components.table_widget.maintenance_rate.plan_maintenance_widget import PlanMaintenanceWidget


class PlanTab(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_page = parent
        self.plan_maintenance_widget = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 계획 유지율 위젯 생성
        self.plan_maintenance_widget = PlanMaintenanceWidget()
        layout.addWidget(self.plan_maintenance_widget)
        
        # 부모의 plan_maintenance_widget 속성 설정 (호환성)
        if hasattr(self.parent_page, 'plan_maintenance_widget'):
            self.parent_page.plan_maintenance_widget = self.plan_maintenance_widget
    
    """
    위젯 반환
    """
    def get_widget(self):
        return self.plan_maintenance_widget