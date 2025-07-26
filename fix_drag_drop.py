"""
드래그&드롭 문제 수정 스크립트
핵심 문제를 수정하는 패치
"""
import os
import shutil
from datetime import datetime


def fix_schedule_grid_view():
    """schedule_grid_view.py 수정"""
    file_path = r"C:\MYCLAUDE_PROJECT\NEW_APS\app\views\schedule_grid_view.py"
    
    # 백업 생성
    backup_path = file_path + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"백업 생성: {backup_path}")
    
    # 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 수정 1: EquipmentTimeSlot의 dropEvent 수정
    old_drop_event = '''    def dropEvent(self, event):
        """드롭 이벤트"""
        if event.mimeData().hasText():
            batch_data = json.loads(event.mimeData().text())
            
            if self.can_accept_batch(batch_data):
                # 배치 이동 시그널 발생
                self.batch_dropped.emit(None, batch_data)
                event.acceptProposedAction()
        
        # 스타일 복원
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
            }
        """)'''
    
    new_drop_event = '''    def dropEvent(self, event):
        """드롭 이벤트"""
        if event.mimeData().hasText():
            batch_data = json.loads(event.mimeData().text())
            
            if self.can_accept_batch(batch_data):
                # 드래그 소스 찾기
                source_widget = event.source()
                source_container = None
                
                if source_widget and hasattr(source_widget, 'parent'):
                    # DraggableBatchLabel의 부모 찾기
                    parent = source_widget.parent()
                    # 그리드 레이아웃에 직접 배치된 경우를 처리
                    if parent and hasattr(parent, 'batch'):
                        source_container = parent
                
                # 배치 이동 시그널 발생
                self.batch_dropped.emit(source_container, batch_data)
                event.acceptProposedAction()
        
        # 스타일 복원
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
            }
        """)'''
    
    content = content.replace(old_drop_event, new_drop_event)
    
    # 수정 2: 드래그 거리 임계값 조정
    old_distance = 'if (event.pos() - self.drag_start_position).manhattanLength() < 10:'
    new_distance = 'if (event.pos() - self.drag_start_position).manhattanLength() < 5:'
    content = content.replace(old_distance, new_distance)
    
    # 수정 3: handle_batch_drop 메서드 개선
    old_handle = '''    def handle_batch_drop(self, source_container, batch_data: dict):
        """배치 드롭 처리"""
        target_container = self.sender()
        
        # EquipmentTimeSlot인지 확인
        if not isinstance(target_container, EquipmentTimeSlot):
            return
        
        # 배치 ID로 라벨 찾기
        batch_id = batch_data['batch_id']
        if batch_id not in self.batch_labels:
            return
        
        batch_label = self.batch_labels[batch_id]
        
        # 대상 슬롯이 비어있는지 확인
        if target_container.batch is not None:
            return'''
    
    new_handle = '''    def handle_batch_drop(self, source_container, batch_data: dict):
        """배치 드롭 처리"""
        print(f"[DEBUG] handle_batch_drop called - batch_id: {batch_data.get('batch_id')}")
        
        target_container = self.sender()
        
        # EquipmentTimeSlot인지 확인
        if not isinstance(target_container, EquipmentTimeSlot):
            print("[DEBUG] Target is not EquipmentTimeSlot")
            return
        
        # 배치 ID로 라벨 찾기
        batch_id = batch_data['batch_id']
        if batch_id not in self.batch_labels:
            print(f"[DEBUG] Batch {batch_id} not found in batch_labels")
            return
        
        batch_label = self.batch_labels[batch_id]
        
        # 대상 슬롯이 비어있는지 확인
        if target_container.batch is not None:
            print("[DEBUG] Target slot is not empty")
            return'''
    
    content = content.replace(old_handle, new_handle)
    
    # 수정 4: DraggableBatchLabel의 mousePressEvent 개선
    old_mouse_press = '''    def mousePressEvent(self, event):
        """마우스 클릭 이벤트"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
            self.batch_selected.emit(self)'''
    
    new_mouse_press = '''    def mousePressEvent(self, event):
        """마우스 클릭 이벤트"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
            self.batch_selected.emit(self)
        # 부모 클래스의 이벤트 핸들러도 호출
        super().mousePressEvent(event)'''
    
    content = content.replace(old_mouse_press, new_mouse_press)
    
    # 수정 5: 드래그 시작 조건 개선
    old_drag_start = '''        # 드래그 시작
        drag = QDrag(self)
        mime_data = QMimeData()'''
    
    new_drag_start = '''        # 드래그 시작
        print(f"[DEBUG] Starting drag for batch {self.batch.id}")
        drag = QDrag(self)
        mime_data = QMimeData()'''
    
    content = content.replace(old_drag_start, new_drag_start)
    
    # 파일 쓰기
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("수정 완료!")
    print("\n적용된 수정사항:")
    print("1. EquipmentTimeSlot.dropEvent - 소스 위젯 찾기 로직 추가")
    print("2. 드래그 거리 임계값을 10에서 5로 감소")
    print("3. handle_batch_drop에 디버그 로그 추가")
    print("4. mousePressEvent에서 부모 이벤트 핸들러 호출")
    print("5. 드래그 시작 시 디버그 로그 추가")


