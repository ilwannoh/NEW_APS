"""
드래그&드롭 문제 분석 스크립트
실제 APS 프로젝트의 드래그&드롭 구조를 테스트
"""
import sys
import os
import json
from datetime import datetime

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt
from app.views.schedule_grid_view import ScheduleGridView, DraggableBatchLabel, EquipmentTimeSlot
from app.models.production_plan import ProductionPlan, Batch
from app.models.master_data import MasterDataManager
from app.controllers.main_controller import MainController


class TestWindow(QMainWindow):
    """테스트 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("드래그&드롭 테스트")
        self.setGeometry(100, 100, 1200, 800)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 레이아웃
        layout = QVBoxLayout(central_widget)
        
        # 상태 라벨
        self.status_label = QLabel("드래그&드롭 테스트를 시작합니다...")
        layout.addWidget(self.status_label)
        
        # 컨트롤러와 마스터 데이터 초기화
        self.controller = MainController()
        self.master_data = self.controller.master_data
        
        # 테스트 데이터 추가
        self.setup_test_data()
        
        # 스케줄 그리드 뷰
        self.schedule_grid = ScheduleGridView(master_data=self.master_data)
        self.schedule_grid.batch_moved.connect(self.on_batch_moved)
        self.schedule_grid.batch_selected.connect(self.on_batch_selected)
        
        layout.addWidget(self.schedule_grid)
        
        # 테스트 스케줄 로드
        self.load_test_schedule()
    
    def setup_test_data(self):
        """테스트 데이터 설정"""
        # 샘플 장비 추가
        if not self.master_data.equipment:
            self.master_data.equipment = {
                'EQ001': {
                    'id': 'EQ001',
                    'name': '타정기 1호',
                    'process_id': 'P003',
                    'available_products': ['PROD001', 'PROD002']
                },
                'EQ002': {
                    'id': 'EQ002',
                    'name': '타정기 2호',
                    'process_id': 'P003',
                    'available_products': ['PROD003', 'PROD004']
                }
            }
        
        # 샘플 제품 추가
        if not self.master_data.products:
            self.master_data.products = {
                'PROD001': {
                    'id': 'PROD001',
                    'name': '기넥신에프정 40mg 100T',
                    'process_order': ['P001', 'P002', 'P003', 'P004', 'P005']
                },
                'PROD002': {
                    'id': 'PROD002',
                    'name': '리넥신정 80/100mg 300T',
                    'process_order': ['P001', 'P002', 'P003', 'P004', 'P005']
                }
            }
        
        self.status_label.setText("테스트 데이터 설정 완료")
    
    def load_test_schedule(self):
        """테스트 스케줄 로드"""
        # 테스트용 생산 계획 생성
        plan = ProductionPlan()
        
        # 테스트 배치 추가
        batch1 = Batch(
            batch_id="BATCH001",
            product_id="PROD001",
            product_name="기넥신에프정 40mg 100T",
            equipment_id="EQ001",
            start_time=datetime(2025, 2, 1, 8, 0),
            duration_hours=4
        )
        batch1.process_id = "P003"
        batch1.lot_number = "1"
        
        batch2 = Batch(
            batch_id="BATCH002",
            product_id="PROD002",
            product_name="리넥신정 80/100mg 300T",
            equipment_id="EQ002",
            start_time=datetime(2025, 2, 1, 10, 0),
            duration_hours=6
        )
        batch2.process_id = "P003"
        batch2.lot_number = "2"
        
        plan.add_batch(batch1)
        plan.add_batch(batch2)
        
        # 스케줄 로드
        self.schedule_grid.load_schedule(plan)
        self.status_label.setText("테스트 스케줄 로드 완료 - 배치를 드래그해보세요")
    
    def on_batch_moved(self, batch_id, new_equipment_id, new_date):
        """배치 이동 이벤트"""
        print(f"[TEST] Batch moved: {batch_id} -> {new_equipment_id} @ {new_date}")
        self.status_label.setText(f"배치 이동: {batch_id} -> {new_equipment_id} @ {new_date}")
    
    def on_batch_selected(self, batch):
        """배치 선택 이벤트"""
        print(f"[TEST] Batch selected: {batch.id}")
        self.status_label.setText(f"배치 선택: {batch.id} - {batch.product_name}")


def test_drag_drop_components():
    """개별 컴포넌트 테스트"""
    print("\n=== 드래그&드롭 컴포넌트 테스트 ===")
    
    # 1. DraggableBatchLabel 테스트
    print("\n1. DraggableBatchLabel 테스트:")
    batch = Batch(
        batch_id="TEST001",
        product_id="PROD001",
        product_name="테스트 제품",
        equipment_id="EQ001",
        start_time=datetime.now(),
        duration_hours=4
    )
    
    label = DraggableBatchLabel(batch)
    print(f"   - 배치 라벨 생성: {label}")
    print(f"   - acceptDrops: {label.acceptDrops()}")
    print(f"   - dragEnabled: {label.hasMouseTracking()}")
    
    # 2. EquipmentTimeSlot 테스트
    print("\n2. EquipmentTimeSlot 테스트:")
    slot = EquipmentTimeSlot("EQ001", datetime.now().date(), 0)
    print(f"   - 슬롯 생성: {slot}")
    print(f"   - acceptDrops: {slot.acceptDrops()}")
    print(f"   - equipment_id: {slot.equipment_id}")
    print(f"   - slot: {slot.slot}")
    
    # 3. 시그널 연결 테스트
    print("\n3. 시그널 연결 테스트:")
    grid = ScheduleGridView()
    print(f"   - batch_moved 시그널: {grid.batch_moved}")
    print(f"   - batch_selected 시그널: {grid.batch_selected}")
    
    # 4. 이벤트 핸들러 확인
    print("\n4. 이벤트 핸들러 확인:")
    print(f"   - DraggableBatchLabel.mousePressEvent: {hasattr(label, 'mousePressEvent')}")
    print(f"   - DraggableBatchLabel.mouseMoveEvent: {hasattr(label, 'mouseMoveEvent')}")
    print(f"   - EquipmentTimeSlot.dragEnterEvent: {hasattr(slot, 'dragEnterEvent')}")
    print(f"   - EquipmentTimeSlot.dropEvent: {hasattr(slot, 'dropEvent')}")


def main():
    """메인 함수"""
    # 컴포넌트 테스트 먼저 실행
    test_drag_drop_components()
    
    # GUI 테스트
    print("\n=== GUI 드래그&드롭 테스트 시작 ===")
    app = QApplication(sys.argv)
    
    # 드래그 설정 확인
    print(f"\nQApplication 설정:")
    print(f"   - startDragDistance: {app.startDragDistance()}")
    print(f"   - startDragTime: {app.startDragTime()}")
    
    window = TestWindow()
    window.show()
    
    print("\n테스트 방법:")
    print("1. 배치 블록을 클릭하고 드래그하여 다른 슬롯으로 이동")
    print("2. 콘솔에서 디버그 메시지 확인")
    print("3. 문제가 발생하는 단계 확인")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()