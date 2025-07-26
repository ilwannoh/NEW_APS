from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from app.views.components.result_components.table_widget.material_widget import MaterialWidget

class MaterialTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_page = parent
        self.material_widget = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 자재 부족 분석 위젯 생성
        self.material_widget = MaterialWidget(self)
        layout.addWidget(self.material_widget)
        
        # 부모의 테이블 참조 설정 (호환성)
        self.shortage_items_table = self.material_widget.get_table()
        if hasattr(self.parent_page, 'shortage_items_table'):
            self.parent_page.shortage_items_table = self.shortage_items_table
        
        # 부모의 material_analyzer 참조 설정 (호환성)
        if hasattr(self.parent_page, 'material_analyzer'):
            self.material_widget.set_material_analyzer(self.parent_page.material_analyzer)
        
        # 자재 부족 정보 업데이트 시그널 연결
        self.material_widget.material_shortage_updated.connect(self.on_material_shortage_updated)
    
    """자재 부족 정보가 업데이트되었을 때 호출되는 핸들러"""
    def on_material_shortage_updated(self, shortage_results):
        # 부모 페이지에 자재 부족 정보 전달 (호환성)
        if hasattr(self.parent_page, 'on_material_shortage_updated'):
            self.parent_page.on_material_shortage_updated(shortage_results)
    
    """
    테이블 반환
    """
    def get_table(self):
        return self.shortage_items_table
    
    """
    위젯 반환
    """
    def get_widget(self):
        return self.material_widget