"""
드래그&드롭 문제 패치 스크립트
schedule_grid_view.py에 디버그 로그를 추가하고 문제를 수정
"""
import os
import shutil
from datetime import datetime


def patch_schedule_grid_view():
    """schedule_grid_view.py 패치"""
    file_path = r"C:\MYCLAUDE_PROJECT\NEW_APS\app\views\schedule_grid_view.py"
    
    # 백업 생성
    backup_path = file_path + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"백업 생성: {backup_path}")
    
    # 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 패치 1: DraggableBatchLabel의 mousePressEvent에 디버그 로그 추가
    old_code1 = '''    def mousePressEvent(self, event):
        """마우스 클릭 이벤트"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
            self.batch_selected.emit(self)'''
    
    new_code1 = '''    def mousePressEvent(self, event):
        """마우스 클릭 이벤트"""
        print(f"[DEBUG] DraggableBatchLabel.mousePressEvent - Button: {event.button()}")
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
            print(f"[DEBUG] Drag start position saved: {self.drag_start_position}")
            self.batch_selected.emit(self)
            # 부모 위젯에도 이벤트 전달
            super().mousePressEvent(event)'''
    
    content = content.replace(old_code1, new_code1)
    
    # 패치 2: mouseMoveEvent에 디버그 로그 추가
    old_code2 = '''    def mouseMoveEvent(self, event):
        """마우스 이동 이벤트"""
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if (event.pos() - self.drag_start_position).manhattanLength() < 10:
            return'''
    
    new_code2 = '''    def mouseMoveEvent(self, event):
        """마우스 이동 이벤트"""
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if not hasattr(self, 'drag_start_position'):
            print("[DEBUG] No drag_start_position attribute")
            return
        
        distance = (event.pos() - self.drag_start_position).manhattanLength()
        print(f"[DEBUG] Mouse move distance: {distance}")
        
        if distance < 10:
            return'''
    
    content = content.replace(old_code2, new_code2)
    
    # 패치 3: drag.exec_ 부분에 디버그 로그 추가
    old_code3 = '''        drag.exec_(Qt.MoveAction)'''
    
    new_code3 = '''        print("[DEBUG] Starting drag.exec_...")
        result = drag.exec_(Qt.MoveAction)
        print(f"[DEBUG] Drag result: {result}")'''
    
    content = content.replace(old_code3, new_code3)
    
    # 패치 4: handle_batch_drop에 디버그 로그 추가
    old_code4 = '''    def handle_batch_drop(self, source_container, batch_data: dict):
        """배치 드롭 처리"""
        target_container = self.sender()'''
    
    new_code4 = '''    def handle_batch_drop(self, source_container, batch_data: dict):
        """배치 드롭 처리"""
        print(f"[DEBUG] handle_batch_drop called!")
        print(f"[DEBUG] Source: {source_container}, Batch data: {batch_data}")
        target_container = self.sender()
        print(f"[DEBUG] Target container: {target_container}")'''
    
    content = content.replace(old_code4, new_code4)
    
    # 패치 5: EquipmentTimeSlot의 init_ui에서 setAcceptDrops 확인
    old_code5 = '''    def init_ui(self):
        """UI 초기화"""
        self.setAcceptDrops(True)'''
    
    new_code5 = '''    def init_ui(self):
        """UI 초기화"""
        self.setAcceptDrops(True)
        print(f"[DEBUG] EquipmentTimeSlot.init_ui - acceptDrops set to True for {self.equipment_id}, slot {self.slot}")'''
    
    content = content.replace(old_code5, new_code5)
    
    # 파일 쓰기
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("패치 완료!")
    print("\n추가된 디버그 로그:")
    print("1. DraggableBatchLabel.mousePressEvent - 마우스 클릭 시")
    print("2. DraggableBatchLabel.mouseMoveEvent - 마우스 이동 시")
    print("3. drag.exec_ - 드래그 실행 시")
    print("4. handle_batch_drop - 드롭 처리 시")
    print("5. EquipmentTimeSlot.init_ui - 드롭 가능 설정 시")


def analyze_problem():
    """문제 분석"""
    print("\n=== 드래그&드롭 문제 분석 ===")
    print("\n가능한 원인들:")
    print("1. 시그널-슬롯 연결 문제")
    print("   - batch_dropped 시그널이 handle_batch_drop 슬롯에 제대로 연결되지 않음")
    print("   - 시그널이 발생하지만 슬롯이 호출되지 않음")
    print("\n2. 이벤트 전파 문제")
    print("   - mousePressEvent가 부모 위젯으로 전파되지 않음")
    print("   - drag_start_position이 제대로 저장되지 않음")
    print("\n3. 드래그 임계값 문제")
    print("   - manhattanLength() < 10 조건이 너무 엄격함")
    print("   - 사용자가 10픽셀 이상 드래그하기 어려움")
    print("\n4. acceptDrops 설정 문제")
    print("   - 일부 위젯에서 setAcceptDrops(True)가 누락됨")
    print("   - 드롭 이벤트가 제대로 전달되지 않음")
    print("\n5. MIME 데이터 문제")
    print("   - JSON 직렬화/역직렬화 과정에서 오류 발생")
    print("   - 데이터가 올바르게 전달되지 않음")


def suggest_fixes():
    """수정 제안"""
    print("\n=== 수정 제안 ===")
    print("\n1. 시그널 연결 확인:")
    print("   - setup_grid에서 container.batch_dropped.connect(self.handle_batch_drop) 확인")
    print("   - 연결이 제대로 되었는지 로그 추가")
    print("\n2. 드래그 임계값 조정:")
    print("   - manhattanLength() < 10을 < 5로 변경")
    print("   - 또는 QApplication.startDragDistance() 사용")
    print("\n3. 이벤트 전파 개선:")
    print("   - mousePressEvent에서 super().mousePressEvent(event) 호출")
    print("   - 부모 위젯으로 이벤트 전파 보장")
    print("\n4. 드롭 가능 영역 시각화:")
    print("   - dragEnterEvent에서 더 명확한 시각적 피드백")
    print("   - 드롭 가능한 영역을 하이라이트")
    print("\n5. 에러 처리 강화:")
    print("   - try-except 블록 추가")
    print("   - 예외 발생 시 상세 로그 출력")


if __name__ == "__main__":
    print("=== 드래그&드롭 패치 스크립트 ===")
    
    # 문제 분석
    analyze_problem()
    
    # 수정 제안
    suggest_fixes()
    
    # 패치 적용 여부 확인
    response = input("\n패치를 적용하시겠습니까? (y/n): ")
    if response.lower() == 'y':
        patch_schedule_grid_view()
        print("\n패치가 적용되었습니다. 프로그램을 다시 실행하여 테스트해보세요.")
    else:
        print("패치를 적용하지 않았습니다.")