def create_minimal_test():
    """최소한의 테스트 케이스 생성"""
    test_code = '''"""
최소한의 드래그&드롭 테스트
문제를 격리하여 테스트
"""
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import json


class TestDraggable(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setFrameStyle(QFrame.Box)
        self.setMinimumSize(100, 50)
        self.setStyleSheet("background-color: lightblue;")
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.pos()
            
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            if (event.pos() - self.drag_pos).manhattanLength() < 5:
                return
                
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(self.text())
            drag.setMimeData(mime)
            
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            
            drag.exec_(Qt.MoveAction)


class TestDropZone(QFrame):
    dropped = pyqtSignal(str)
    
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Box)
        self.setMinimumSize(150, 100)
        self.setStyleSheet("background-color: lightgray;")
        
        layout = QVBoxLayout(self)
        self.label = QLabel(name)
        layout.addWidget(self.label)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet("background-color: yellow;")
            
    def dragLeaveEvent(self, event):
        self.setStyleSheet("background-color: lightgray;")
        
    def dropEvent(self, event):
        if event.mimeData().hasText():
            text = event.mimeData().text()
            self.label.setText(f"{self.name}\\n{text}")
            self.dropped.emit(text)
            event.acceptProposedAction()
        self.setStyleSheet("background-color: lightgreen;")


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minimal Drag&Drop Test")
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        
        # 드래그 소스
        left = QVBoxLayout()
        left.addWidget(QLabel("Drag from here:"))
        for i in range(3):
            left.addWidget(TestDraggable(f"Item {i+1}"))
        left.addStretch()
        
        # 드롭 타겟
        right = QVBoxLayout()
        right.addWidget(QLabel("Drop here:"))
        for i in range(2):
            zone = TestDropZone(f"Zone {i+1}")
            zone.dropped.connect(lambda text, z=zone: print(f"Dropped '{text}' on {z.name}"))
            right.addWidget(zone)
        right.addStretch()
        
        layout.addLayout(left)
        layout.addLayout(right)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())
'''
    
    with open("minimal_drag_drop_test.py", "w", encoding="utf-8") as f:
        f.write(test_code)
    
    print("\n최소 테스트 케이스 생성: minimal_drag_drop_test.py")
    print("이 테스트가 작동하면 문제는 APS 프로젝트의 복잡한 구조에 있습니다.")


if __name__ == "__main__":
    print("=== 드래그&드롭 문제 수정 스크립트 ===")
    
    # 문제 설명
    print("\n발견된 문제:")
    print("1. EquipmentTimeSlot의 dropEvent에서 소스 위젯을 제대로 찾지 못함")
    print("2. 드래그 거리 임계값이 너무 높음 (10픽셀)")
    print("3. 이벤트 전파가 제대로 되지 않음")
    print("4. 디버그 정보 부족으로 문제 추적이 어려움")
    
    # 수정 적용
    response = input("\n수정을 적용하시겠습니까? (y/n): ")
    if response.lower() == 'y':
        fix_schedule_grid_view()
        create_minimal_test()
        print("\n수정이 완료되었습니다!")
        print("1. 프로그램을 다시 실행하여 테스트하세요.")
        print("2. minimal_drag_drop_test.py로 기본 기능을 확인하세요.")
    else:
        print("수정을 취소했습니다.")